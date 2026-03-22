from typing import List, Dict, Optional
from datetime import datetime
from hello_agents.memory.memory import MemoryItem
from hello_agents.config.memory_config import MemoryConfig
from hello_agents.memory.memory_list.working_memory import WorkingMemory
from hello_agents.memory.memory_list.episodic_memory import EpisodicMemory
from hello_agents.memory.memory_list.semantic_memory import SemanticMemory


class MemoryManager:
    """记忆管理器 - 统一的记忆操作接口
    
    特点：
    - 统一管理工作记忆、情景记忆、语义记忆
    - 支持用户隔离
    - 提供跨记忆类型的混合检索
    - 简化的API接口
    """
    
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        user_id: str = "default_user",
        enable_working: bool = True,
        enable_episodic: bool = True,
        enable_semantic: bool = True
    ):
        self.config = config or MemoryConfig()
        self.user_id = user_id
        
        # 初始化各类型记忆
        self.memory_types = {}
        
        if enable_working:
            self.memory_types['working'] = WorkingMemory(self.config)
        
        if enable_episodic:
            self.memory_types['episodic'] = EpisodicMemory(self.config)
        
        if enable_semantic:
            self.memory_types['semantic'] = SemanticMemory(self.config)
    
    def add(self, memory_item: MemoryItem, memory_type: str = "episodic") -> str:
        """添加记忆到指定类型"""
        if memory_type not in self.memory_types:
            raise ValueError(f"不支持的记忆类型: {memory_type}")
        
        # 确保记忆包含用户ID
        if "user_id" not in memory_item.metadata:
            memory_item.metadata["user_id"] = self.user_id
        
        memory = self.memory_types[memory_type]
        return memory.add(memory_item)
    
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, List[MemoryItem]]:
        """跨记忆类型检索
        
        Args:
            query: 查询文本
            limit: 每种类型返回的最大数量
            memory_types: 要检索的记忆类型列表，None表示全部
            **kwargs: 其他过滤条件（如user_id）
        
        Returns:
            按记忆类型分组的检索结果
        """
        # 确保使用当前用户ID
        if "user_id" not in kwargs:
            kwargs["user_id"] = self.user_id
        
        # 确定要检索的记忆类型
        types_to_search = memory_types or list(self.memory_types.keys())
        
        results = {}
        for memory_type in types_to_search:
            if memory_type in self.memory_types:
                memory = self.memory_types[memory_type]
                results[memory_type] = memory.retrieve(query, limit, **kwargs)
        
        return results
    
    def retrieve_all(
        self,
        query: str,
        limit: int = 5,
        **kwargs
    ) -> List[MemoryItem]:
        """跨记忆类型混合检索
        
        从所有记忆类型中检索，并按相关性排序返回统一结果
        """
        # 确保使用当前用户ID
        if "user_id" not in kwargs:
            kwargs["user_id"] = self.user_id
        
        all_results = []
        
        for memory_type, memory in self.memory_types.items():
            type_results = memory.retrieve(query, limit, **kwargs)
            all_results.extend(type_results)
        
        # 按重要性排序
        all_results.sort(key=lambda x: x.importance, reverse=True)
        
        return all_results[:limit]
    
    def retrieve_by_session(self, session_id: str, limit: int = 10) -> List[MemoryItem]:
        """按会话检索情景记忆"""
        if "episodic" in self.memory_types:
            return self.memory_types["episodic"].retrieve_by_session(session_id, limit, user_id=self.user_id)
        return []
    
    def retrieve_by_entity(self, entity_name: str, limit: int = 10) -> List[MemoryItem]:
        """按实体检索语义记忆"""
        if "semantic" in self.memory_types:
            return self.memory_types["semantic"].retrieve_by_entity(entity_name, limit, user_id=self.user_id)
        return []
    
    def retrieve_by_relation(self, relation_type: str, limit: int = 10) -> List[MemoryItem]:
        """按关系类型检索语义记忆"""
        if "semantic" in self.memory_types:
            return self.memory_types["semantic"].retrieve_by_relation(relation_type, limit, user_id=self.user_id)
        return []
    
    def get_stats(self) -> Dict:
        """获取所有记忆类型的统计信息"""
        stats = {
            "user_id": self.user_id,
            "memory_types": {}
        }
        
        for memory_type, memory in self.memory_types.items():
            if hasattr(memory, "get_stats"):
                stats["memory_types"][memory_type] = memory.get_stats(user_id=self.user_id)
            elif hasattr(memory, "get_session_stats"):
                stats["memory_types"][memory_type] = memory.get_session_stats(user_id=self.user_id)
            elif hasattr(memory, "get_entity_stats"):
                stats["memory_types"][memory_type] = memory.get_entity_stats(user_id=self.user_id)
        
        # 汇总统计
        stats["total_memories"] = sum(
            s.get("count", s.get("total_memories", 0))
            for s in stats["memory_types"].values()
        )
        
        return stats
    
    def get_memory(self, memory_type: str) -> Optional[object]:
        """获取指定类型的记忆实例"""
        return self.memory_types.get(memory_type)
    
    def clear(self, memory_type: Optional[str] = None) -> None:
        """清空记忆
        
        Args:
            memory_type: 要清空的记忆类型，None表示清空所有
        """
        if memory_type:
            if memory_type in self.memory_types:
                memory = self.memory_types[memory_type]
                if hasattr(memory, "clear"):
                    memory.clear()
        else:
            for memory in self.memory_types.values():
                if hasattr(memory, "clear"):
                    memory.clear()
    
    def close(self) -> None:
        """关闭所有记忆连接"""
        for memory in self.memory_types.values():
            if hasattr(memory, "close"):
                memory.close()