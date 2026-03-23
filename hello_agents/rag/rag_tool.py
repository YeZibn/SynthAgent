"""RAG工具 - 提供向量查询（检索）核心能力"""
import os
from typing import Dict, Any, List, Optional
from hello_agents.tool.tool import Tool, ToolParameter
from hello_agents.config.rag_config import RAGConfig
from hello_agents.memory.qdrant.qdrant_vector_store import QdrantVectorStore
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchText
from hello_agents.embedder.qwen_embedder import QwenEmbedder

class RAGTool(Tool):
    """RAG工具
    
    提供核心的向量查询（检索）能力：
    - 智能检索与召回
    - 相似度排序
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        rag_config: Optional[RAGConfig] = None
    ):
        super().__init__(
            name="rag", 
            description="RAG检索增强生成工具，提供智能向量查询能力")
        
        self.user_id = user_id
        self.config = rag_config or RAGConfig()
        # 使用用户ID作为命名空间的一部分
        self.user_namespace = f"{self.config.rag_namespace}_{user_id}"
        
        self.embedder = self._create_embedding_model()
        self.qdrant_client = QdrantVectorStore(
            self.config.qdrant_url, 
            self.config.qdrant_api_key, 
            self.config.collection_name
        )

    def _create_embedding_model(self):
        return QwenEmbedder()
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行RAG工具
        
        只支持 search 操作：
        - search: 检索文档
        """
        action = parameters.get("action", "search")
        
        if action == "search":
            results = self._search_documents(parameters)
            if not results:
                return "❌ 未找到相关文档"
            
            # 格式化搜索结果为字符串
            output = f"找到 {len(results)} 条相关文档:\n"
            for i, result in enumerate(results, 1):
                content = result.get("metadata", {}).get("content", "")
                source = result.get("metadata", {}).get("source", "未知来源")
                score = result.get("score", 0)
                
                content_preview = content[:100] + "..." if len(content) > 100 else content
                output += f"\n{i}. {content_preview}"
                output += f"\n   来源: {source}"
                output += f"\n   相似度: {score:.3f}"
            
            return output
        else:
            return f"❌ 未知的操作: {action}。仅支持的操作: search"
    
    def _search_documents(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检索文档"""
        query = parameters.get("query")
        if not query:
            return []
        
        top_k = parameters.get("top_k", self.config.top_k)
        
        try:
            if not self.embedder:
                return []
            
            if not self.qdrant_client:
                return []
            
            query_vector = self.embedder.encode(query)

            search_result = self.qdrant_client.search(
                query_vector=query_vector,
                limit=top_k,
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="namespace",
                            match=MatchText(text=self.user_namespace)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchText(text=self.user_id)
                        )
                    ]
                )
            )
            
            return search_result
        except Exception as e:
            print(f"检索文档失败: {str(e)}")
            return []
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: search(检索文档)",
                required=True
            ),
            ToolParameter(
                name="query",
                type="string",
                description="检索查询（search操作必填）",
                required=True
            ),
            ToolParameter(
                name="top_k",
                type="integer",
                description="检索结果数量，默认5",
                required=False
            )
        ]


if __name__ == "__main__":
    rag_tool = RAGTool(user_id="user_xiaoming")
    
    print("\n=== 测试检索文档 ===")
    result = rag_tool.run({
        "action": "search",
        "query": "人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。 机器学习是人工智能的一个子集，它使用统计技术使计算机能够从数据中学习，而无需明确编程。 深度学习是机器学习的一个分支，它使用多层神经网络来模拟人脑的工作方式。",
        "top_k": 3
    })
    print(result)


