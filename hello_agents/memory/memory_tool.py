from typing import Dict, Any, List, Optional
from datetime import datetime
from hello_agents.tool.tool import Tool, ToolParameter
from hello_agents.memory.memory_manager import MemoryManager
from hello_agents.config.memory_config import MemoryConfig
from hello_agents.memory.memory import MemoryItem


class MemoryTool(Tool):
    """记忆工具 - 为Agent提供记忆存储和检索功能
    
    支持三种记忆类型：
    - working: 工作记忆（短期、容量有限）
    - episodic: 情景记忆（对话历史、事件）
    - semantic: 语义记忆（知识、实体关系）
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        memory_config: Optional[MemoryConfig] = None,
        memory_types: Optional[List[str]] = None
    ):
        super().__init__(
            name="memory",
            description="记忆工具 - 可以存储和检索对话历史、知识和经验。支持工作记忆(短期)、情景记忆(对话历史)、语义记忆(知识图谱)三种类型。"
        )
        
        self.user_id = user_id
        self.memory_config = memory_config or MemoryConfig()
        self.memory_types = memory_types or ["working", "episodic", "semantic"]
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager(
            config=self.memory_config,
            user_id=user_id,
            enable_working="working" in self.memory_types,
            enable_episodic="episodic" in self.memory_types,
            enable_semantic="semantic" in self.memory_types
        )
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行记忆操作
        
        Args:
            parameters: {
                "action": "store" | "retrieve" | "retrieve_by_session" | "stats",
                "content": str,  # store时使用
                "memory_type": "working" | "episodic" | "semantic",
                "query": str,  # retrieve时使用
                "session_id": str,  # retrieve_by_session时使用
                "importance": float,  # store时使用 (0-1)
                "metadata": dict  # store时使用
            }
        """
        action = parameters.get("action", "retrieve")
        
        try:
            if action == "store":
                return self._store_memory(parameters)
            elif action == "retrieve":
                return self._retrieve_memory(parameters)
            elif action == "retrieve_by_session":
                return self._retrieve_by_session(parameters)
            elif action == "retrieve_all":
                return self._retrieve_all(parameters)
            elif action == "stats":
                return self._get_stats(parameters)
            else:
                return f"不支持的操作: {action}"
        except Exception as e:
            return f"记忆操作失败: {str(e)}"
    
    def _store_memory(self, parameters: Dict[str, Any]) -> str:
        """存储记忆"""
        content = parameters.get("content", "")
        memory_type = parameters.get("memory_type", "episodic")
        importance = parameters.get("importance", 0.5)
        metadata = parameters.get("metadata", {})
        
        if not content:
            return "错误: 内容不能为空"
        
        # 确保包含用户ID
        if "user_id" not in metadata:
            metadata["user_id"] = self.user_id
        
        memory_item = MemoryItem(
            content=content,
            importance=importance,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        memory_id = self.memory_manager.add(memory_item, memory_type=memory_type)
        return f"记忆存储成功 [类型: {memory_type}] [ID: {memory_id[:8]}...]"
    
    def _retrieve_memory(self, parameters: Dict[str, Any]) -> str:
        """检索记忆"""
        query = parameters.get("query", "")
        memory_type = parameters.get("memory_type")
        limit = parameters.get("limit", 5)
        
        if not query:
            return "错误: 查询内容不能为空"
        
        if memory_type:
            results = self.memory_manager.retrieve(
                query, 
                limit=limit, 
                memory_types=[memory_type]
            )
            memories = results.get(memory_type, [])
        else:
            memories = self.memory_manager.retrieve_all(query, limit=limit)
        
        if not memories:
            return f"未找到与 '{query}' 相关的记忆"
        
        output = f"找到 {len(memories)} 条相关记忆:\n"
        for i, mem in enumerate(memories, 1):
            # 防御性编程：确保 content 是字符串
            content = mem.content if isinstance(mem.content, str) else str(mem.content)
            content_preview = content[:100] + "..." if len(content) > 100 else content
            output += f"\n{i}. {content_preview}"
            output += f"\n   [重要性: {mem.importance:.2f}]"
            
            # 防御性编程：确保 metadata 存在且是字典
            if hasattr(mem, 'metadata') and isinstance(mem.metadata, dict):
                if mem.metadata.get("user_name"):
                    output += f" [用户: {mem.metadata['user_name']}]"
                
                # 防御性编程：确保 tags 是列表
                tags = mem.metadata.get("tags")
                if tags:
                    if isinstance(tags, list):
                        output += f" [标签: {', '.join(tags)}]"
                    else:
                        output += f" [标签: {tags}]"
        
        return output
    
    def _retrieve_by_session(self, parameters: Dict[str, Any]) -> str:
        """按会话检索情景记忆"""
        session_id = parameters.get("session_id", "")
        limit = parameters.get("limit", 10)
        
        if not session_id:
            return "错误: 会话ID不能为空"
        
        memories = self.memory_manager.retrieve_by_session(session_id, limit)
        
        if not memories:
            return f"会话 '{session_id}' 中未找到记忆"
        
        output = f"会话 '{session_id}' 的记忆 ({len(memories)} 条):\n"
        for i, mem in enumerate(memories, 1):
            # 防御性编程：确保 content 是字符串
            content = mem.content if isinstance(mem.content, str) else str(mem.content)
            content_preview = content[:80] + "..." if len(content) > 80 else content
            
            # 防御性编程：确保 timestamp 存在
            if hasattr(mem, 'timestamp') and mem.timestamp:
                time_str = mem.timestamp.strftime("%m-%d %H:%M")
            else:
                time_str = "未知时间"
            
            output += f"\n{i}. [{time_str}] {content_preview}"
        
        return output
    
    def _retrieve_all(self, parameters: Dict[str, Any]) -> str:
        """跨所有记忆类型检索"""
        query = parameters.get("query", "")
        limit = parameters.get("limit", 5)
        
        if not query:
            return "错误: 查询内容不能为空"
        
        results = self.memory_manager.retrieve_all(query, limit=limit)
        
        if not results:
            return f"未找到与 '{query}' 相关的记忆"
        
        output = f"跨记忆类型检索 '{query}'，找到 {len(results)} 条:\n"
        for i, mem in enumerate(results, 1):
            # 防御性编程：确保 content 是字符串
            content = mem.content if isinstance(mem.content, str) else str(mem.content)
            content_preview = content[:80] + "..." if len(content) > 80 else content
            output += f"\n{i}. {content_preview}"
            output += f"\n   [重要性: {mem.importance:.2f}]"
        
        return output
    
    def _get_stats(self, parameters: Dict[str, Any]) -> str:
        """获取记忆统计信息"""
        stats = self.memory_manager.get_stats()
        
        output = f"记忆统计 [用户: {stats['user_id']}]\n"
        output += f"总记忆数: {stats['total_memories']}\n"
        output += "\n各类型统计:\n"
        
        for memory_type, type_stats in stats['memory_types'].items():
            count = type_stats.get("count", type_stats.get("total_memories", 0))
            output += f"  - {memory_type}: {count} 条\n"
        
        return output
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: store(存储), retrieve(检索), retrieve_by_session(按会话检索), retrieve_all(跨类型检索), stats(统计)",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="要存储的记忆内容 (action=store时使用)",
                required=False
            ),
            ToolParameter(
                name="memory_type",
                type="string",
                description="记忆类型: working(工作记忆), episodic(情景记忆), semantic(语义记忆)。注意：每一次调用都必须要有这个参数，用于确定操作的记忆类型",
                required=False,
                default="episodic"
            ),
            ToolParameter(
                name="query",
                type="string",
                description="检索查询内容，我希望查询内容需要编写的比较完整，是一段完整的话 (action=retrieve/retrieve_all时使用)",
                required=False
            ),
            ToolParameter(
                name="session_id",
                type="string",
                description="会话ID (action=retrieve_by_session时使用)",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量限制",
                required=False,
                default=5
            ),
            ToolParameter(
                name="importance",
                type="float",
                description="记忆重要性 (0-1, action=store时必须要返回，用于确定记忆的重要程度)",
                required=False,
                default=0.5
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="额外元数据 (action=store时使用)",
                required=False,
                default={}
            )
        ]


