"""记忆模块配置管理"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """记忆模块配置类"""
    
    # 工作记忆配置
    working_memory_capacity: int = Field(default=50, description="工作记忆最大容量")
    working_memory_ttl: int = Field(default=60, description="工作记忆TTL（分钟）")
    
    # 情景记忆配置
    database_path: str = Field(default="episodic.db", description="SQLite数据库路径")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant向量数据库URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API密钥")
    qdrant_episodic_collection_name: str = Field(default="collection_episodic_memory", description="Qdrant向量数据库集合名称")

    # 语义记忆配置
    qdrant_semantic_collection_name: str = Field(default="collection_semantic_memory", description="Qdrant向量数据库集合名称")
    
    # 语义记忆配置
    embedding_model_name: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", description="文本嵌入模型名称")
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j图数据库URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j用户名")
    neo4j_password: str = Field(default="12345678", description="Neo4j密码")
    
    # 感知记忆配置
    text_vector_dim: int = Field(default=384, description="文本向量维度")
    image_vector_dim: int = Field(default=512, description="图像向量维度")
    audio_vector_dim: int = Field(default=512, description="音频向量维度")
    
    # 通用配置
    enable_caching: bool = Field(default=True, description="是否启用缓存")
    log_level: str = Field(default="INFO", description="日志级别")
    
    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """从环境变量创建配置"""
        return cls(
            working_memory_capacity=int(os.getenv("WORKING_MEMORY_CAPACITY", "50")),
            working_memory_ttl=int(os.getenv("WORKING_MEMORY_TTL", "60")),
            database_path=os.getenv("DATABASE_PATH", "data/memories/episodic.db"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            text_vector_dim=int(os.getenv("TEXT_VECTOR_DIM", "384")),
            image_vector_dim=int(os.getenv("IMAGE_VECTOR_DIM", "512")),
            audio_vector_dim=int(os.getenv("AUDIO_VECTOR_DIM", "512")),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        validate_assignment = True


if __name__ == "__main__":
    config = MemoryConfig.from_env()
    print(config.to_dict())
