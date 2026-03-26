# SynthAgent

一个基于 Python 的智能代理框架，支持多角色任务规划、ReAct 推理模式和记忆管理能力。

## 项目概览

SynthAgent 是一个功能强大的智能代理开发框架，核心特色是**任务规划与执行系统 (PlanFlow)**，能够将复杂目标分解为可执行的子任务，并根据角色分配和依赖关系调度执行。

### 核心特性

- **PlanFlow 任务规划系统**：自动分解任务、智能调度执行
- **多角色 Agent**：支持 Researcher、Coder、Analyst、Writer、Manager 等专业角色
- **ReAct 推理模式**：结合推理与行动，实现更智能的决策过程
- **多层记忆架构**：工作记忆、情景记忆、语义记忆
- **RAG 增强能力**：文档检索和知识增强
- **可扩展工具系统**：内置多种工具，支持自定义工具注册

## 项目结构

```
SynthAgent/
├── synth_agent/                    # 主包
│   ├── __init__.py                 # 包初始化
│   ├── agent/                      # Agent 相关
│   │   ├── agent.py               # Agent 基类
│   │   ├── react_agent.py         # ReAct Agent 实现
│   │   └── multi_agent/           # 多 Agent 系统
│   │       ├── agent_team.py      # Agent 团队
│   │       ├── communication_bus.py  # 通信总线
│   │       └── shared_memory.py   # 共享内存
│   ├── flow/                      # 任务流程系统 ⭐
│   │   ├── plan_flow.py           # 任务规划与执行主流程
│   │   ├── planner.py             # 任务分解器
│   │   ├── scheduler.py           # 任务调度器
│   │   ├── role.py                # 角色定义
│   │   ├── task.py                # 任务模型
│   │   └── task_persistence.py    # 任务持久化
│   ├── llm/                       # LLM 相关
│   │   └── synth_LLM.py           # Synth LLM
│   ├── memory/                    # 记忆系统
│   │   ├── memory_tool.py         # 记忆工具
│   │   └── memory_list/           # 记忆实现
│   │       ├── episodic_memory.py    # 情景记忆
│   │       ├── semantic_memory.py    # 语义记忆
│   │       └── working_memory.py     # 工作记忆
│   ├── rag/                       # RAG 系统
│   │   ├── rag_tool.py           # RAG 工具
│   │   └── rag_manager.py        # RAG 管理器
│   ├── tool/                      # 工具系统
│   │   ├── tool_registry.py       # 工具注册表
│   │   └── tool_list/             # 内置工具
│   │       ├── bash_tool.py       # Bash 命令
│   │       ├── read_tool.py       # 读取文件
│   │       ├── write_tool.py      # 写入文件
│   │       └── web/                # Web 工具
│   │           ├── baidu_search_tool.py
│   │           └── url_search_tool.py
│   └── config/                    # 配置
├── task/                          # 任务数据存储
│   └── plan_*/                    # 任务计划目录
├── tests/                         # 测试
└── requirements.txt               # 依赖
```

## 核心功能

### 1. PlanFlow 任务规划系统 ⭐

PlanFlow 是本框架的核心特性，能够将复杂目标自动分解为可执行的子任务，并根据角色和依赖关系调度执行。

**工作流程**：

```
用户目标 → 任务分解 → 角色分配 → 依赖分析 → 任务调度 → 结果汇总
```

**使用示例**：

```python
from synth_agent.llm.synth_LLM import SynthLLM
from synth_agent.tool.tool_registry import ToolRegistry
from synth_agent.flow.plan_flow import PlanFlow

# 初始化 LLM
llm = SynthLLM(model="your-model")

# 初始化工具注册表
registry = ToolRegistry()

# 创建任务流程
flow = PlanFlow(
    llm=llm,
    tool_registry=registry,
    max_tasks=10,
    max_concurrent=5
)

# 执行任务
result = flow.run("帮我调研一下最新的 AI 发展趋势，并输出一份报告")
```

**任务持久化**：
- 自动保存任务计划到 `task/` 目录
- 支持恢复和重新执行任务
- 记录任务执行状态和结果

### 2. 多角色 Agent 系统

框架内置多种专业角色，每个角色有独立的系统提示和专业工具：

| 角色 | 描述 | 擅长领域 |
|------|------|----------|
| Researcher | 研究员 | 信息搜集、网络搜索、数据分析 |
| Coder | 程序员 | 代码编写、调试、技术实现 |
| Analyst | 分析师 | 数据分析、图表生成、洞察提炼 |
| Writer | 作家 | 内容撰写、文案编辑、文档整理 |
| Manager | 经理 | 任务协调、结果汇总、决策建议 |

**角色使用**：

