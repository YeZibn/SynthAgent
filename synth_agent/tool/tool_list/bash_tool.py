from synth_agent.tool.tool import Tool, ToolParameter
from typing import Dict, Any, List

# 定义Bash工具
class BashTool(Tool):
    def __init__(self):
        super().__init__(name="bash", description="执行bash命令")
    
    def run(self, parameters: Dict[str, Any]) -> str:
        import subprocess
        command = parameters.get("command", "")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"命令执行结果:\n标准输出:\n{result.stdout}\n标准错误:\n{result.stderr}\n返回码: {result.returncode}"
        except Exception as e:
            return f"执行命令时出错: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="command", type="string", description="要执行的bash命令", required=True)
        ]
