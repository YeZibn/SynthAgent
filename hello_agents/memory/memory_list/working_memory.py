import re
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter
from hello_agents.memory.memory import MemoryItem, BaseMemory
from hello_agents.config.memory_config import MemoryConfig



class WorkingMemory(BaseMemory):
    """工作记忆实现
    特点：
    - 容量有限（默认50条）+ TTL自动清理
    - 纯内存存储，访问速度极快
    - 混合检索：TF-IDF向量化 + 关键词匹配
    """
    
    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # 工作记忆配置
        self.max_capacity = getattr(config, 'working_memory_capacity', None) or 50
        self.max_age_minutes = getattr(config, 'working_memory_ttl', None) or 60
        self.memories: List[MemoryItem] = []
        
        # TF-IDF 相关缓存
        self._tfidf_cache: Dict[str, Dict[str, float]] = {}
        self._idf_cache: Dict[str, float] = {}
        self._cache_valid = False
    
    def add(self, memory_item: MemoryItem) -> str:
        """添加工作记忆"""
        self._expire_old_memories()  # 过期清理
        
        if len(self.memories) >= self.max_capacity:
            self._remove_lowest_priority_memory()  # 容量管理
        
        self.memories.append(memory_item)
        self._cache_valid = False  # 使TF-IDF缓存失效
        return memory_item.id
    
    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """混合检索：TF-IDF向量化 + 关键词匹配"""
        self._expire_old_memories()
        
        if not self.memories:
            return []
        
        # 尝试TF-IDF向量检索
        vector_scores = self._try_tfidf_search(query)
        
        # 计算综合分数
        scored_memories = []
        for memory in self.memories:
            vector_score = vector_scores.get(memory.id, 0.0)
            keyword_score = self._calculate_keyword_score(query, memory.content)
            
            # 混合评分
            base_relevance = vector_score * 0.7 + keyword_score * 0.3 if vector_score > 0 else keyword_score
            time_decay = self._calculate_time_decay(memory.timestamp)
            importance_weight = 0.8 + (memory.importance * 0.4)
            
            final_score = base_relevance * time_decay * importance_weight
            if final_score > 0:
                scored_memories.append((final_score, memory))
        
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]
    
    def _expire_old_memories(self) -> None:
        """清理过期记忆（基于TTL）"""
        if not self.memories:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=self.max_age_minutes)
        original_count = len(self.memories)
        
        self.memories = [
            memory for memory in self.memories 
            if memory.timestamp > cutoff_time
        ]
        
        if len(self.memories) < original_count:
            self._cache_valid = False  # 使TF-IDF缓存失效
    
    def _remove_lowest_priority_memory(self) -> None:
        """移除优先级最低的记忆（重要性低且时间最旧的）"""
        if not self.memories:
            return
        
        # 计算每个记忆的综合优先级分数
        # 分数越低越容易被移除
        def calculate_removal_score(memory: MemoryItem) -> float:
            # 重要性越低，分数越低
            importance_score = memory.importance
            
            # 时间越旧，分数越低
            age_hours = (datetime.now() - memory.timestamp).total_seconds() / 3600
            recency_score = math.exp(-0.1 * age_hours)  # 指数衰减
            
            # 综合分数（重要性权重更高）
            return importance_score * 0.6 + recency_score * 0.4
        
        # 找到分数最低的记忆并移除
        lowest_priority_memory = min(self.memories, key=calculate_removal_score)
        self.memories.remove(lowest_priority_memory)
        print(f"移除最低优先级工作记忆: {lowest_priority_memory.content}")
        self._cache_valid = False  # 使TF-IDF缓存失效
    
    def _tokenize(self, text: str) -> List[str]:
        """简单的中文/英文分词"""
        # 转换为小写
        text = text.lower()
        
        # 提取中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        
        # 提取英文单词
        english_words = re.findall(r'[a-z]+', text)
        
        # 合并结果
        tokens = chinese_chars + english_words
        
        # 过滤停用词（简单的常见词）
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那'}
        tokens = [t for t in tokens if t not in stopwords and len(t) > 1 or t in chinese_chars]
        
        return tokens
    
    def _build_tfidf(self) -> None:
        """构建TF-IDF模型"""
        if self._cache_valid and self._tfidf_cache:
            return
        
        if not self.memories:
            self._tfidf_cache = {}
            self._idf_cache = {}
            self._cache_valid = True
            return
        
        # 收集所有文档的词频
        documents: Dict[str, List[str]] = {}
        for memory in self.memories:
            documents[memory.id] = self._tokenize(memory.content)
        
        # 计算IDF
        all_terms = set()
        for tokens in documents.values():
            all_terms.update(tokens)
        
        doc_count = len(documents)
        self._idf_cache = {}
        
        for term in all_terms:
            # 包含该词的文档数
            doc_freq = sum(1 for tokens in documents.values() if term in tokens)
            # IDF = log(N / df)
            self._idf_cache[term] = math.log(doc_count / (doc_freq + 1)) + 1
        
        # 计算TF-IDF向量
        self._tfidf_cache = {}
        for memory_id, tokens in documents.items():
            term_counts = Counter(tokens)
            total_terms = len(tokens) if tokens else 1
            
            tfidf_vector = {}
            for term, count in term_counts.items():
                tf = count / total_terms
                idf = self._idf_cache.get(term, 1.0)
                tfidf_vector[term] = tf * idf
            
            self._tfidf_cache[memory_id] = tfidf_vector
        
        self._cache_valid = True
    
    def _try_tfidf_search(self, query: str) -> Dict[str, float]:
        """使用TF-IDF进行向量相似度搜索"""
        self._build_tfidf()
        
        if not self._tfidf_cache:
            return {}
        
        # 对查询进行分词并计算TF-IDF
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return {}
        
        query_counts = Counter(query_tokens)
        total_query_terms = len(query_tokens)
        
        query_vector = {}
        for term, count in query_counts.items():
            tf = count / total_query_terms
            idf = self._idf_cache.get(term, 1.0)
            query_vector[term] = tf * idf
        
        # 计算余弦相似度
        scores = {}
        for memory_id, memory_vector in self._tfidf_cache.items():
            # 计算点积
            dot_product = sum(
                query_vector.get(term, 0) * weight 
                for term, weight in memory_vector.items()
            )
            
            # 计算向量模长
            query_norm = math.sqrt(sum(w ** 2 for w in query_vector.values()))
            memory_norm = math.sqrt(sum(w ** 2 for w in memory_vector.values()))
            
            # 余弦相似度
            if query_norm > 0 and memory_norm > 0:
                cosine_sim = dot_product / (query_norm * memory_norm)
                scores[memory_id] = max(0.0, cosine_sim)  # 确保非负
            else:
                scores[memory_id] = 0.0
        
        return scores
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """计算关键词匹配分数"""
        query_tokens = set(self._tokenize(query))
        content_tokens = self._tokenize(content)
        
        if not query_tokens or not content_tokens:
            return 0.0
        
        # 计算匹配的词数
        matches = sum(1 for token in content_tokens if token in query_tokens)
        
        # Jaccard相似度
        content_token_set = set(content_tokens)
        union = query_tokens | content_token_set
        intersection = query_tokens & content_token_set
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # 结合词频匹配率和Jaccard相似度
        match_ratio = matches / len(content_tokens) if content_tokens else 0
        
        return jaccard * 0.7 + match_ratio * 0.3
    
    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """计算时间衰减因子"""
        age_minutes = (datetime.now() - timestamp).total_seconds() / 60
        
        # 指数衰减：在TTL时间内保持较高分数，之后逐渐衰减
        # 使用半衰期模型
        half_life = self.max_age_minutes / 2
        if half_life <= 0:
            return 1.0
        
        decay = math.exp(-0.693 * age_minutes / half_life)
        
        # 确保最低分数为0.1
        return max(0.1, decay)
    
    def clear(self) -> None:
        """清空所有工作记忆"""
        self.memories.clear()
        self._tfidf_cache.clear()
        self._idf_cache.clear()
        self._cache_valid = False
    
    def get_stats(self, **kwargs) -> Dict:
        """获取工作记忆统计信息"""
        user_id = kwargs.get("user_id")
        
        # 过滤用户记忆
        if user_id:
            user_memories = [m for m in self.memories if m.metadata.get("user_id") == user_id]
            count = len(user_memories)
        else:
            count = len(self.memories)
        
        return {
            "count": count,
            "max_capacity": self.max_capacity,
            "max_age_minutes": self.max_age_minutes,
            "cache_valid": self._cache_valid
        }