```python
from synth_agent.flow.role import RoleType
from synth_agent.agent.react_agent import ReActAgent
from synth_agent.flow.task import Task

# 为任务分配角色
task = Task(
    task_id="task_1",
    description="搜索最新 AI 新闻",
    role=RoleType.RESEARCHER,
    depends_on=[]
)
```

### 3. ReAct Agent

基于 ReAct（Reasoning + Acting）模式的智能代理，支持：
- LLM 原生 tool_calls 功能
- 工具链自动选择
- 多轮推理
- 记忆和 RAG 增强

```python
from synth_agent.agent.react_agent import ReActAgent

agent = ReActAgent(
    name="助手",
    llm=llm,
    tool_registry=tool_registry,
    max_steps=10
)

result = agent.run("帮我查一下今天天气怎么样")
```

### 4. 工具系统

**内置工具**：
- `bash`: 执行 Shell 命令
- `read`: 读取文件内容
- `write`: 写入文件内容
- `baidu_search`: 百度搜索
- `url_search`: URL 网页抓取
- `memory`: 记忆存取
- `rag`: 文档检索

**自定义工具**：

```python
from synth_agent.tool.tool import Tool, ToolResult
from synth_agent.tool.tool_registry import ToolRegistry

class MyTool(Tool):
    name = "my_tool"
    description = "我的自定义工具"
    
    def run(self, **params) -> ToolResult:
        # 实现逻辑
        return ToolResult(success=True, data={"result": "ok"})

registry = ToolRegistry()
registry.register_tool(MyTool())
```

### 5. 记忆系统

三层记忆架构：

| 记忆类型 | 描述 | 存储 |
|----------|------|------|
| Working Memory | 短期记忆，有容量限制 | SQLite |
| Episodic Memory | 按会话存储的经历 | SQLite |
| Semantic Memory | 知识图谱，实体关系 | Neo4j + Qdrant |

**使用记忆工具**：

```python
from synth_agent.memory.memory_tool import MemoryTool

memory = MemoryTool(user_id="user_001")

# 存储记忆
memory.run({
    "action": "store",
    "content": "用户喜欢川菜",
    "memory_type": "semantic",
    "importance": 0.8
})

# 检索记忆
results = memory.run({
    "action": "retrieve",
    "query": "用户口味偏好"
})
```

### 6. MCP 集成

**MCP (Model Context Protocol)** 是一种标准化的 LLM 通信协议，用于 LLM 与外部系统/服务交互。本项目已集成 MCP 支持：

**MCP 服务**：
- `synth_agent/mcp/comfyImage_mcp_server.py` - 即梦 AI 3.1 MCP 服务
- 支持文生图功能
- 基于火山引擎 API

**使用示例**：

```python
from synth_agent.tool.tool_registry import ToolRegistry

# 注册 MCP 工具
registry = ToolRegistry()
registry.register_mcp_tools("http://localhost:9000")

# 执行 MCP 工具
result = registry.execute_tool("generate_image_async", {
    "prompt": "a beautiful landscape with mountains and lake",
    "width": 1024,
    "height": 1024
})
```

**MCP 服务启动**：

```bash
# 启动即梦 AI 3.1 MCP 服务
python synth_agent/mcp/comfyImage_mcp_server.py
```

**配置**：
- 在 `.env` 文件中设置火山引擎 API 密钥：
  ```
  VOLCENGINE_ACCESS_KEY=your-access-key
  VOLCENGINE_SECRET_KEY=your-secret-key
  ```

**注意**：
- 需要在火山引擎控制台申请即梦 AI 3.1 API 访问权限
- 生成的图片 URL 有效期为 24 小时

## 安装指南

### 环境要求
- Python 3.10+
- Neo4j（图数据库，用于语义记忆）
- Qdrant（向量数据库，用于语义检索）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制 `.env.example` 为 `.env` 并填写配置
2. 确保 Neo4j 和 Qdrant 服务已启动

### 快速开始

```bash
# 运行示例
python synth_agent/flow/test_flow.py
```

## 任务数据

任务计划和数据保存在 `task/` 目录：

```
task/
└── plan_20260326_005134_f77851/
    ├── plan.json              # 任务计划
    ├── dependency_graph.json  # 依赖图
    ├── summary.json            # 执行摘要
    └── task_*_status.json      # 任务状态
```

## 依赖

主要依赖：
- `pydantic`: 数据模型
- `python-dotenv`: 环境变量
- `qdrant-client`: Qdrant 向量数据库
- `neo4j`: Neo4j 图数据库
- `langchain`: LLM 工具链
- `fastmcp`: MCP 服务框架
- `httpx`: HTTP 客户端
- `websockets`: WebSocket 支持
- `Pillow`: 图像处理

详见 `requirements.txt`

## 许可证

MIT License
