import asyncio
from typing import Dict, Any, List, Optional
from synth_agent.tool.tool import Tool, ToolParameter


class MCPTool(Tool):
    """
    使用 fastmcp 客户端连接 MCP 服务
    """
    _loop: Optional[asyncio.AbstractEventLoop] = None

    def __init__(self, name: str, mcp_url: str, tool_name: str, description: str):
        super().__init__(name, description)
        self.mcp_url = mcp_url.rstrip('/')
        self.tool_name = tool_name
        self.mcp_endpoint = f"{self.mcp_url}/mcp"

    def get_parameters(self) -> List[ToolParameter]:
        return []

    def run(self, params: Dict[str, Any]) -> str:
        """同步调用 MCP 工具"""
        try:
            # 确保有事件循环
            if MCPTool._loop is None:
                MCPTool._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(MCPTool._loop)

            return MCPTool._loop.run_until_complete(self._async_run(params))

        except Exception as e:
            return f"调用失败: {str(e)}"

    async def _async_run(self, params: Dict[str, Any]) -> str:
        """异步调用 MCP 工具"""
        try:
            from fastmcp.client import Client

            async with Client(self.mcp_endpoint) as client:
                result = await client.call_tool(self.tool_name, params)
                return self._process_result(result)

        except Exception as e:
            return f"调用失败: {str(e)}"

    def _process_result(self, result: Any) -> str:
        """处理工具执行结果"""
        if isinstance(result, dict):
            if "success" in result:
                if result.get("success"):
                    return f"成功: {result.get('message', '操作成功')}"
                else:
                    error = result.get("error", "未知错误")
                    return f"失败：{error}"
            else:
                return f"MCP 服务返回: {result}"
        else:
            return f"MCP 服务返回: {result}"
