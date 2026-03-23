
"""RAG模块配置管理"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RAGConfig(BaseModel):
    """RAG配置类"""
    
    knowledge_base_path: str = Field(default="knowledge_base", description="知识库路径")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant向量数据库URL")
    qdrant_api_key: Optional[str] = Field(default="default_api_key", description="Qdrant API密钥")
    collection_name: str = Field(default="rag_collection", description="Qdrant向量数据库集合名称")
    rag_namespace: str = Field(default="rag", description="RAG命名空间")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2", description="文本嵌入模型名称")
    
    top_k: int = Field(default=5, description="检索返回的top-k结果数")
    score_threshold: float = Field(default=0.7, description="检索相似度阈值")
    search_type: str = Field(default="similarity", description="检索类型")
    
    chunk_size: int = Field(default=512, description="文本分块大小")
    chunk_overlap: int = Field(default=50, description="文本分块重叠大小")
    
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存TTL（秒）")
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """从环境变量创建配置"""
        return cls(
            knowledge_base_path=os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY", "default_api_key"),
            collection_name=os.getenv("RAG_COLLECTION_NAME", "rag_collection"),
            rag_namespace=os.getenv("RAG_NAMESPACE", "rag"),
            embedding_model_name=os.getenv("RAG_EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
            top_k=int(os.getenv("RAG_TOP_K", "5")),
            score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.7")),
            search_type=os.getenv("RAG_SEARCH_TYPE", "similarity"),
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "512")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "50")),
            enable_cache=os.getenv("RAG_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.getenv("RAG_CACHE_TTL", "3600"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def from_dict(self, config_dict: dict) -> "RAGConfig":
        """从字典加载配置"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    @field_validator('knowledge_base_path', 'qdrant_url', 'collection_name')
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        """验证必填字段"""
        if not v or not str(v).strip():
            raise ValueError(f"{info.field_name} 不能为空")
        return v
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        validate_assignment = True


if __name__ == "__main__":
    config = RAGConfig.from_env()
    print(config.to_dict())
