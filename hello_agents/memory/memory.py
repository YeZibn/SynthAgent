from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
from hello_agents.config import memory_config
from hello_agents.config.memory_config import MemoryConfig

class MemoryItem:
    """记忆项数据类"""
    
    def __init__(
        self,
        content: str,
        memory_id: Optional[str] = None,
        importance: float = 0.5,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ):
        self.id = memory_id or self._generate_id()
        self.content = content
        self.importance = max(0.0, min(1.0, importance))  # 限制在 0-1 范围
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return f"wm_{uuid.uuid4().hex[:12]}"


class BaseMemory(ABC):
    """记忆基类"""
    
    def __init__(self, config: MemoryConfig, storage_backend=None):
        self.config = config
        self.storage_backend = storage_backend
    
    @abstractmethod
    def add(self, memory_item: MemoryItem) -> str:
        """添加记忆"""
        pass

    @abstractmethod
    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """检索"""
        pass