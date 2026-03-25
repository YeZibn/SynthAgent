import requests
import json
from typing import List, Union, Dict, Optional
import time

class QwenEmbedder:
    """
    硅基流动 Qwen/Qwen3-Embedding-8B 模型的 API 封装类
    """
    def __init__(
        self,
        api_key: str = "sk-qqvwbybttiknbxvsxqujxrhmvlvdsaeqcmqtxetdiguimzym",
        api_url: str = "https://api.siliconflow.cn/v1/embeddings",
        model_name: str = "Qwen/Qwen3-Embedding-8B",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        初始化配置
        :param api_key: 硅基流动平台的 API Key（必填）
        :param api_url: 硅基流动 Embedding API 地址（默认即可）
        :param model_name: 模型名称（固定为 Qwen/Qwen3-Embedding-8B）
        :param timeout: API 调用超时时间（秒）
        :param max_retries: 失败重试次数
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 请求头配置
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> Union[List[float], List[List[float]]]:
        """
        文本编码生成向量
        :param texts: 单个文本字符串 或 文本列表
        :param normalize: 是否对向量进行归一化（默认 True，推荐开启）
        :param batch_size: 批量编码时的批次大小（避免单次请求文本过多）
        :return: 单个向量（输入单文本）或向量列表（输入多文本）
        """
        # 统一格式：将单文本转为列表
        is_single = False
        if isinstance(texts, str):
            is_single = True
            texts = [texts]
        
        all_embeddings = []
        # 分批处理文本，避免单次请求过长
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            embeddings = self._request_embedding(batch_texts, normalize)
            all_embeddings.extend(embeddings)
        
        # 如果是单文本输入，返回单个向量；否则返回向量列表
        return all_embeddings[0] if is_single else all_embeddings

    def _request_embedding(
        self,
        texts: List[str],
        normalize: bool
    ) -> List[List[float]]:
        """
        内部方法：发送 API 请求获取向量
        """
        # 构造请求体
        payload = {
            "model": self.model_name,
            "dimensions": 512,
            "input": texts,
            "encoding_format": "float",  # 向量格式：float（默认）或 base64
            "normalize": normalize      # 是否归一化向量
        }

        # 重试机制
        for retry in range(self.max_retries):
            try:
                # 发送 POST 请求
                response = requests.post(
                    url=self.api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=self.timeout
                )
                # 检查 HTTP 状态码
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                # 提取向量（按返回顺序）
                embeddings = [item["embedding"] for item in result["data"]]
                return embeddings
            
            except requests.exceptions.HTTPError as e:
                # HTTP 错误（如 401 密钥错误、429 限流）
                error_msg = f"HTTP 错误 {response.status_code}: {response.text}"
                if retry == self.max_retries - 1:
                    raise Exception(f"API 调用失败：{error_msg}") from e
                time.sleep(1 * (retry + 1))  # 指数退避重试
            except requests.exceptions.Timeout:
                # 超时错误
                if retry == self.max_retries - 1:
                    raise Exception("API 调用超时")
                time.sleep(1 * (retry + 1))
            except Exception as e:
                # 其他未知错误
                if retry == self.max_retries - 1:
                    raise Exception(f"向量生成失败：{str(e)}") from e
                time.sleep(1 * (retry + 1))
        
        raise Exception("达到最大重试次数，向量生成失败")

# ------------------------------
# 使用示例
# ------------------------------
if __name__ == "__main__":

    
    # 初始化嵌入模型客户端
    embedder = QwenEmbedder()    
    
    # 1. 单文本编码
    single_text = "超过退换货期限的（具体期限见本手册2.1条）"
    single_embedding = embedder.encode(single_text)
    print(f"单文本向量长度：{len(single_embedding)}")
    print(f"向量前5个值：{single_embedding[:5]}")
    
    # 2. 多文本编码
    multi_texts = [
        "退货：买家签收商品后7天内可申请无理由退货",
        "换货：买家签收商品后15天内，商品有质量问题可申请换货"
    ]
    multi_embeddings = embedder.encode(multi_texts)
    print(f"\n多文本向量数量：{len(multi_embeddings)}")
    print(f"第一个多文本向量长度：{len(multi_embeddings[0])}")