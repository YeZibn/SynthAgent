# Multi-Agent 多智能体系统

Hello Agents Python 的多智能体系统提供了强大的智能体协作能力，支持多种协作模式和复杂的任务协调。

## 🏗️ 系统架构

### 核心组件

```
Multi-Agent 系统
├── MultiAgentSystem (统一入口)
│   ├── 整合 AgentOrchestrator
│   ├── 整合 AgentTeam  
│   └── 共享 CommunicationBus 和 SharedMemory
├── AgentOrchestrator (编排器)
│   ├── 任务分解与分配
│   ├── 结果聚合
│   └── 历史记录管理
├── AgentTeam (智能体团队)
│   ├── 多种协作模式
│   ├── 团队记忆共享
│   └── 通信机制
├── CommunicationBus (通信总线)
│   ├── 消息发布/订阅
│   ├── 直接消息传递
│   └── 广播机制
└── SharedMemory (共享记忆)
    ├── 知识存储与检索
    ├── 任务上下文管理
    └── 对话历史记录
```

### 架构图

![Multi-Agent系统架构图](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Multi-Agent%20system%20architecture%20diagram%20showing%20MultiAgentSystem%20integrating%20AgentOrchestrator%2C%20AgentTeam%2C%20CommunicationBus%2C%20and%20SharedMemory%2C%20professional%20software%20diagram%2C%20color-coded%2C%20modern%20design&image_size=landscape_16_9)

## 🚀 快速开始

### 1. 使用 MultiAgentSystem（推荐方式）

```python
from hello_agents.agent.react_agent import ReActAgent
from hello_agents.llm.HelloAgentsLLM import HelloAgentsLLM
from hello_agents.tool.tool_registry import ToolRegistry
from hello_agents.agent.multi_agent.multi_agent_system import MultiAgentSystem

# 初始化
llm = HelloAgentsLLM()
registry = ToolRegistry()

# 创建统一的多智能体系统
system = MultiAgentSystem("我的智能团队", llm)

# 设置为混合模式（同时支持编排器和团队）
system.setup_as_hybrid(
    orchestrator_name="主编排器",
    team_name="执行团队",
    collaboration_mode="hierarchical"
)

# 创建并注册 Agent
tech_agent = ReActAgent("技术专家", llm, registry)
sales_agent = ReActAgent("销售顾问", llm, registry)
support_agent = ReActAgent("客服代表", llm, registry)

system.register_agent(tech_agent, "技术")
system.register_agent(sales_agent, "销售")
system.register_agent(support_agent, "客服")

# 执行任务（自动选择合适的模式）
result = system.execute_task("用户需要技术支持和产品推荐")
print(result)

# 查看系统状态
status = system.get_system_status()
print(status)

# 多智能体协商
deliberation_result = system.multi_agent_deliberation(
    "我们应该如何改进产品？",
    deliberation_rounds=3
)
print(deliberation_result)
```

### 2. 基础使用 - AgentOrchestrator

```python
from hello_agents.agent.react_agent import ReActAgent
from hello_agents.llm.HelloAgentsLLM import HelloAgentsLLM
from hello_agents.tool.tool_registry import ToolRegistry
from hello_agents.agent.multi_agent.agent_orchestrator import AgentOrchestrator

# 初始化 LLM 和工具
llm = HelloAgentsLLM()
registry = ToolRegistry()

# 创建不同角色的 Agent
technical_agent = ReActAgent("技术专家", llm, registry)
sales_agent = ReActAgent("销售顾问", llm, registry)
support_agent = ReActAgent("客服代表", llm, registry)

# 创建编排器
orchestrator = AgentOrchestrator("客服团队", llm)

# 注册 Agent
orchestrator.register_agent(technical_agent, "技术")
orchestrator.register_agent(sales_agent, "销售")
orchestrator.register_agent(support_agent, "客服")

# 执行复杂任务
result = orchestrator.coordinate("用户需要技术支持和产品推荐")
print(result)
```

### 2. 团队协作 - AgentTeam

```python
from hello_agents.agent.multi_agent.agent_team import AgentTeam

# 创建团队
research_team = AgentTeam("研究团队", collaboration_mode="pipeline")

# 添加团队成员
research_team.add_member(researcher, "研究员")
research_team.add_member(analyst, "分析师")
research_team.add_member(writer, "撰写者")

# 团队协作
result = research_team.collaborate("研究人工智能发展趋势")
print(result)
```

