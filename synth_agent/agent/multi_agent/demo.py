"""
多智能体系统演示示例
"""

from synth_agent.agent.react_agent import ReActAgent
from synth_agent.llm.synth_LLM import SynthLLM
from synth_agent.tool.tool_registry import ToolRegistry
from synth_agent.agent.multi_agent.agent_orchestrator import AgentOrchestrator
from synth_agent.agent.multi_agent.agent_team import AgentTeam


def demo_agent_orchestrator():
    """演示 AgentOrchestrator 的使用"""
    print("🚀 开始演示 AgentOrchestrator")
    print("=" * 50)
    
    # 初始化 LLM
    llm = SynthLLM()
    
    # 初始化工具注册表
    registry = ToolRegistry()
    
    # 创建不同角色的 Agent
    print("📝 创建不同角色的 Agent...")
    
    # 技术专家 Agent
    tech_agent = ReActAgent(
        name="技术专家",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个技术专家，擅长解决技术问题、代码开发和系统设计。
        请用专业的技术语言回答问题，并提供详细的解决方案。"""
    )
    
    # 销售顾问 Agent
    sales_agent = ReActAgent(
        name="销售顾问",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个销售顾问，擅长产品推荐、销售策略和客户关系管理。
        请用友好的语言与客户沟通，提供个性化的产品建议。"""
    )
    
    # 客服代表 Agent
    support_agent = ReActAgent(
        name="客服代表",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个客服代表，擅长解决客户问题、提供技术支持和处理投诉。
        请用耐心和专业的态度服务客户。"""
    )
    
    # 创建编排器
    orchestrator = AgentOrchestrator("客服团队编排器", llm=llm)
    
    # 注册 Agent
    print("👥 注册 Agent 到编排器...")
    orchestrator.register_agent(tech_agent, "技术")
    orchestrator.register_agent(sales_agent, "销售")
    orchestrator.register_agent(support_agent, "客服")
    
    # 执行任务
    print("🎯 执行复杂任务...")
    
    tasks = [
        "用户想要购买一台笔记本电脑，需要技术规格建议和价格咨询",
        "客户反映产品使用过程中遇到技术问题，需要技术支持",
        "用户想要了解我们的产品线和服务套餐"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📋 任务 {i}: {task}")
        print("-" * 30)
        
        result = orchestrator.coordinate(task)
        print(f"✅ 任务完成结果:\n{result}")
        
        # 显示任务历史
        history = orchestrator.get_task_history()
        print(f"📊 任务历史记录数: {len(history)}")
    
    print("\n✅ AgentOrchestrator 演示完成")
    print("=" * 50)


def demo_agent_team():
    """演示 AgentTeam 的使用"""
    print("\n🚀 开始演示 AgentTeam")
    print("=" * 50)
    
    # 初始化 LLM
    llm = SynthLLM()
    
    # 初始化工具注册表
    registry = ToolRegistry()
    
    # 创建研究团队成员
    print("📝 创建研究团队成员...")
    
    # 研究员 Agent
    researcher = ReActAgent(
        name="研究员",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个研究员，擅长收集信息、分析数据和发现规律。
        请用严谨的学术态度进行研究工作。"""
    )
    
    # 分析师 Agent
    analyst = ReActAgent(
        name="分析师",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个分析师，擅长数据分析和趋势预测。
        请用逻辑清晰的方式呈现分析结果。"""
    )
    
    # 撰写者 Agent
    writer = ReActAgent(
        name="撰写者",
        llm=llm,
        tool_registry=registry,
        system_prompt="""你是一个撰写者，擅长将复杂信息整理成清晰的报告。
        请用简洁明了的语言撰写文档。"""
    )
    
    # 测试不同的协作模式
    collaboration_modes = ["hierarchical", "peer_to_peer", "pipeline"]
    
    for mode in collaboration_modes:
        print(f"\n🤝 测试 {mode} 协作模式...")
        
        # 创建团队
        team = AgentTeam(f"研究团队-{mode}", collaboration_mode=mode)
        
        # 添加成员
        team.add_member(researcher, "研究员", is_coordinator=(mode == "hierarchical"))
        team.add_member(analyst, "分析师")
        team.add_member(writer, "撰写者")
        
        # 执行团队任务
        research_task = "研究人工智能在医疗领域的应用现状和未来趋势"
        
        print(f"📋 研究任务: {research_task}")
        result = team.collaborate(research_task)
        
        print(f"✅ 团队协作结果 ({mode} 模式):")
        print("-" * 40)
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # 显示团队信息
        members = team.get_member_info()
        print(f"👥 团队成员: {[m['role'] for m in members]}")
        
        # 显示协作历史
        history = team.get_collaboration_history()
        print(f"📊 协作历史记录数: {len(history)}")
    
    print("\n✅ AgentTeam 演示完成")
    print("=" * 50)


def demo_advanced_features():
    """演示高级功能"""
    print("\n🚀 开始演示高级功能")
    print("=" * 50)
    
    # 初始化 LLM
    llm = SynthLLM()
    
    # 初始化工具注册表
    registry = ToolRegistry()
    
    # 创建复杂的多智能体系统
    print("🏗️  创建复杂的多智能体系统...")
    
    # 创建多个专业 Agent
    agents_info = [
        ("产品经理", "负责产品规划和需求分析"),
        ("UI设计师", "负责用户界面设计"),
        ("前端开发", "负责前端技术实现"),
        ("后端开发", "负责后端服务开发"),
        ("测试工程师", "负责质量保证和测试")
    ]
    
    agents = {}
    for role, description in agents_info:
        agents[role] = ReActAgent(
            name=role,
            llm=llm,
            tool_registry=registry,
            system_prompt=f"""你是一个{role}，{description}。
            请专注于你的专业领域，并与团队成员协作。"""
        )
    
    # 创建项目编排器
    project_orchestrator = AgentOrchestrator("项目开发编排器", llm=llm)
    
    # 注册所有 Agent
    for role, agent in agents.items():
        project_orchestrator.register_agent(agent, role)
    
    # 执行复杂的项目任务
    project_tasks = [
        "开发一个在线购物网站，需要产品展示、购物车、支付功能",
        "设计一个移动应用，支持用户注册、内容浏览和社交功能",
        "构建一个数据分析平台，支持数据可视化和管理功能"
    ]
    
    for i, task in enumerate(project_tasks, 1):
        print(f"\n🏗️  项目任务 {i}: {task}")
        print("-" * 40)
        
        # 使用编排器协调项目
        result = project_orchestrator.coordinate(task)
        
        print(f"✅ 项目协调结果:")
        print(result[:300] + "..." if len(result) > 300 else result)
        
        # 显示统计信息
        stats = project_orchestrator.shared_memory.get_statistics()
        print(f"📊 共享记忆统计: {stats}")
    
    print("\n✅ 高级功能演示完成")
    print("=" * 50)


def main():
    """主函数"""
    print("🎯 Hello Agents Python - 多智能体系统演示")
    print("=" * 60)
    
    try:
        # 演示基础功能
        demo_agent_orchestrator()
        
        # 演示团队协作
        demo_agent_team()
        
        # 演示高级功能
        demo_advanced_features()
        
        print("\n🎉 所有演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("💡 请确保已正确配置 LLM 和工具注册表")


if __name__ == "__main__":
    main()