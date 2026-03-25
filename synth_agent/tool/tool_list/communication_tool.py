from typing import Dict, Any, List, Optional
from synth_agent.tool.tool import Tool, ToolParameter
from synth_agent.agent.multi_agent.communication_bus import CommunicationBus


class CommunicationTool(Tool):
    def __init__(self, communication_bus: Optional[CommunicationBus] = None):
        super().__init__(
            name="communication",
            description="多智能体通信工具，支持一对一消息发送和广播消息"
        )
        self.communication_bus = communication_bus or CommunicationBus()

    def run(self, parameters: Dict[str, Any]) -> str:
        action = parameters.get("action", "")

        if action == "send":
            return self._send_message(parameters)
        elif action == "broadcast":
            return self._broadcast_message(parameters)
        elif action == "receive":
            return self._receive_messages(parameters)
        elif action == "get_agents":
            return self._get_agents()
        elif action == "get_history":
            return self._get_history(parameters)
        elif action == "get_statistics":
            return self._get_statistics()
        else:
            return f"❌ 未知的操作: {action}。可用操作: send, broadcast, receive, get_agents, get_history, get_statistics"

    def _send_message(self, parameters: Dict[str, Any]) -> str:
        sender = parameters.get("sender", "")
        receiver = parameters.get("receiver", "")
        content = parameters.get("content", "")

        if not sender:
            return "❌ 缺少发送者 (sender) 参数"
        if not receiver:
            return "❌ 缺少接收者 (receiver) 参数"
        if not content:
            return "❌ 缺少消息内容 (content) 参数"

        success = self.communication_bus.send_message(sender, receiver, content)
        if success:
            return f"✅ 消息已从 {sender} 发送到 {receiver}: {content}"
        else:
            return f"❌ 消息发送失败，接收者 {receiver} 不存在"

    def _broadcast_message(self, parameters: Dict[str, Any]) -> str:
        sender = parameters.get("sender", "")
        content = parameters.get("content", "")
        exclude_sender = parameters.get("exclude_sender", True)

        if not sender:
            return "❌ 缺少发送者 (sender) 参数"
        if not content:
            return "❌ 缺少消息内容 (content) 参数"

        count = self.communication_bus.broadcast_message(sender, content, exclude_sender)
        return f"✅ 广播消息已从 {sender} 发送给 {count} 个接收者: {content}"

    def _receive_messages(self, parameters: Dict[str, Any]) -> str:
        agent_id = parameters.get("agent_id", "")
        limit = parameters.get("limit", 10)

        if not agent_id:
            return "❌ 缺少代理 ID (agent_id) 参数"

        messages = self.communication_bus.receive_messages(agent_id)

        if not messages:
            return f"ℹ️ 代理 {agent_id} 没有新消息"

        limited_messages = messages[:limit]
        result = [f"📨 代理 {agent_id} 收到 {len(limited_messages)} 条消息:"]
        for i, msg in enumerate(limited_messages, 1):
            result.append(f"\n{i}. 发送者: {msg.sender}")
            result.append(f"   类型: {msg.message_type}")
            result.append(f"   时间: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            result.append(f"   内容: {msg.content}")

        return "\n".join(result)

    def _get_agents(self) -> str:
        agents = self.communication_bus.get_all_agents()
        if not agents:
            return "ℹ️ 当前没有注册的代理"
        return f"📋 已注册的代理列表: {', '.join(agents)}"

    def _get_history(self, parameters: Dict[str, Any]) -> str:
        agent_id = parameters.get("agent_id", "")
        limit = parameters.get("limit", 20)

        if agent_id:
            history = self.communication_bus.get_history_for_agent(agent_id, limit)
            if not history:
                return f"ℹ️ 代理 {agent_id} 没有历史消息"
            result = [f"📜 代理 {agent_id} 的消息历史 (最近 {len(history)} 条):"]
        else:
            history = self.communication_bus.get_message_history(limit)
            if not history:
                return "ℹ️ 没有历史消息"
            result = [f"📜 全局消息历史 (最近 {len(history)} 条):"]

        for i, msg in enumerate(history, 1):
            result.append(f"\n{i}. {msg['sender']} -> {msg['receiver']}")
            result.append(f"   类型: {msg['message_type']}")
            result.append(f"   时间: {msg['timestamp']}")
            result.append(f"   内容: {msg['content']}")

        return "\n".join(result)

    def _get_statistics(self) -> str:
        stats = self.communication_bus.get_statistics()
        result = [
            "📊 通信总线统计信息:",
            f"   总消息数: {stats['total_messages']}",
            f"   直接消息: {stats['direct_messages']}",
            f"   广播消息: {stats['broadcast_messages']}",
            f"   注册代理数: {stats['registered_agents']}",
            "\n各代理统计:"
        ]

        for agent_id, agent_stats in stats['agent_statistics'].items():
            result.append(f"\n   {agent_id}:")
            result.append(f"      待处理消息: {agent_stats['pending_messages']}")
            result.append(f"      已发送: {agent_stats['sent']}")
            result.append(f"      已接收: {agent_stats['received']}")

        return "\n".join(result)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: send(发送消息), broadcast(广播消息), receive(接收消息), get_agents(获取代理列表), get_history(获取历史消息), get_statistics(获取统计信息)",
                required=True
            ),
            ToolParameter(
                name="sender",
                type="string",
                description="发送者代理ID (send/broadcast 操作必需)",
                required=False
            ),
            ToolParameter(
                name="receiver",
                type="string",
                description="接收者代理ID (send 操作必需)",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="消息内容 (send/broadcast 操作必需)",
                required=False
            ),
            ToolParameter(
                name="agent_id",
                type="string",
                description="代理ID (receive/get_history 操作必需)",
                required=False
            ),
            ToolParameter(
                name="exclude_sender",
                type="boolean",
                description="广播时是否排除发送者 (默认: true)",
                required=False,
                default=True
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回消息数量限制 (默认: 10/20)",
                required=False,
                default=10
            )
        ]

    def register_agent(self, agent_id: str, agent: Any) -> None:
        self.communication_bus.register_agent(agent_id, agent)

    def unregister_agent(self, agent_id: str) -> None:
        self.communication_bus.unregister_agent(agent_id)

    def get_communication_bus(self) -> CommunicationBus:
        return self.communication_bus
