import urllib
import uuid
from typing import Dict, Any, List
import httpx
import logging
import json
import os
import time
import hmac
import hashlib
import base64
from datetime import datetime
from fastmcp import FastMCP
from dotenv import load_dotenv


load_dotenv()

# ====================== 配置 ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jimeng-ai-mcp-server")


# 火山引擎配置
VOLCENGINE_ACCESS_KEY = os.environ.get("VOLCENGINE_ACCESS_KEY")
VOLCENGINE_SECRET_KEY = os.environ.get("VOLCENGINE_SECRET_KEY")
API_ENDPOINT = "https://visual.volcengineapi.com"

# 统一 MCP 实例
mcp = FastMCP(
    name="JimengAIServer",
    instructions="这个服务用来通过即梦 AI 3.1 生成图片。\n"
                 "调用 generate_image_async 生成图片，返回图片 URL"
)

# ====================== 火山引擎签名认证 ======================
def generate_signature(method, uri, headers, body):
    """生成火山引擎 API 签名"""
    # 构建规范化请求字符串
    canonical_request = f"{method}\n{uri}\n\n"
    
    # 添加头部参数
    signed_headers = ["host", "x-date"]
    for header in sorted(signed_headers):
        canonical_request += f"{header}:{headers[header]}\n"
    canonical_request += "\n"
    canonical_request += ",".join(signed_headers)
    canonical_request += "\n"
    
    # 添加请求体哈希
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    canonical_request += body_hash
    
    # 构建签名字符串
    date = headers["X-Date"]
    credential_scope = f"{date[:8]}/cn-north-1/cv/request"
    string_to_sign = f"HMAC-SHA256\n{date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    # 计算签名
    signing_key = hmac.new(
        f"{VOLCENGINE_SECRET_KEY}".encode(),
        f"{date[:8]}/cn-north-1/cv/request".encode(),
        hashlib.sha256
    ).digest()
    
    signature = hmac.new(
        signing_key,
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# ====================== 提交任务到即梦 AI ======================
def submit_task(prompt: str, width: int = 1024, height: int = 1024, seed: int = -1) -> Dict[str, Any]:
    """提交文生图任务"""
    method = "POST"
    uri = "/?Action=CVSync2AsyncSubmitTask&Version=2022-08-31"
    
    # 构建请求体
    body = {
        "req_key": "jimeng_t2i_v31",
        "prompt": prompt,
        "seed": seed,
        "width": width,
        "height": height,
        "use_pre_llm": True
    }
    
    # 构建头部
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    headers = {
        "Host": "visual.volcengineapi.com",
        "X-Date": now,
        "Content-Type": "application/json",
        "X-Security-Token": ""
    }
    
    # 生成签名
    body_str = json.dumps(body, ensure_ascii=False)
    signature = generate_signature(method, uri, headers, body_str)
    
    # 添加 Authorization 头部
    credential = f"{VOLCENGINE_ACCESS_KEY}/{now[:8]}/cn-north-1/cv"
    headers["Authorization"] = f"HMAC-SHA256 Credential={credential}, SignedHeaders=host;x-date, Signature={signature}"
    
    try:
        response = httpx.post(
            f"{API_ENDPOINT}{uri}",
            json=body,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 10000:
                return result.get("data", {})
            else:
                raise RuntimeError(f"API 错误: {result.get('message', 'Unknown error')}")
        else:
            raise RuntimeError(f"请求失败: {response.status_code} {response.text}")
    except Exception as e:
        raise RuntimeError(f"提交任务失败: {str(e)}")

# ====================== 查询任务状态 ======================
def query_task(task_id: str) -> Dict[str, Any]:
    """查询任务状态"""
    method = "POST"
    uri = "/?Action=CVSync2AsyncGetResult&Version=2022-08-31"
    
    # 构建请求体
    body = {
        "req_key": "jimeng_t2i_v31",
        "task_id": task_id,
        "req_json": json.dumps({"return_url": True})
    }
    
    # 构建头部
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    headers = {
        "Host": "visual.volcengineapi.com",
        "X-Date": now,
        "Content-Type": "application/json",
        "X-Security-Token": ""
    }
    
    # 生成签名
    body_str = json.dumps(body, ensure_ascii=False)
    signature = generate_signature(method, uri, headers, body_str)
    
    # 添加 Authorization 头部
    credential = f"{VOLCENGINE_ACCESS_KEY}/{now[:8]}/cn-north-1/cv"
    headers["Authorization"] = f"HMAC-SHA256 Credential={credential}, SignedHeaders=host;x-date, Signature={signature}"
    
    try:
        response = httpx.post(
            f"{API_ENDPOINT}{uri}",
            json=body,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 10000:
                return result.get("data", {})
            else:
                raise RuntimeError(f"API 错误: {result.get('message', 'Unknown error')}")
        else:
            raise RuntimeError(f"请求失败: {response.status_code} {response.text}")
    except Exception as e:
        raise RuntimeError(f"查询任务失败: {str(e)}")

# ====================== 生成图片并等待完成 ======================
def generate_image(prompt: str, width: int = 1024, height: int = 1024, seed: int = -1) -> List[str]:
    """生成图片并返回 URL 列表"""
    # 提交任务
    task_data = submit_task(prompt, width, height, seed)
    task_id = task_data.get("task_id")
    
    if not task_id:
        raise RuntimeError("未获取到 task_id")
    
    # 轮询查询状态
    max_retries = 60  # 最多轮询 60 次
    retry_interval = 2  # 每 2 秒查询一次
    
    for i in range(max_retries):
        time.sleep(retry_interval)
        result = query_task(task_id)
        status = result.get("status")
        
        if status == "done":
            image_urls = result.get("image_urls", [])
            if image_urls:
                return image_urls
            else:
                raise RuntimeError("生成失败: 未返回图片 URL")
        elif status in ["in_queue", "generating"]:
            logger.info(f"生成中... ({i+1}/{max_retries})")
        else:
            raise RuntimeError(f"任务失败: status={status}")
    
    raise RuntimeError("生成超时")

# ====================== MCP 工具：生成图片 ======================
@mcp.tool()
def generate_image_async(
    prompt: str = "a cute cat wearing a yellow hat",
    width: int = 1024,
    height: int = 1024,
    seed: int = -1
) -> Dict[str, Any]:
    """使用即梦 AI 3.1 生成图片"""
    try:
        image_urls = generate_image(prompt, width, height, seed)
        return {
            "success": True,
            "image_urls": image_urls,
            "prompt": prompt
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ====================== 启动 MCP 服务 ======================
if __name__ == "__main__":
    logger.info("✅ 即梦 AI 3.1 MCP 服务启动：http://127.0.0.1:9000")
    mcp.run(transport="http", host="127.0.0.1", port=9000)