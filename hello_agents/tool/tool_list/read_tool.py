from hello_agents.tool.tool import Tool, ToolParameter
from typing import Dict, Any, List

# 定义Read工具
class ReadTool(Tool):
    def __init__(self):
        super().__init__(name="read", description="读取文件内容")
    
    def run(self, parameters: Dict[str, Any]) -> str:
        file_path = parameters.get("file_path", "")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"文件内容:\n{content}"
        except Exception as e:
            return f"读取文件时出错: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="file_path", type="string", description="要读取的文件路径", required=True)
        ]