# 测试示例代码
if __name__ == "__main__":
    
    # 创建配置
    config = MemoryConfig(
        working_memory_capacity=10,  # 最多10条记忆
        working_memory_ttl=5  # 5分钟过期
    )
    
    # 初始化工作记忆
    working_memory = WorkingMemory(config)
    
    # 创建测试记忆项
    
    # 添加一些工作记忆
    memories_data = [
        ("用户询问今天天气如何", 0.8),
        ("用户提到喜欢Python编程", 0.7),
        ("用户说要去北京出差", 0.9),
        ("用户询问推荐附近的餐厅", 0.6),
        ("用户提到对机器学习感兴趣", 0.75),
    ]
    
    print("=== 添加工作记忆 ===")
    for content, importance in memories_data:
        memory = MemoryItem(
            content=content,
            importance=importance,
            memory_type="working",
            timestamp=datetime.now()
        )
        memory_id = working_memory.add(memory)
        print(f"添加记忆: {content[:20]}... (重要性: {importance}) -> ID: {memory_id[:8]} | 时间: {memory.timestamp.strftime('%H:%M:%S')}")
    
    print(f"\n当前记忆数量: {working_memory.get_stats()['count']}")
    
    # 测试检索功能
    print("\n=== 测试检索功能 ===")
    queries = [
        "天气怎么样",
        "编程语言",
        "出差旅行",
        "吃饭推荐",
        "人工智能学习"
    ]
    
    for query in queries:
        print(f"\n查询: '{query}'")
        results = working_memory.retrieve(query, limit=3)
        for i, memory in enumerate(results, 1):
            print(f"  {i}. {memory.content} (重要性: {memory.importance})")
    
    # 测试容量限制和低优先级移除
    print("\n=== 测试容量限制和低优先级移除 ===")
    print(f"最大容量: {working_memory.max_capacity}")
    print(f"当前记忆数量: {working_memory.get_stats()['count']}")
    
    # 显示当前所有记忆
    print("\n当前记忆列表:")
    for i, memory in enumerate(working_memory.memories, 1):
        print(f"  {i}. [{memory.timestamp.strftime('%H:%M:%S')}] {memory.content} (重要性: {memory.importance})")
    
    print("\n添加更多记忆以触发容量清理...")
    
    # 添加不同重要性和时间的记忆
    import time
    additional_memories = [
        ("重要会议记录", 0.95),
        ("临时笔记1", 0.3),
        ("临时笔记2", 0.3),
        ("关键任务提醒", 0.9),
        ("普通消息1", 0.5),
        ("普通消息2", 0.5),
        ("低优先级消息", 0.2),
        ("紧急事项", 0.98),
    ]
    
    for content, importance in additional_memories:
        memory = MemoryItem(
            content=content,
            importance=importance,
            timestamp=datetime.now()
        )
        memory_id = working_memory.add(memory)
        print(f"添加记忆: {content} (重要性: {importance}) -> ID: {memory_id[:8]} | 时间: {memory.timestamp.strftime('%H:%M:%S')}")
        time.sleep(0.1)  # 稍微延迟，产生时间差
    
    print(f"\n添加后记忆数量: {working_memory.get_stats()['count']}")
    
    # 显示最终记忆列表
    print("\n最终记忆列表 (按添加顺序):")
    for i, memory in enumerate(working_memory.memories, 1):
        print(f"  {i}. [{memory.timestamp.strftime('%H:%M:%S')}] {memory.content} (重要性: {memory.importance})")
    
    # 测试清空功能
    print("\n=== 测试清空功能 ===")
    working_memory.clear()
    print(f"清空后记忆数量: {working_memory.get_stats()['count']}")
    print(f"缓存状态: {working_memory.get_stats()['cache_valid']}")
    
    print("\n=== 测试完成 ===")

