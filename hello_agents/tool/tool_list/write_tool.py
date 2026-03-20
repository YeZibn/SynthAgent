from hello_agents.tool.tool import Tool, ToolParameter
from typing import Dict, Any, List

# 定义Write工具
class WriteTool(Tool):
    def __init__(self):
        super().__init__(name="write", description="写入文件内容")
    
    def run(self, parameters: Dict[str, Any]) -> str:
        file_path = parameters.get("file_path", "")
        content = parameters.get("content", "")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件写入成功: {file_path}"
        except Exception as e:
            return f"写入文件时出错: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="file_path", type="string", description="要写入的文件路径", required=True),
            ToolParameter(name="content", type="string", description="要写入的内容", required=True)
        ]