## 🔧 核心功能详解

### MultiAgentSystem 统一入口（推荐使用）

#### 四种运行模式

1. **Standalone 模式** - 独立运行，简单任务
2. **Orchestrated 模式** - 编排器模式，复杂任务分解
3. **Team 模式** - 团队协作模式，多 Agent 共同完成
4. **Hybrid 模式** - 混合模式，结合编排器和团队

#### 主要功能

```python
# 获取系统状态
status = system.get_system_status()

# 获取任务历史
history = system.get_task_history()

# 清空历史
system.clear_history()

# 添加自定义组件
system.add_custom_component("my_tool", custom_tool)

# 查看系统信息
print(system)
```

#### 使用示例

```python
# 场景1：简单任务（Standalone）
simple_system = MultiAgentSystem("简单系统")
simple_system.setup_as_team("快速团队", "pipeline")
simple_system.register_agent(agent1, "执行者")
result = simple_system.execute_task("回答今天天气")

# 场景2：复杂任务编排（Orchestrated）
complex_system = MultiAgentSystem("复杂系统")
complex_system.setup_as_orchestrator("高级编排器")
complex_system.register_agent(agent1, "技术")
complex_system.register_agent(agent2, "销售")
result = complex_system.execute_task("用户要开发一个电商网站")

# 场景3：团队协作（Team）
team_system = MultiAgentSystem("协作系统")
team_system.setup_as_team("研发团队", "peer_to_peer")
team_system.register_agent(researcher, "研究员")
team_system.register_agent(developer, "开发者")
team_system.register_agent(tester, "测试员")
result = team_system.collaborate("开发移动应用")

# 场景4：混合模式（Hybrid）
hybrid_system = MultiAgentSystem("混合系统")
hybrid_system.setup_as_hybrid(
    orchestrator_name="项目编排",
    team_name="执行团队",
    collaboration_mode="hierarchical"
)
# 注册 Agent 到两个组件
hybrid_system.register_agent(planner, "规划")
hybrid_system.register_agent(developer, "开发")
result = hybrid_system.execute_task("完成项目开发")
```

### AgentOrchestrator 编排器

#### 主要功能
- **智能任务分解**: 使用 LLM 将复杂任务分解为子任务
- **角色匹配**: 根据任务特性匹配合适的 Agent
- **结果聚合**: 综合多个 Agent 的执行结果
- **历史管理**: 记录任务执行历史

#### 使用示例

```python
# 获取任务历史
history = orchestrator.get_task_history()

# 清空历史
orchestrator.clear_history()

# 查看编排器信息
print(orchestrator)
```

### AgentTeam 智能体团队

#### 协作模式

1. **层级协作 (Hierarchical)**
   - 指定协调者进行任务分配
   - 适合有明确领导结构的团队

2. **对等协作 (Peer-to-Peer)**
   - 所有成员平等参与
   - 适合需要多角度分析的任务

3. **流水线协作 (Pipeline)**
   - 按顺序处理任务
   - 适合需要多阶段处理的任务

#### 使用示例

```python
# 设置协调者
team.add_member(coordinator, "协调者", is_coordinator=True)

# 获取团队信息
members = team.get_member_info()

# 获取协作历史
history = team.get_collaboration_history()

# 清空历史
team.clear_history()
```

### CommunicationBus 通信总线

#### 消息类型
- **发布/订阅**: 定向消息传递
- **广播**: 向所有订阅者发送消息
- **直接消息**: 点对点通信

#### 使用示例

```python
from hello_agents.agent.multi_agent.communication_bus import CommunicationBus

# 创建通信总线
bus = CommunicationBus()

# 订阅消息
def message_handler(message):
    print(f"收到消息: {message}")

bus.subscribe("agent1", message_handler, ["task", "result"])

# 发布消息
bus.publish("agent2", {"type": "task", "content": "新任务"}, "task")

# 广播消息
bus.broadcast("system", {"type": "announcement", "content": "系统通知"}, "broadcast")

# 发送直接消息
bus.send_direct("agent1", "agent2", {"type": "direct", "content": "私密消息"}, "direct")

# 获取统计信息
stats = bus.get_statistics()
```

### SharedMemory 共享记忆

