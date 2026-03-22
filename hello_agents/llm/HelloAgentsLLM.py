import os
import requests
import json
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class HelloAgentsLLM:
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, timeout: int = None, tools: List[Dict[str, str]] = None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))
        self.tools = tools or []

        if not self.model or not self.api_key or not self.base_url:
            raise ValueError("请配置 LLM_MODEL_ID / LLM_API_KEY / LLM_BASE_URL")

        self.url = f"{self.base_url.rstrip('/')}/chat/completions"

    def think(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> Optional[Dict]:
        print(f"🧠 调用模型: {self.model}")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "enable_thinking": True,
            "using_tools": "auto",
            "max_tokens": 1024,
            "tools": self.tools
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        all_raw_chunks = []
        full_reasoning = []
        full_content = []

        try:
            with requests.post(self.url, json=payload, headers=headers, stream=True, timeout=self.timeout) as resp:
                resp.raise_for_status()

                for line in resp.iter_lines():
                    if not line:
                        continue

                    s = line.decode("utf-8").strip()
                    if s.startswith("data: "):
                        s = s[6:]
                    if s == "[DONE]":
                        break

                    try:
                        data = json.loads(s)
                        all_raw_chunks.append(data)

                        # 安全提取内容
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})

                        r = delta.get("reasoning_content")
                        if r:
                            full_reasoning.append(r)

                        c = delta.get("content")
                        if c:
                            full_content.append(c)

                    except json.JSONDecodeError:
                        continue

            # 最终返回完整结构
            return {
                "model": self.model,
                "raw_chunks": all_raw_chunks,          # 所有原始 chunk（含 tool_calls）
                "full_reasoning": "".join(full_reasoning),
                "full_content": "".join(full_content)
            }

        except Exception as e:
            print(f"❌ 调用失败: {e}")
            return None


if __name__ == '__main__':
    llm = HelloAgentsLLM()

    messages = [
        {"role": "system", "content": "你是一个智能助手，可以调用工具"},
        {"role": "user", "content": "你是谁"}
    ]

    res = llm.think(messages)

    if res:
        # 打印最后的 chunk，你就能看到 tool_calls 了
        print(json.dumps(res["raw_chunks"][-1]))

        print("\n" + "="*50)
        print("🧠 思考过程：")
        print(res["full_reasoning"])

        print("\n" + "="*50)
        print("📝 回复内容：")
        print(res["full_content"])