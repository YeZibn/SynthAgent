from typing import Dict, List, Optional, Any
from datetime import datetime
from threading import Lock
from hello_agents.message.message import Message


class CommunicationMessage:
    def __init__(
        self,
        sender: str,
        receiver: str,
        content: str,
        message_type: str = "direct",
        timestamp: datetime = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_type = message_type
        self.timestamp = timestamp or datetime.now()
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class CommunicationBus:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._message_queues: Dict[str, List[CommunicationMessage]] = {}
        self._message_history: List[CommunicationMessage] = []
        self._lock = Lock()

    def register_agent(self, agent_id: str, agent: Any) -> None:
        with self._lock:
            if agent_id in self._agents:
                print(f"⚠️ Agent {agent_id} 已存在，将被覆盖")
            self._agents[agent_id] = agent
            self._message_queues[agent_id] = []
            print(f"✅ Agent {agent_id} 已注册到通信总线")

    def unregister_agent(self, agent_id: str) -> None:
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                del self._message_queues[agent_id]
                print(f"✅ Agent {agent_id} 已从通信总线注销")

    def send_message(self, sender: str, receiver: str, content: str) -> bool:
        with self._lock:
            if receiver not in self._agents:
                print(f"❌ 接收者 {receiver} 不存在")
                return False

            message = CommunicationMessage(
                sender=sender,
                receiver=receiver,
                content=content,
                message_type="direct"
            )

            self._message_queues[receiver].append(message)
            self._message_history.append(message)
            print(f"📨 {sender} -> {receiver}: {content[:50]}...")
            return True

    def broadcast_message(self, sender: str, content: str, exclude_sender: bool = True) -> int:
        with self._lock:
            count = 0
            receivers = []

            for agent_id in self._agents:
                if exclude_sender and agent_id == sender:
                    continue
                receivers.append(agent_id)

            for receiver in receivers:
                message = CommunicationMessage(
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    message_type="broadcast"
                )
                self._message_queues[receiver].append(message)
                self._message_history.append(message)
                count += 1

            print(f"📢 {sender} 广播消息给 {count} 个接收者: {content[:50]}...")
            return count

    def receive_messages(self, agent_id: str) -> List[CommunicationMessage]:
        with self._lock:
            if agent_id not in self._message_queues:
                return []

            messages = self._message_queues[agent_id].copy()
            self._message_queues[agent_id].clear()
            return messages

    def peek_messages(self, agent_id: str) -> List[CommunicationMessage]:
        with self._lock:
            if agent_id not in self._message_queues:
                return []
            return self._message_queues[agent_id].copy()

    def get_message_count(self, agent_id: str) -> int:
        with self._lock:
            if agent_id not in self._message_queues:
                return 0
            return len(self._message_queues[agent_id])

    def get_all_agents(self) -> List[str]:
        with self._lock:
            return list(self._agents.keys())

    def get_agent(self, agent_id: str) -> Optional[Any]:
        with self._lock:
            return self._agents.get(agent_id)

    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            history = self._message_history[-limit:] if limit > 0 else self._message_history
            return [msg.to_dict() for msg in history]

    def get_history_for_agent(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            filtered = [
                msg for msg in self._message_history
                if msg.sender == agent_id or msg.receiver == agent_id
            ]
            history = filtered[-limit:] if limit > 0 else filtered
            return [msg.to_dict() for msg in history]

    def clear_history(self) -> None:
        with self._lock:
            self._message_history.clear()
            print("✅ 消息历史已清空")

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            total_messages = len(self._message_history)
            direct_messages = sum(1 for msg in self._message_history if msg.message_type == "direct")
            broadcast_messages = sum(1 for msg in self._message_history if msg.message_type == "broadcast")

            agent_stats = {}
            for agent_id in self._agents:
                agent_stats[agent_id] = {
                    "pending_messages": len(self._message_queues[agent_id]),
                    "sent": sum(1 for msg in self._message_history if msg.sender == agent_id),
                    "received": sum(1 for msg in self._message_history if msg.receiver == agent_id)
                }

            return {
                "total_messages": total_messages,
                "direct_messages": direct_messages,
                "broadcast_messages": broadcast_messages,
                "registered_agents": len(self._agents),
                "agent_statistics": agent_stats
            }

    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"CommunicationBus(agents={stats['registered_agents']}, messages={stats['total_messages']})"
