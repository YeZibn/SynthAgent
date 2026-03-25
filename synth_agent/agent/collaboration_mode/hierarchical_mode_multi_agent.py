from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from synth_agent.agent.multi_agent.agent_team import AgentTeam
from synth_agent.agent.agent import Agent
from synth_agent.agent.react_agent import ReActAgent
from synth_agent.llm.synth_LLM import SynthLLM
from synth_agent.message.message import Message
from synth_agent.tool.tool_list.communication_tool import CommunicationTool


class HierarchicalTask:
    def __init__(
        self,
        task_id: str,
        description: str,
        role: str,
        parent_task: Optional[str] = None,
        dependencies: List[str] = None,
        status: str = "pending"
    ):
        self.task_id = task_id
        self.description = description
        self.role = role
        self.parent_task = parent_task
        self.dependencies = dependencies or []
        self.status = status
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "role": self.role,
            "parent_task": self.parent_task,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

    def __str__(self) -> str:
        deps_str = f" (依赖: {', '.join(self.dependencies)})" if self.dependencies else ""
        parent_str = f" (父任务: {self.parent_task})" if self.parent_task else ""
        return f"[{self.status}] {self.task_id}: {self.description} ({self.role}){deps_str}{parent_str}"


class HierarchicalModeMultiAgent:
    def __init__(self, team_name: str, llm: SynthLLM):
        self.team = AgentTeam(team_name, collaboration_mode="hierarchical")
        self.llm = llm
        self.hierarchical_tasks: List[HierarchicalTask] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.communication_tool = CommunicationTool(self.team.communication_bus)

    def add_member(self, agent: ReActAgent, role: str, is_coordinator: bool = False) -> None:
        self.team.add_agent(role, agent, is_coordinator)

    def get_member_info(self) -> List[Dict[str, Any]]:
        members = []
        for role, agent in self.team.members.items():
            members.append({
                "role": role,
                "name": agent.name,
                "type": type(agent).__name__,
                "is_coordinator": role == self.team.coordinator_role
            })
        return members

    def execute_hierarchical(self, task: str) -> str:
        """执行分层模式任务"""
        print(f"\n🏛️  开始执行分层模式")
        print("=" * 60)

        if not self.team.coordinator_role:
            return "❌ 分层模式需要设置协调者"

        coordinator = self.team.get_agent(self.team.coordinator_role)
        if not coordinator:
            return f"❌ 找不到协调者: {self.team.coordinator_role}"

        print(f"👑 协调者: {self.team.coordinator_role}")
        print(f"👥 团队成员: {', '.join(self.team.get_all_roles())}")

        # 步骤1: 协调者分解任务
        tasks = self._coordinator_decompose_task(task)
        if not tasks:
            return "❌ 任务分解失败"

        # 步骤2: 执行子任务
        execution_results = self._execute_subtasks(tasks)

        # 步骤3: 协调者汇总结果
        final_summary = self._coordinator_summarize(task, execution_results)

        self.execution_history.append({
            "main_task": task,
            "timestamp": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in self.hierarchical_tasks],
            "results": execution_results,
            "summary": final_summary
        })

        print("\n✅ 分层模式执行完成")
        print("=" * 60)

        return final_summary

    def _coordinator_decompose_task(self, task: str) -> List[HierarchicalTask]:
        """协调者分解任务"""
        print(f"\n🔧 协调者开始任务分解: {task}")
        print("=" * 60)

        coordinator = self.team.get_agent(self.team.coordinator_role)
        available_roles = [role for role in self.team.get_all_roles() if role != self.team.coordinator_role]

        print(f"👥 可用执行角色: {', '.join(available_roles)}")

        # 构建协调者的任务分解上下文
        context = f"""
        你是 {self.team.coordinator_role}，作为项目的协调者，你的职责是：
        1. 将主任务分解为多个子任务
        2. 为每个子任务分配合适的执行角色
        3. 确定子任务之间的依赖关系

        主任务: {task}

        可用执行角色: {', '.join(available_roles)}

        请按照以下要求进行任务分解：
        1. 将主任务分解为 3-6 个子任务
        2. 每个子任务必须指定一个对应的执行角色
        3. 明确每个子任务的前后依赖关系
        4. 子任务应该具有明确的层次结构
        5. 第一个任务不应该有依赖

        请严格按照以下 JSON 格式返回（不要包含其他文字）:

        {{
        "tasks": [
            {{
            "task_id": "task_1",
            "description": "任务描述",
            "role": "角色名称",
            "dependencies": []
            }},
            {{
            "task_id": "task_2",
            "description": "任务描述",
            "role": "角色名称",
            "dependencies": ["task_1"]
            }}
        ]
        }}
        """

        print("🧠 协调者思考中...")
        result = coordinator.run(context)

        print(f"📝 协调者分解结果:{result}")

        tasks = self._parse_tasks_from_response(result, available_roles)

        print(f"✅ 任务分解完成，共 {len(tasks)} 个子任务:")
        for task in tasks:
            print(f"  - {task}")

        self.hierarchical_tasks = tasks
        return tasks

    def _parse_tasks_from_response(self, content: str, available_roles: List[str]) -> List[HierarchicalTask]:
        """从协调者的响应中解析任务"""
        tasks = []

        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                print("❌ 无法从响应中提取 JSON")
                return []

            json_str = json_match.group(0)
            data = json.loads(json_str)

            task_list = data.get("tasks", [])
            for task_data in task_list:
                task_id = task_data.get("task_id", "")
                description = task_data.get("description", "")
                role = task_data.get("role", "")
                dependencies = task_data.get("dependencies", [])

                if not task_id or not description or not role:
                    print(f"⚠️ 跳过无效任务: {task_data}")
                    continue

                if role not in available_roles:
                    print(f"⚠️ 角色 {role} 不在可用角色列表中，跳过任务 {task_id}")
                    continue

                task = HierarchicalTask(
                    task_id=task_id,
                    description=description,
                    role=role,
                    dependencies=dependencies
                )
                tasks.append(task)

        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
        except Exception as e:
            print(f"❌ 解析任务时出错: {e}")

        return tasks

    def _execute_subtasks(self, tasks: List[HierarchicalTask]) -> Dict[str, str]:
        """执行子任务"""
        print(f"\n🚀 开始执行子任务")
        print("=" * 60)

        execution_results = {}

        for task in tasks:
            print(f"\n🔄 执行任务: {task.task_id}")
            print("-" * 40)

            if not self._check_dependencies(task, execution_results):
                print(f"❌ 任务 {task.task_id} 的依赖未满足，跳过")
                task.status = "failed"
                task.error = "依赖未满足"
                continue

            task.status = "running"
            task.start_time = datetime.now()

            try:
                agent = self.team.get_agent(task.role)
                if not agent:
                    raise ValueError(f"找不到角色 {task.role} 的智能体")

                context = self._build_task_context(task, execution_results)
                result = agent.run(context)

                task.result = result
                task.status = "completed"
                task.end_time = datetime.now()

                execution_results[task.task_id] = result

                self.team.shared_memory.set(
                    f"hierarchical_{task.task_id}_result",
                    result,
                    agent_id=task.role
                )

                print(f"✅ 任务 {task.task_id} 完成")
                print(f"📄 结果预览: {result[:200]}...")

            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                task.end_time = datetime.now()
                print(f"❌ 任务 {task.task_id} 失败: {e}")

        return execution_results

    def _check_dependencies(self, task: HierarchicalTask, execution_results: Dict[str, str]) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in execution_results:
                print(f"⚠️ 依赖任务 {dep_id} 未完成")
                return False
        return True

    def _build_task_context(self, task: HierarchicalTask, execution_results: Dict[str, str]) -> str:
        """构建任务执行上下文"""
        context_parts = [
            f"你是 {task.role}，正在分层模式下执行子任务。",
            f"任务 ID: {task.task_id}",
            f"任务描述: {task.description}",
            "",
            "分层模式特点:",
            "- 有一个协调者负责整体协调",
            "- 你只需要专注完成自己的子任务",
            "- 你可以通过通信工具与其他智能体交流",
            "- 最终由协调者汇总所有结果",
            "",
            "可用工具:",
            "- communication: 用于与其他智能体通信",
            "- 其他你自己的专业工具",
            "",
        ]

        if task.dependencies:
            context_parts.append("前置任务结果:")
            for dep_id in task.dependencies:
                if dep_id in execution_results:
                    context_parts.append(f"\n【{dep_id}】")
                    context_parts.append(execution_results[dep_id][:500])

        context_parts.append("\n请基于以上信息完成你的任务。如果需要与其他智能体交流，请使用communication工具。")

        return "\n".join(context_parts)

    def _coordinator_summarize(self, main_task: str, execution_results: Dict[str, str]) -> str:
        """协调者汇总结果"""
        print(f"\n📊 协调者开始汇总结果")
        print("=" * 60)

        coordinator = self.team.get_agent(self.team.coordinator_role)

        # 构建汇总上下文
        context_parts = [
            f"你是 {self.team.coordinator_role}，作为项目的协调者，你的职责是汇总所有子任务的结果。",
            f"主任务: {main_task}",
            "",
            "子任务执行结果:",
        ]

        for task in self.hierarchical_tasks:
            context_parts.append(f"\n【{task.task_id}】")
            context_parts.append(f"  角色: {task.role}")
            context_parts.append(f"  描述: {task.description}")
            context_parts.append(f"  状态: {task.status}")
            if task.status == "completed" and task.result:
                context_parts.append(f"  结果: {task.result[:300]}..." if len(task.result) > 300 else f"  结果: {task.result}")

        context_parts.append("\n请基于以上信息，提供一个全面的任务完成总结。")

        context = "\n".join(context_parts)

        print("🧠 协调者汇总中...")
        summary = coordinator.run(context)

        print(f"📝 协调者汇总结果:{summary}")

        return summary

    def _summarize_hierarchical_results(self, tasks: List[HierarchicalTask], main_task: str) -> str:
        """汇总分层执行结果"""
        summary_parts = [
            f"📋 分层模式任务总结",
            f"主任务: {main_task}",
            f"协调者: {self.team.coordinator_role}",
            f"子任务数: {len(tasks)}",
            f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "任务执行详情:"
        ]

        completed_count = 0
        failed_count = 0

        for task in tasks:
            summary_parts.append(f"\n【{task.task_id}】")
            summary_parts.append(f"  描述: {task.description}")
            summary_parts.append(f"  角色: {task.role}")
            summary_parts.append(f"  状态: {task.status}")

            if task.status == "completed":
                completed_count += 1
                summary_parts.append(f"  结果: {task.result[:300]}..." if len(task.result) > 300 else f"  结果: {task.result}")
            elif task.status == "failed":
                failed_count += 1
                summary_parts.append(f"  错误: {task.error}")

        summary_parts.append("\n" + "=" * 60)
        summary_parts.append("📊 执行统计:")
        summary_parts.append(f"  总任务数: {len(tasks)}")
        summary_parts.append(f"  成功: {completed_count}")
        summary_parts.append(f"  失败: {failed_count}")
        summary_parts.append(f"  成功率: {completed_count/len(tasks)*100:.1f}%" if tasks else "  成功率: 0%")

        return "\n".join(summary_parts)

    def get_hierarchical_tasks(self) -> List[Dict[str, Any]]:
        return [task.to_dict() for task in self.hierarchical_tasks]

    def get_execution_history(self) -> List[Dict[str, Any]]:
        return self.execution_history

    def get_statistics(self) -> Dict[str, Any]:
        total_tasks = len(self.hierarchical_tasks)
        completed = sum(1 for t in self.hierarchical_tasks if t.status == "completed")
        failed = sum(1 for t in self.hierarchical_tasks if t.status == "failed")

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "pending": sum(1 for t in self.hierarchical_tasks if t.status == "pending"),
            "running": sum(1 for t in self.hierarchical_tasks if t.status == "running"),
            "success_rate": completed/total_tasks*100 if total_tasks > 0 else 0,
            "execution_count": len(self.execution_history),
            "coordinator": self.team.coordinator_role
        }

    def clear_history(self) -> None:
        self.hierarchical_tasks.clear()
        self.execution_history.clear()
        self.team.communication_bus.clear_history()
        self.team.shared_memory.clear()
        print("🧹 分层模式历史已清空")

    def __str__(self) -> str:
        return f"HierarchicalModeMultiAgent(team={self.team.team_name}, coordinator={self.team.coordinator_role}, members={len(self.team.members)})"
