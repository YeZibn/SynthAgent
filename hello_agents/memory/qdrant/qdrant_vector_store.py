from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from typing import List, Dict, Optional
import time
import os
import uuid


class QdrantVectorStore:
    """Qdrant向量存储
    
    特点：
    - 支持连接重试机制
    - 优雅处理服务不可用情况
    - 本地队列缓存（可选）
    """
    
    def __init__(self, url: str, api_key: Optional[str], collection_name: str = "memory_collection", vector_size: int = 384):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._client = None
        self._connected = False
        self._max_retries = 3
        self._retry_delay = 1.0
        self._init_client()
    
    def _init_client(self):
        """初始化Qdrant客户端"""
        try:
            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=10.0
            )
            
            # 测试连接
            self._client.get_collections()
            self._connected = True
            
            # 创建集合（如果不存在）
            self._ensure_collection()
            
        except Exception as e:
            print(f"Qdrant连接失败: {e}")
            self._connected = False
    
    def _ensure_collection(self):
        """确保集合存在"""
        if not self._connected:
            return
        
        try:
            # 检查集合是否存在
            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                # 创建集合
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"创建Qdrant集合: {self.collection_name}")
        except Exception as e:
            print(f"创建集合失败: {e}")
    
    def _retry_operation(self, operation, *args, **kwargs):
        """带重试的操作"""
        for attempt in range(self._max_retries):
            try:
                if not self._connected:
                    self._init_client()
                
                if not self._connected:
                    raise Exception("Qdrant服务不可用")
                
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt < self._max_retries - 1:
                    print(f"操作失败，{self._retry_delay}秒后重试... ({attempt + 1}/{self._max_retries})")
                    time.sleep(self._retry_delay)
                    self._connected = False
                else:
                    raise e
    
    def _convert_id(self, memory_id: str):
        """将字符串ID转换为UUID格式"""
        try:
            uuid.UUID(memory_id)
            return memory_id
        except (ValueError, AttributeError):
            new_uuid = str(uuid.uuid4())
            return new_uuid
    
    def add(self, memory_id: str, vector: List[float], metadata: Dict):
        """添加向量和元数据"""
        try:
            self._retry_operation(
                self._client.upsert,
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=self._convert_id(memory_id),
                        vector=vector,
                        payload=metadata
                    )
                ]
            )
        except Exception as e:
            print(f"Qdrant添加向量失败: {e}")
            pass
    
    def add_batch(self, memory_ids: List[str], vectors: List[List[float]], metadata_list: List[Dict]):
        """批量添加向量"""
        try:
            points = []
            for memory_id, vector, metadata in zip(memory_ids, vectors, metadata_list):
                points.append(PointStruct(
                    id=self._convert_id(memory_id),
                    vector=vector,
                    payload=metadata
                ))
            
            self._retry_operation(
                self._client.upsert,
                collection_name=self.collection_name,
                points=points
            )
        except Exception as e:
            print(f"Qdrant批量添加向量失败: {e}")
            pass
    
    def search(self, query_vector: List[float], limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict]:
        """向量搜索"""
        try:
            search_result = self._retry_operation(
                self._client.query_points,
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=filter_conditions
            )
            
            hits = []
            for result in search_result.points:
                memory_id = result.payload.get("memory_id", str(result.id))
                hits.append({
                    "id": memory_id,
                    "uuid": str(result.id),
                    "score": result.score,
                    "metadata": result.payload
                })
            
            return hits
        except Exception as e:
            print(f"Qdrant搜索失败: {e}")
            return []
    
    def delete(self, memory_id: str):
        """删除向量"""
        try:
            uuid_id = self._convert_id(memory_id)
            self._retry_operation(
                self._client.delete,
                collection_name=self.collection_name,
                points_selector=uuid_id
            )
        except Exception as e:
            print(f"Qdrant删除向量失败: {e}")
    
    def delete_batch(self, memory_ids: List[str]):
        """批量删除向量"""
        try:
            uuid_ids = [self._convert_id(mid) for mid in memory_ids]
            self._retry_operation(
                self._client.delete,
                collection_name=self.collection_name,
                points_selector=uuid_ids
            )
        except Exception as e:
            print(f"Qdrant批量删除向量失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取集合统计信息"""
        try:
            if not self._connected:
                return {"status": "disconnected"}
            
            return {
                "status": "connected",
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"status": "error"}
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def reconnect(self):
        """重新连接"""
        self._init_client()


if __name__ == "__main__":
    # 测试代码
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
    
    # 初始化向量存储
    store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name="test_memory_collection",
        vector_size=384
    )
    
    # 检查连接状态
    print(f"连接状态: {store.is_connected()}")
    
    # 获取统计信息
    stats = store.get_stats()
    print(f"集合统计: {stats}")
    
    # 测试添加单个向量
    print("\n--- 测试添加单个向量 ---")
    test_vector = [0.1] * 384
    store.add(
        memory_id="memory_001",
        vector=test_vector,
        metadata={
            "content": "这是一个测试记忆",
            "timestamp": time.time(),
            "importance": 0.8,
            "tags": ["test", "memory"]
        }
    )
    print("添加单个向量完成")
    
    # 测试批量添加
    print("\n--- 测试批量添加向量 ---")
    memory_ids = ["memory_002", "memory_003", "memory_004"]
    vectors = [[0.2] * 384, [0.3] * 384, [0.4] * 384]
    metadata_list = [
        {"content": "批量测试1", "timestamp": time.time(), "importance": 0.7},
        {"content": "批量测试2", "timestamp": time.time(), "importance": 0.9},
        {"content": "批量测试3", "timestamp": time.time(), "importance": 0.5}
    ]
    store.add_batch(memory_ids, vectors, metadata_list)
    print("批量添加向量完成")
    
    # 测试搜索
    print("\n--- 测试向量搜索 ---")
    query_vector = [0.15] * 384
    results = store.search(query_vector, limit=3)
    print(f"搜索结果 (返回{len(results)}条):")
    for hit in results:
        print(f"  ID: {hit['id']}, 相似度: {hit['score']:.4f}, 元数据: {hit['metadata']}")
    
    # 再次获取统计信息
    print("\n--- 更新后的统计信息 ---")
    stats = store.get_stats()
    print(f"集合统计: {stats}")
    
    # 测试删除
    print("\n--- 测试删除向量 ---")
    store.delete("memory_004")
    print("删除 memory_004 完成")
    
    # 批量删除
    print("\n--- 测试批量删除 ---")
    store.delete_batch(["memory_002", "memory_003"])
    print("批量删除 memory_002, memory_003 完成")
    
    # 最终统计
    print("\n--- 最终统计信息 ---")
    stats = store.get_stats()
    print(f"集合统计: {stats}")
    
    print("\n测试完成!")
