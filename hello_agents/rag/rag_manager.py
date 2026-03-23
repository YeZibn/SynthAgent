"""RAG管理器 - 提供完整的RAG管理能力"""
import os
from typing import Dict, Any, List, Optional
from hello_agents.config.rag_config import RAGConfig
from hello_agents.memory.qdrant.qdrant_vector_store import QdrantVectorStore
from qdrant_client.models import PointStruct
from markitdown import MarkItDown


class RAGManager:
    """RAG管理器
    
    提供完整的 RAG 管理能力：
    - 添加多格式文档（PDF、Office等）
    - 智能检索与召回
    - 知识库管理
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        config: Optional[RAGConfig] = None
    ):
        self.user_id = user_id
        self.config = config or RAGConfig()

        os.makedirs(config.knowledge_base_path, exist_ok=True)
        
        # 创建用户特定的目录结构
        self.user_knowledge_base_path = os.path.join(
            self.config.knowledge_base_path,
            f"user_{user_id}"
        )
        os.makedirs(self.user_knowledge_base_path, exist_ok=True)
        os.makedirs(os.path.join(self.user_knowledge_base_path, "documents"), exist_ok=True)
        os.makedirs(os.path.join(self.user_knowledge_base_path, "chunks"), exist_ok=True)
        
        # 使用用户ID作为命名空间的一部分
        self.user_namespace = f"{self.config.rag_namespace}_{user_id}"
        
        self.embedder = self._create_embedding_model()
        self.qdrant_client = QdrantVectorStore(
            config.qdrant_url, 
            config.qdrant_api_key, 
            config.collection_name
        )
        self.markitdown = self._init_markitdown()
        
    
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
    
    def _init_markitdown(self):
        """初始化 MarkItDown 转换器"""
        try:
            return MarkItDown()
        except Exception as e:
            print(f"初始化 MarkItDown 失败: {e}")
            return None
    
    def index_document(self, file_path: str) -> str:
        """索引文档"""
        if not file_path:
            return "❌ 缺少必填参数: file_path"
        
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
        
        try:
            # 复制原始文档到用户目录
            import shutil
            doc_filename = os.path.basename(file_path)
            dest_doc_path = os.path.join(self.user_knowledge_base_path, "documents", doc_filename)
            shutil.copy2(file_path, dest_doc_path)
            print(f"✅ 文档已保存到: {dest_doc_path}")
            
            markdown_text = self._convert_to_markdown(file_path)
            if not markdown_text.strip():
                return f"❌ 文档转换失败或文档为空: {file_path}"
            
            chunks = self._chunk_text(markdown_text)
            
            # 保存分块到用户目录
            self._save_chunks(chunks, doc_filename)
            
            if not self.embedder:
                return "❌ 嵌入模型未初始化，无法索引文档"
            
            if not self.qdrant_client:
                return "❌ Qdrant客户端未初始化，无法索引文档"
            
            self._index_chunks(chunks, dest_doc_path)
            
            return f"✅ 文档索引成功: {file_path}，共生成 {len(chunks)} 个分块"
        except Exception as e:
            return f"❌ 索引文档失败: {str(e)}"
    
    def add_text(self, text: str, source: str = "手动输入") -> str:
        """添加文本"""
        if not text:
            return "❌ 缺少必填参数: text"
        
        try:
            chunks = self._chunk_text(text)
            
            # 保存文本内容和分块到用户目录
            import time
            timestamp = int(time.time())
            text_filename = f"text_{source}_{timestamp}.txt"
            text_path = os.path.join(self.user_knowledge_base_path, "documents", text_filename)
            
            # 保存原始文本
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ 文本已保存到: {text_path}")
            
            # 保存分块
            self._save_chunks(chunks, text_filename)
            
            if not self.embedder:
                return "❌ 嵌入模型未初始化，无法添加文本"
            
            if not self.qdrant_client:
                return "❌ Qdrant客户端未初始化，无法添加文本"
            
            self._index_chunks(chunks, text_path)
            
            return f"✅ 文本添加成功，共生成 {len(chunks)} 个分块"
        except Exception as e:
            return f"❌ 添加文本失败: {str(e)}"
    
    def list_documents(self) -> str:
        """列出文档"""
        try:
            if not self.qdrant_client:
                return "❌ Qdrant客户端未初始化"
            
            result = self.qdrant_client.scroll(
                collection_name=self.config.collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False,
                scroll_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": self.user_id}}
                    ]
                }
            )
            
            points = result[0]
            
            sources = set()
            for point in points:
                if point.payload and "source" in point.payload:
                    sources.add(point.payload["source"])
            
            if not sources:
                return "📭 知识库为空"
            
            return f"📚 知识库包含 {len(sources)} 个文档:\n" + "\n".join(f"- {s}" for s in sorted(sources))
        except Exception as e:
            return f"❌ 列出文档失败: {str(e)}"
    
    def _convert_to_markdown(self, path: str) -> str:
        """将文档转换为Markdown格式"""
        if not os.path.exists(path):
            return ""
        
        ext = os.path.splitext(path)[1].lower()
        
        if ext in ['.txt', '.md', '.json', '.csv', '.xml', '.html']:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"⚠️ 读取文本文件失败: {e}")
                return ""
        
        if self.markitdown:
            try:
                result = self.markitdown.convert(path)
                markdown_text = getattr(result, "text_content", None)
                if isinstance(markdown_text, str) and markdown_text.strip():
                    print(f"✅ MarkItDown转换成功: {path}")
                    return markdown_text
            except Exception as e:
                print(f"⚠️ MarkItDown转换失败: {e}")
        
        return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """将文本分块"""
        paragraphs = self._split_paragraphs(text)
        chunks = []
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para["content"])
            
            if current_size + para_size > chunk_size and current_chunk:
                chunk_text = "\n\n".join(p["content"] for p in current_chunk)
                chunks.append({
                    "content": chunk_text,
                    "heading_path": current_chunk[0].get("heading_path"),
                    "start": current_chunk[0]["start"],
                    "end": current_chunk[-1]["end"]
                })
                
                overlap_paras = current_chunk[-1:] if overlap > 0 else []
                current_chunk = overlap_paras
                current_size = sum(len(p["content"]) for p in overlap_paras)
            
            current_chunk.append(para)
            current_size += para_size
        
        if current_chunk:
            chunk_text = "\n\n".join(p["content"] for p in current_chunk)
            chunks.append({
                "content": chunk_text,
                "heading_path": current_chunk[0].get("heading_path"),
                "start": current_chunk[0]["start"],
                "end": current_chunk[-1]["end"]
            })
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[Dict]:
        """分割段落"""
        lines = text.splitlines()
        paragraphs = []
        current_para = []
        heading_stack = []
        char_pos = 0
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('#'):
                if current_para:
                    content = "\n".join(current_para).strip()
                    if content:
                        paragraphs.append({
                            "content": content,
                            "heading_path": " > ".join(heading_stack) if heading_stack else None,
                            "start": char_pos - len(content),
                            "end": char_pos
                        })
                    current_para = []
                
                level = len(stripped) - len(stripped.lstrip('#'))
                title = stripped.lstrip('#').strip()
                
                if level <= len(heading_stack):
                    heading_stack = heading_stack[:level-1]
                heading_stack.append(title)
            else:
                if stripped:
                    current_para.append(line)
                elif current_para:
                    content = "\n".join(current_para).strip()
                    if content:
                        paragraphs.append({
                            "content": content,
                            "heading_path": " > ".join(heading_stack) if heading_stack else None,
                            "start": char_pos - len(content),
                            "end": char_pos
                        })
                    current_para = []
            
            char_pos += len(line) + 1
        
        if current_para:
            content = "\n".join(current_para).strip()
            if content:
                paragraphs.append({
                    "content": content,
                    "heading_path": " > ".join(heading_stack) if heading_stack else None,
                    "start": char_pos - len(content),
                    "end": char_pos
                })
        
        return paragraphs if paragraphs else [{"content": text, "heading_path": None, "start": 0, "end": len(text)}]
    
    def _save_chunks(self, chunks: List[Dict], doc_filename: str):
        """保存分块到用户目录"""
        import json
        chunk_filename = f"{os.path.splitext(doc_filename)[0]}_chunks.json"
        chunk_path = os.path.join(self.user_knowledge_base_path, "chunks", chunk_filename)
        
        # 保存分块信息
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 分块已保存到: {chunk_path}")
    
    def _index_chunks(self, chunks: List[Dict], source: str):
        """索引文本块"""
        if not self.embedder or not self.qdrant_client:
            return
        
        points = []
        for idx, chunk in enumerate(chunks):
            vector = self.embedder.encode(chunk["content"]).tolist()
            
            metadata = {
                    "content": chunk["content"],
                    "source": source,
                    "namespace": self.user_namespace,
                    "user_id": self.user_id,
                    "heading_path": chunk.get("heading_path"),
                    "start": chunk.get("start"),
                    "end": chunk.get("end")
                }
        
            points.append({"memory_id": f"{self.user_namespace}_{source}_{idx}","vector":vector,"metadata":metadata})
        
        self.qdrant_client.add_batch([p["memory_id"] for p in points], [p["vector"] for p in points], [p["metadata"] for p in points])
        
        print(f"✅ 索引了 {len(points)} 个文本块")
