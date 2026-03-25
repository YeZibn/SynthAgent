from typing import Dict, List, Optional, Any
from datetime import datetime
from synth_agent.agent.agent import Agent
from synth_agent.agent.multi_agent.shared_memory import SharedMemory
from synth_agent.agent.multi_agent.communication_bus import CommunicationBus
from synth_agent.agent.react_agent import ReActAgent


class AgentTeam:
    """
    智能体团队
    职责：成员创建、管理
    不负责任务编排与执行
    支持三种协作模式：hierarchical, peer_to_peer, pipeline
    """

    def __init__(self, team_name: str, collaboration_mode: str = "peer_to_peer"):
        self.team_name = team_name
        self.collaboration_mode = collaboration_mode
        self.members: Dict[str, ReActAgent] = {}  # role -> ReActAgent
        self.communication_bus = CommunicationBus()
        self.shared_memory = SharedMemory()
        self.coordinator_role: Optional[str] = None

    def add_agent(self, role: str, agent: ReActAgent, is_coordinator: bool = False) -> None:
        """添加智能体到团队，按角色管理"""
        if role in self.members:
            print(f"⚠️ 角色 {role} 已存在，将覆盖")

        if is_coordinator:
            self.coordinator_role = role
            print(f"💡 自动选择协调者: {role}")

        self.members[role] = agent
        self.communication_bus.register_agent(role, agent)
        print(f"✅ 团队 {self.team_name} 添加成员: {role}({agent.name})")

    def get_agent(self, role: str) -> Optional[ReActAgent]:
        return self.members.get(role)

    def get_all_roles(self) -> List[str]:
        return list(self.members.keys())

    def __len__(self):
        return len(self.members)

    def __str__(self):
        return f"AgentTeam({self.team_name}, roles={self.get_all_roles()})"