#### 功能特性
- **知识存储**: 支持结构化知识存储
- **智能检索**: 基于内容和元数据的搜索
- **过期管理**: 自动清理过期知识
- **对话记录**: 维护团队对话历史

#### 使用示例

```python
from hello_agents.agent.multi_agent.shared_memory import SharedMemory

# 创建共享记忆
memory = SharedMemory()

# 共享知识
memory.share_knowledge(
    agent_id="agent1",
    knowledge={"topic": "AI", "content": "人工智能基础知识"},
    knowledge_type="technical",
    importance=0.8,
    tags=["AI", "技术"]
)

# 搜索知识
results = memory.search_knowledge(
    query="人工智能",
    knowledge_type="technical",
    min_importance=0.5,
    tags=["技术"]
)

# 管理任务上下文
memory.set_task_context("task1", {"status": "进行中", "progress": 50})
context = memory.get_task_context("task1")

# 记录对话
memory.add_conversation("agent1", "你好，有什么需要帮助的吗？", "greeting")

# 获取统计信息
stats = memory.get_statistics()
```

## 🎯 应用场景

### 1. 客服系统
```python
# 多角色客服团队
客服编排器 = AgentOrchestrator("客服编排器")
客服编排器.register_agent(技术客服, "技术")
客服编排器.register_agent(销售客服, "销售") 
客服编排器.register_agent(售后客服, "售后")

# 处理复杂客户问题
result = 客服编排器.coordinate("产品技术问题+购买咨询+售后服务")
```

### 2. 研发团队
```python
# 研发流水线团队
研发团队 = AgentTeam("研发团队", "pipeline")
研发团队.add_member(产品经理, "需求分析")
研发团队.add_member(设计师, "UI设计")
研发团队.add_member(开发者, "编码实现")
研发团队.add_member(测试员, "质量测试")

# 协作开发项目
result = 研发团队.collaborate("开发新的移动应用")
```

### 3. 研究分析
```python
# 研究分析团队
研究团队 = AgentTeam("研究团队", "peer_to_peer")
研究团队.add_member(数据收集员, "数据收集")
研究团队.add_member(分析师, "数据分析")
研究团队.add_member(报告撰写员, "报告撰写")

# 多角度研究分析
result = 研究团队.collaborate("分析市场趋势和竞争格局")
```

## ⚙️ 配置选项

### AgentOrchestrator 配置
```python
orchestrator = AgentOrchestrator(
    name="编排器名称",
    llm=llm_instance  # 可选的 LLM 实例
)
```

### AgentTeam 配置
```python
team = AgentTeam(
    team_name="团队名称",
    collaboration_mode="hierarchical"  # hierarchical, peer_to_peer, pipeline
)
```

### CommunicationBus 配置
```python
bus = CommunicationBus(
    max_queue_size=1000  # 最大消息队列大小
)
```

### SharedMemory 配置
```python
memory = SharedMemory(
    max_knowledge_size=1000,  # 最大知识库大小
    ttl_hours=24  # 知识过期时间（小时）
)
```

## 🔍 调试和监控

### 查看系统状态
```python
# 编排器状态
print(f"编排器: {orchestrator}")
print(f"任务历史: {len(orchestrator.get_task_history())}")

# 团队状态
print(f"团队: {team}")
print(f"成员: {team.get_member_info()}")

# 通信状态
print(f"通信总线: {bus}")
print(f"统计: {bus.get_statistics()}")

# 记忆状态
print(f"共享记忆: {memory}")
print(f"统计: {memory.get_statistics()}")
```

### 错误处理
```python
try:
    result = orchestrator.coordinate(复杂任务)
except Exception as e:
    print(f"任务执行失败: {e}")
    # 可以在这里添加重试逻辑或错误处理
```

## 🚀 性能优化建议

1. **合理设置团队规模**: 根据任务复杂度选择合适数量的 Agent
2. **选择合适的协作模式**: 根据任务特性选择最有效的协作方式
3. **优化消息传递**: 减少不必要的通信开销
4. **定期清理记忆**: 及时清理过期的知识和历史记录
5. **监控系统资源**: 关注内存和计算资源的使用情况

## 📚 示例代码

完整的示例代码请参考 `demo.py` 文件，其中包含了多种使用场景的详细演示。

---

**Multi-Agent 系统** - 让智能体协作变得更简单、更强大！🚀