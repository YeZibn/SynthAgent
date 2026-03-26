from synth_agent.tool.tool import Tool, ToolParameter
from typing import List
from synth_agent.tool.mcp_tool.mcp_tool import MCPTool


class JimengTool(MCPTool):
    """即梦 AI 图片生成工具"""
    def __init__(self):
        super().__init__(
            name="jimeng_ai",
            mcp_url="http://127.0.0.1:9000",
            tool_name="generate_image_async",
            description="使用即梦 AI 3.1 生成图片"
        )

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数"""
        return [
            ToolParameter(
                name="prompt",
                type="string",
                description="图片生成提示词",
                required=True
            ),
            ToolParameter(
                name="width",
                type="integer",
                description="图片宽度",
                default=1024,
                required=False
            ),
            ToolParameter(
                name="height",
                type="integer",
                description="图片高度",
                default=1024,
                required=False
            ),
            ToolParameter(
                name="seed",
                type="integer",
                description="随机种子，-1 表示随机",
                default=-1,
                required=False
            )
        ]

    def _process_response(self, result):
        """处理图片生成响应"""
        if isinstance(result, dict):
            if "success" in result:
                if result.get("success"):
                    image_urls = result.get("image_urls", [])
                    if image_urls:
                        return f"成功生成图片：\n" + "\n".join(image_urls)
                    else:
                        return f"成功: {result.get('message', '操作成功')}"
                else:
                    error = result.get("error", "未知错误")
                    return f"失败：{error}"
            else:
                return f"MCP 服务返回: {result}"
        else:
            return f"MCP 服务返回格式错误: {result}"
