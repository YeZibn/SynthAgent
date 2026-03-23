"""RAG工具 - 提供向量查询（检索）核心能力"""
import os
from typing import Dict, Any, List, Optional
from hello_agents.tool.tool import Tool, ToolParameter
from hello_agents.config.rag_config import RAGConfig
from hello_agents.memory.qdrant.qdrant_vector_store import QdrantVectorStore

class RAGTool(Tool):
    """RAG工具
    
    提供核心的向量查询（检索）能力：
    - 智能检索与召回
    - 相似度排序
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        config: Optional[RAGConfig] = None
    ):
        super().__init__(
            name="rag", 
            description="RAG检索增强生成工具，提供智能向量查询能力")
        
        self.user_id = user_id
        self.config = config or RAGConfig()
        # 使用用户ID作为命名空间的一部分
        self.user_namespace = f"{self.config.rag_namespace}_{user_id}"
        
        self.embedder = self._create_embedding_model()
        self.qdrant_client = QdrantVectorStore(
            config.qdrant_url, 
            config.qdrant_api_key, 
            config.collection_name
        )

    def _create_embedding_model(self):
        """创建嵌入模型"""
        try:
            import os
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', 
                          cache_folder='./models')
            print("模型加载成功！")
            return model
        except Exception as e:
            print(f"加载嵌入模型失败: {e}")
            class SimpleEmbedder:
                def encode(self, text: str) -> List[float]:
                    vector = [0.0] * 384
                    for i, c in enumerate(text[:384]):
                        vector[i] = ord(c) / 128.0
                    return vector
            return SimpleEmbedder()
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行RAG工具
        
        只支持 search 操作：
        - search: 检索文档
        """
        action = parameters.get("action", "search")
        
        if action == "search":
            return self._search_documents(parameters)
        else:
            return f"❌ 未知的操作: {action}。仅支持的操作: search"
    
    def _search_documents(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检索文档"""
        query = parameters.get("query")
        if not query:
            return "❌ 缺少必填参数: query"
        
        top_k = parameters.get("top_k", self.config.top_k)
        
        try:
            if not self.embedder:
                return "❌ 嵌入模型未初始化，无法检索文档"
            
            if not self.qdrant_client:
                return "❌ Qdrant客户端未初始化，无法检索文档"
            
            query_vector = self.embedder.encode(query).tolist()
            
            search_result = self.qdrant_client.search(
                collection_name=self.config.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter={
                    "must": [
                        {"key": "namespace", "match": {"value": self.user_namespace}},
                        {"key": "user_id", "match": {"value": self.user_id}}
                    ]
                }
            )
            
            if not search_result:
                return f"❌ 未找到相关文档，查询: {query}"

            
            return search_result
        except Exception as e:
            return f"❌ 检索文档失败: {str(e)}"
    
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
    rag_tool = RAGTool()
    
    print("\n=== 测试检索文档 ===")
    result = rag_tool.run({
        "action": "search",
        "query": "什么是Hello Agents",
        "top_k": 3
    })
    print(result)