if __name__ == "__main__":
    # 测试记忆工具
    tool = MemoryTool(user_id="user_xiaoming")

    result = tool.run({"action": "retrieve",
        "query": "旅游",
        "memory_type": "episodic",
        "limit": 10
    })
    print(result)

    # # 测试语义记忆存储
    # print("1. 存储语义记忆 - 知识实体")
    # result = tool.run({
    #     "action": "store",
    #     "content": "Python是一种高级编程语言，由Guido van Rossum于1991年创建，以简洁易读的语法著称",
    #     "memory_type": "semantic",
    #     "importance": 0.85,
    #     "metadata": {
    #         "session_id": "session_1",
    #         "user_name": "小明",
    #         "user_id": "user_xiaoming",
    #         "tags": ["编程", "Python", "技术"],
    #     }
    # })
    # print(f"  {result}\n")
    
    # result = tool.run({
    #     "action": "store",
    #     "content": "东京是日本的国都，位于本州岛东部，是世界上人口最多的大都市区之一，以樱花、秋叶原和涩谷闻名",
    #     "memory_type": "semantic",
    #     "importance": 0.8,
    #     "metadata": {
    #         "session_id": "session_1",
    #         "user_name": "小明",
    #         "user_id": "user_xiaoming",
    #         "tags": ["地理", "日本", "东京", "旅行"],
    #         "entity_type": "location",
    #         "entity_name": "东京"
    #     }
    # })
    # print(f"  {result}\n")
    
    # result = tool.run({
    #     "action": "store",
    #     "content": "樱花是蔷薇科樱属植物的花朵，在日本文化中象征生命的短暂与美丽，每年春季盛开",
    #     "memory_type": "semantic",
    #     "importance": 0.75,
    #     "metadata": {
    #         "session_id": "session_1",
    #         "user_name": "小明",
    #         "user_id": "user_xiaoming",
    #         "tags": ["植物", "樱花", "日本文化"],
    #         "entity_type": "nature",
    #         "entity_name": "樱花"
    #     }
    # })
    # print(f"  {result}\n")
    
    # result = tool.run({
    #     "action": "store",
    #     "content": "小明的偏好：喜欢日本文化、热爱编程、计划每年春季旅行、不喜欢辛辣食物",
    #     "memory_type": "semantic",
    #     "importance": 0.9,
    #     "metadata": {
    #         "session_id": "session_1",
    #         "user_name": "小明",
    #         "user_id": "user_xiaoming",
    #         "tags": ["用户画像", "偏好", "个人"],
    #         "entity_type": "user_profile",
    #         "entity_name": "小明"
    #     }
    # })
    # print(f"  {result}\n")
    
    # # 测试语义记忆检索 - 按实体类型
    # print("2. 检索语义记忆 - 查询技术相关")
    # result = tool.run({
    #     "action": "retrieve",
    #     "query": "编程语言 Python",
    #     "memory_type": "semantic",
    #     "limit": 3
    # })
    # print(f"  {result}\n")
    
    # print("3. 检索语义记忆 - 查询地理相关")
    # result = tool.run({
    #     "action": "retrieve",
    #     "query": "东京 日本 城市",
    #     "memory_type": "semantic",
    #     "limit": 3
    # })
    # print(f"  {result}\n")
    
    # print("4. 检索语义记忆 - 查询用户偏好")
    # result = tool.run({
    #     "action": "retrieve",
    #     "query": "小明喜欢什么",
    #     "memory_type": "semantic",
    #     "limit": 3
    # })
    # print(f"  {result}\n")
    
    # # 测试跨类型检索
    # print("5. 跨类型检索 - 查询樱花相关（应包含语义记忆和之前的情景记忆）")
    # result = tool.run({
    #     "action": "retrieve_all",
    #     "query": "樱花 东京",
    #     "limit": 5
    # })
    # print(f"  {result}\n")
    
    # # 测试语义记忆更新（存储新知识覆盖旧知识）
    # print("6. 更新语义记忆 - 添加Python新版本信息")
    # result = tool.run({
    #     "action": "store",
    #     "content": "Python 3.12于2023年发布，引入了改进的错误消息、f-string解析优化和性能提升",
    #     "memory_type": "semantic",
    #     "importance": 0.7,
    #     "metadata": {
    #         "session_id": "session_1",
    #         "user_name": "小明",
    #         "user_id": "user_xiaoming",
    #         "tags": ["编程", "Python", "新版本"],
    #         "entity_type": "technology",
    #         "entity_name": "Python"
    #     }
    # })
    # print(f"  {result}\n")
    
    # # 再次检索验证更新
    # print("7. 再次检索Python相关信息")
    # result = tool.run({
    #     "action": "retrieve",
    #     "query": "Python 版本",
    #     "memory_type": "semantic",
    #     "limit": 3
    # })
    # print(f"  {result}\n")
    
    # # 测试统计信息
    # print("8. 统计信息 - 查看各类型记忆分布")
    # result = tool.run({"action": "stats"})
    # print(f"  {result}\n")
    
    
    
    # # 关闭连接
    # tool.memory_manager.close()
    # print("✅ 测试完成!")
