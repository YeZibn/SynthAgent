from typing import Optional, List, Tuple, Dict, Any
from hello_agents.agent.agent import Agent
from hello_agents.llm.HelloAgentsLLM import HelloAgentsLLM
from hello_agents.config.config import Config
from hello_agents.tool.tool_registry import ToolRegistry
from hello_agents.tool.tool import Tool, ToolParameter
import re
from hello_agents.tool.tool_list.bash_tool import BashTool
from hello_agents.tool.tool_list.write_tool import WriteTool
from hello_agents.tool.tool_list.read_tool import ReadTool

# ReAct Agent 提示模板
MY_REACT_PROMPT = """
你是一个具备推理和行动能力的AI助手。你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。 
 
 ## 可用工具 
 {tools_info} 
 
 ## 工作流程 
 请严格按照以下格式进行回应，**每次只能输出以下格式中的一种，绝对不能同时输出两种**:
 
 ### 格式1: 只输出思考
 ```
Thought: 分析当前问题，思考需要什么信息或采取什么行动。
```

### 格式2: 只输出行动
 ```
Action: 如果思考给出了行动，就到工具中选择一个合适的工具去执行，格式必须是以下之一:
- {{tool_name}}[参数1=值1, 参数2=值2] - 调用指定工具，严格按照工具定义的参数名称和类型填写
- Finish[最终答案] - 当你有足够信息给出最终答案时
```

**工具调用示例:**
- bash[command=ls -la] - 执行bash命令
- read[file_path=/path/to/file.txt] - 读取文件内容
- write[file_path=/path/to/file.txt, content=Hello World] - 写入文件内容

## 重要提醒
**必须严格遵守以下规则，否则你的回答将被视为无效:**
1. **每次回应只能包含Thought或Action中的一个，绝对不能同时包含两个**
2. **必须使用指定的格式**，包括正确的缩进和标记
3. **工具调用的格式必须严格遵循:工具名[参数名1=值1, 参数名2=值2]**
4. **参数名称必须与工具定义完全一致，参数值要符合参数类型要求**
5. **只有当你确信有足够信息回答问题时，才使用Finish**
6. **如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数**

## 当前任务
**Question:** {task}

## 执行历史
{history}

现在开始你的推理和行动，**只输出一种格式**:
"""

class ReActAgent(Agent):
    """
    重写的ReAct Agent - 推理与行动结合的智能体
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 100,
        custom_prompt: Optional[str] = None
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.prompt_template = custom_prompt if custom_prompt else MY_REACT_PROMPT
        print(f"✅ {name} 初始化完成，最大步数: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        """
        运行ReAct Agent
        """
        self.current_history = []
        current_step = 0

        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            # 1. 构建提示词
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools_info=tools_desc,
                task=input_text,
                history=history_str
            )

            # 2. 调用LLM
            messages = [
                {"role": "system", "content": self.system_prompt or "你是一个智能助手，能够通过推理和使用工具来解决问题。"},
                {"role": "user", "content": prompt}
            ]
            response_text = self.llm.think(messages, temperature=self.config.temperature)
            if not response_text:
                return "抱歉，我无法处理这个请求。"

            # 3. 解析输出
            thought, action, action_input, is_finish = self._parse_response(response_text)

            # 4. 处理思考
            if thought:
                print(f"🧠 思考: {thought}")
                self.current_history.append(f"Thought: {thought}")
                # 如果只有思考，继续下一轮循环
                continue

            # 5. 检查完成条件
            if action and is_finish:
                final_answer = action_input
                self.current_history.append(f"Action: Finish[{final_answer}]")
                print(f"📝 最终回答: {final_answer}")
                return final_answer

            # 6. 执行工具调用
            if action:
                # 执行行动
                print(f"📝 行动: `{action}[{action_input}]`")
                observation = self.tool_registry.execute_tool(action, action_input)
                print(f"👁️  观察: {observation}")
                self.current_history.append(f"Action: `{action}[{action_input}]`")
                self.current_history.append(f"Observation: {observation}")

        # 达到最大步数
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        self.current_history.append(f"Action: Finish[{final_answer}]")
        return final_answer
    
    def _get_tools_info(self) -> str:
        """
        获取工具信息
        """
        tools_info = []
        for tool in self.tool_registry.get_tool_list():
            params = tool.get_parameters()
            param_str = ", ".join([f"{p.name}: {p.type}" for p in params])
            tools_info.append(f"- {tool.name}: {tool.description} (参数: {param_str})")
        
        return "\n".join(tools_info) if tools_info else "暂无可用工具"
    
    def _parse_response(self, response: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bool]]:
        """
        解析LLM响应
        返回: (思考, 工具名称, 工具输入, 是否为Finish)
        """
        # 提取思考
        thought_match = re.search(r'Thought: (.*?)(?:\n|$)', response)
        thought = thought_match.group(1).strip() if thought_match else None

        if thought:
            print(f"这个Thought: {thought}")
        
        # 提取行动
        # 检查是否为Finish
        finish_match = re.search(r'Action: Finish\[(.*?)\]', response)
        if finish_match:
            return None, "Finish", finish_match.group(1).strip(), True
        
        # 检查是否为工具调用
        action_match = re.search(r'Action: (\w+)\[(.*?)\]', response)
        if action_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2).strip()
            print(f"Action: {action}{action_input}")
            return None, action, action_input, False
        
        # 如果只返回了思考
        if thought:
            return thought, None, None, False
        
        return None, None, None, False
    


if __name__ == "__main__":
    # 初始化LLM
    llm = HelloAgentsLLM()
    # 初始化工具注册表
    tool_registry = ToolRegistry()

    # 注册工具
    bash_tool = BashTool()
    read_tool = ReadTool()
    write_tool = WriteTool()
    
    tool_registry.register_tool(bash_tool)
    tool_registry.register_tool(read_tool)
    tool_registry.register_tool(write_tool)
    
    # 初始化Agent
    agent = ReActAgent(name="HelloAgent", llm=llm, tool_registry=tool_registry, config=Config())
    agent.run("请帮我看一下当前项目的结构")