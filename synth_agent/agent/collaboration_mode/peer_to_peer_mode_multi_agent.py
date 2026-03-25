from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Thread
import time
from synth_agent.agent.multi_agent.agent_team import AgentTeam
from synth_agent.agent.agent import Agent
from synth_agent.agent.react_agent import ReActAgent
from synth_agent.message.message import Message


class PeerToPeerModeMultiAgent:
    def __init__(self, team_name: str):
        self.team = AgentTeam(team_name, collaboration_mode="peer_to_peer")
        self.collaboration_history: List[Dict[str, Any]] = []

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

    def collaborate(self, task: str, max_rounds: int = 3, communication_enabled: bool = True) -> str:
        print(f"\n🤝 开始 P2P 协作模式处理任务: {task}")
        print("=" * 60)

        if len(self.team.members) == 0:
            return "❌ 团队中没有成员"

        roles = self.team.get_all_roles()
        print(f"👥 参与协作的角色: {', '.join(roles)}")

        self.team.shared_memory.set("task", task, agent_id="system")
        self.team.shared_memory.set("collaboration_mode", "peer_to_peer", agent_id="system")

        round_results = {}

        for round_num in range(1, max_rounds + 1):
            print(f"\n🔄 第 {round_num} 轮协作开始")
            print("-" * 40)

            round_results[round_num] = {}

            threads = []
            results = {}

            def process_agent(role: str):
                agent = self.team.get_agent(role)
                if not agent:
                    return

                print(f"👤 {role} 开始独立思考...")

                try:
                    context = self._build_context(role, round_num, task)

                    if communication_enabled and round_num > 1:
                        messages = self.team.communication_bus.receive_messages(role)
                        if messages:
                            print(f"📨 {role} 收到 {len(messages)} 条消息")
                            for msg in messages:
                                context += f"\n[来自 {msg.sender} 的消息]: {msg.content}"

                    result = agent.run(context)

                    results[role] = result

                    self.team.shared_memory.set(
                        f"{role}_round_{round_num}_result",
                        result,
                        agent_id=role
                    )

                    print(f"✅ {role} 完成本轮思考")

                    if communication_enabled and round_num < max_rounds:
                        self._share_insights(role, result, roles)

                except Exception as e:
                    print(f"❌ {role} 处理出错: {str(e)}")
                    results[role] = f"处理出错: {str(e)}"

            for role in roles:
                thread = Thread(target=process_agent, args=(role,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            round_results[round_num] = results

            print(f"\n📊 第 {round_num} 轮协作完成")

            if communication_enabled:
                self._facilitate_communication(roles, round_num)

        final_summary = self._summarize_results(round_results, task)

        self.collaboration_history.append({
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "rounds": max_rounds,
            "participants": roles,
            "results": round_results,
            "summary": final_summary
        })

        print("\n✅ P2P 协作完成")
        print("=" * 60)

        return final_summary

    def _build_context(self, role: str, round_num: int, task: str) -> str:
        context_parts = [
            f"你是一个 {role}，正在参与 P2P（点对点）协作模式。",
            f"当前是第 {round_num} 轮协作。",
            f"任务: {task}",
            "",
            "P2P 协作模式特点:",
            "- 所有智能体地位平等，没有中心指挥",
            "- 各自独立思考和处理任务",
            "- 可以通过消息与其他智能体沟通",
            "- 最后汇总所有结果",
            "",
            "请从你的专业角度独立思考这个任务，提供你的见解和建议。"
        ]

        if round_num > 1:
            context_parts.append("\n之前的协作结果:")
            for r in range(1, round_num):
                prev_result = self.team.shared_memory.get(f"{role}_round_{r}_result")
                if prev_result:
                    context_parts.append(f"\n第 {r} 轮你的结果: {prev_result[:200]}...")

        return "\n".join(context_parts)

    def _share_insights(self, sender_role: str, result: str, all_roles: List[str]) -> None:
        insights = self._extract_insights(result)

        for role in all_roles:
            if role != sender_role:
                message = f"我是 {sender_role}，这是我的思考结果和见解:\n{insights}"
                self.team.communication_bus.send_message(sender_role, role, message)

    def _extract_insights(self, result: str) -> str:
        if len(result) <= 300:
            return result

        sentences = result.split('。')
        insights = []
        for i, sentence in enumerate(sentences):
            if i < 3:
                insights.append(sentence.strip())

        return '。'.join(insights) + '。'

    def _facilitate_communication(self, roles: List[str], round_num: int) -> None:
        print("\n💬 智能体间沟通...")

        for role in roles:
            messages = self.team.communication_bus.peek_messages(role)
            if messages:
                print(f"📨 {role} 有 {len(messages)} 条待处理消息")

    def _summarize_results(self, round_results: Dict[int, Dict[str, str]], task: str) -> str:
        summary_parts = [
            f"📋 P2P 协作模式任务总结",
            f"任务: {task}",
            f"参与角色: {', '.join(round_results[1].keys())}",
            f"协作轮数: {len(round_results)}",
            "",
            "各角色最终结果:"
        ]

        for role, result in round_results[len(round_results)].items():
            summary_parts.append(f"\n【{role}】")
            summary_parts.append(result[:500] + "..." if len(result) > 500 else result)

        summary_parts.append("\n" + "=" * 60)
        summary_parts.append("📊 协作统计:")
        summary_parts.append(f"- 总消息数: {len(self.team.communication_bus.get_message_history())}")
        summary_parts.append(f"- 共享记忆条目: {len(self.team.shared_memory)}")

        return "\n".join(summary_parts)

    def get_collaboration_history(self) -> List[Dict[str, Any]]:
        return self.collaboration_history

    def get_communication_statistics(self) -> Dict[str, Any]:
        return self.team.communication_bus.get_statistics()

    def get_shared_memory_statistics(self) -> Dict[str, Any]:
        return self.team.shared_memory.get_statistics()

    def clear_history(self) -> None:
        self.collaboration_history.clear()
        self.team.communication_bus.clear_history()
        self.team.shared_memory.clear()
        print("🧹 P2P 协作历史已清空")

    def __str__(self) -> str:
        return f"PeerToPeerModeMultiAgent(team={self.team.team_name}, members={len(self.team.members)})"
