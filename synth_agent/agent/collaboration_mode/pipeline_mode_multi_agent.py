from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from synth_agent.agent.multi_agent.agent_team import AgentTeam
from synth_agent.agent.agent import Agent
from synth_agent.agent.react_agent import ReActAgent
from synth_agent.llm.synth_LLM import SynthLLM
from synth_agent.message.message import Message


class PipelineTask:
    def __init__(
        self,
        task_id: str,
        description: str,
        role: str,
        dependencies: List[str] = None,
        status: str = "pending"
    ):
        self.task_id = task_id
        self.description = description
        self.role = role
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
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

    def __str__(self) -> str:
        deps_str = f" (依赖: {', '.join(self.dependencies)})" if self.dependencies else ""
        return f"[{self.status}] {self.task_id}: {self.description} ({self.role}){deps_str}"


class PipelineModeMultiAgent:
    def __init__(self, team_name: str, llm: SynthLLM):  
        self.team = AgentTeam(team_name, collaboration_mode="pipeline")
        self.llm = llm
        self.pipeline_tasks: List[PipelineTask] = []
        self.execution_history: List[Dict[str, Any]] = []

    def add_member(self, agent: ReActAgent, role: str, is_coordinator: bool = False) -> None:
        self.team.add_agent(role, agent, is_coordinator)

    def get_member_info(self) -> List[Dict[str, Any]]:
        members = []
        for role, agent in self.team.members.items():
            members.append({
                "role": role,
                "name": agent.name,
                "type": type(agent).__name__
            })
        return members

    def task_decomposition(self, task: str) -> List[PipelineTask]:
        """使用 LLM 将主任务分解为多个流水线任务"""
        print(f"\n🔧 开始任务分解: {task}")
        print("=" * 60)

        available_roles = self.team.get_all_roles()
        print(f"👥 可用角色: {', '.join(available_roles)}")

        prompt = self._build_decomposition_prompt(task, available_roles)

        messages = [
            {"role": "system", "content": "你是一个任务分解专家，擅长将复杂任务分解为可执行的流水线子任务。"},
            {"role": "user", "content": prompt}
        ]

        print("🧠 调用 LLM 进行任务分解...")
        response = self.llm.think(messages, temperature=0.3)

        if not response:
            print("❌ 任务分解失败: LLM 调用失败")
            return []

        content = response.get("full_content", "")
        print(f"📝 LLM 返回内容:\n{content}")

        tasks = self._parse_tasks_from_response(content, available_roles)

        print(f"✅ 任务分解完成，共 {len(tasks)} 个子任务:")
        for task in tasks:
            print(f"  - {task}")

        self.pipeline_tasks = tasks
        return tasks

    def _build_decomposition_prompt(self, task: str, available_roles: List[str]) -> str:
        return f"""请将以下主任务分解为多个流水线子任务：

        主任务: {task}

        可用角色: {', '.join(available_roles)}

        要求:
        1. 将主任务分解为 3-6 个子任务
        2. 每个子任务必须指定一个对应的角色
        3. 明确每个子任务的前后依赖关系（哪些任务需要先完成）
        4. 子任务之间应该有逻辑顺序，形成流水线
        5. 第一个任务不应该有依赖
        6. 每个任务应该具体、可执行

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

        注意事项:
        - task_id 必须唯一，格式为 task_1, task_2, ...
        - dependencies 是任务 ID 列表，表示需要先完成的任务
        - role 必须是可用角色之一
        - 只返回 JSON，不要有其他解释文字
        """

    def _parse_tasks_from_response(self, content: str, available_roles: List[str]) -> List[PipelineTask]:
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

                task = PipelineTask(
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

    def execute_pipeline(self, task: str) -> str:
        """执行流水线任务"""
        print(f"\n🚀 开始执行流水线模式")
        print("=" * 60)

        tasks = self.task_decomposition(task)

        if not tasks:
            return "❌ 任务分解失败，无法执行流水线"

        print(f"\n📋 流水线任务执行计划:")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task}")

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
                    f"pipeline_{task.task_id}_result",
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

        final_summary = self._summarize_pipeline_results(tasks, task)

        self.execution_history.append({
            "main_task": task,
            "timestamp": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in tasks],
            "results": execution_results,
            "summary": final_summary
        })

        print("\n✅ 流水线执行完成")
        print("=" * 60)

        return final_summary

    def _check_dependencies(self, task: PipelineTask, execution_results: Dict[str, str]) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in execution_results:
                print(f"⚠️ 依赖任务 {dep_id} 未完成")
                return False
        return True

    def _build_task_context(self, task: PipelineTask, execution_results: Dict[str, str]) -> str:
        """构建任务执行上下文"""
        context_parts = [
            f"你是 {task.role}，正在执行流水线任务。",
            f"任务 ID: {task.task_id}",
            f"任务描述: {task.description}",
            ""
        ]

        if task.dependencies:
            context_parts.append("前置任务结果:")
            for dep_id in task.dependencies:
                if dep_id in execution_results:
                    context_parts.append(f"\n【{dep_id}】")
                    context_parts.append(execution_results[dep_id][:500])

        context_parts.append("\n请基于以上信息完成你的任务。")

        return "\n".join(context_parts)

    def _summarize_pipeline_results(self, tasks: List[PipelineTask], main_task: str) -> str:
        """汇总流水线执行结果"""
        summary_parts = [
            f"📋 流水线模式任务总结",
            f"主任务: {main_task}",
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
        summary_parts.append(f"  成功率: {completed_count/len(tasks)*100:.1f}%")

        return "\n".join(summary_parts)

    def get_pipeline_tasks(self) -> List[Dict[str, Any]]:
        return [task.to_dict() for task in self.pipeline_tasks]

    def get_execution_history(self) -> List[Dict[str, Any]]:
        return self.execution_history

    def get_statistics(self) -> Dict[str, Any]:
        total_tasks = len(self.pipeline_tasks)
        completed = sum(1 for t in self.pipeline_tasks if t.status == "completed")
        failed = sum(1 for t in self.pipeline_tasks if t.status == "failed")

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "pending": sum(1 for t in self.pipeline_tasks if t.status == "pending"),
            "running": sum(1 for t in self.pipeline_tasks if t.status == "running"),
            "success_rate": completed/total_tasks*100 if total_tasks > 0 else 0,
            "execution_count": len(self.execution_history)
        }

    def clear_history(self) -> None:
        self.pipeline_tasks.clear()
        self.execution_history.clear()
        print("🧹 流水线历史已清空")

    def __str__(self) -> str:
        return f"PipelineModeMultiAgent(team={self.team.team_name}, members={len(self.team.members)})"
