#!/usr/bin/env python3
"""
CrewAI × Agentic Design Patterns 演示腳本

展示已完成的核心模組和設計模式功能：
1. Agent 基礎類別和工廠
2. 記憶系統管理
3. 工具註冊表和網路搜索
4. Reflection Pattern 自我批評
5. Planning Pattern WBS 規劃
6. 代碼解釋器

運行方式: python demo.py
"""

import asyncio
import json
from datetime import datetime, timedelta

# 核心模組
from src.core.agents.agent_base import AgentFactory, AgentConfig, AgentType
from src.core.memory.memory_manager import MemoryManager, MemoryType
from src.core.tools.tool_registry import ToolRegistry
from src.core.tools.web_search_tool import WebSearchTool
from src.core.tools.code_interpreter_tool import CodeInterpreterTool

# Agentic Patterns
from src.patterns.reflection.self_critique import SelfCritiqueEngine, ReflectionLevel
from src.patterns.planning.wbs_planner import WBSPlanner


def print_banner(title: str):
    """打印橫幅"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def demo_agent_factory():
    """演示 Agent 工廠功能"""
    print_banner("Agent 工廠演示")
    
    # 創建不同類型的 Agent
    agents = []
    
    # 1. 工作者 Agent
    worker_agent = AgentFactory.create_worker_agent(
        role="Python 開發工程師",
        goal="高效開發 Python 應用程式",
        backstory="具備5年 Python 開發經驗，熟悉 Web 開發和 AI 技術"
    )
    agents.append(("工作者", worker_agent))
    
    # 2. 管理者 Agent
    manager_agent = AgentFactory.create_manager_agent(
        role="技術團隊領導",
        goal="協調團隊完成項目目標",
        backstory="具備10年技術管理經驗，擅長團隊協作和項目規劃"
    )
    agents.append(("管理者", manager_agent))
    
    # 3. 專家 Agent
    specialist_agent = AgentFactory.create_specialist_agent(
        role="AI 架構師",
        goal="設計和實作 AI 系統",
        backstory="AI 領域專家，專精於多代理系統設計",
        specialization="ai_architecture"
    )
    agents.append(("專家", specialist_agent))
    
    # 顯示 Agent 資訊
    for agent_type, agent in agents:
        print(f"\n{agent_type} Agent:")
        print(f"  ID: {agent.agent_id}")
        print(f"  角色: {agent.role}")
        print(f"  類型: {agent.agent_type.value}")
        print(f"  狀態: {agent.status_summary}")
    
    return agents


async def demo_memory_system():
    """演示記憶系統功能"""
    print_banner("記憶系統演示")
    
    # 創建記憶管理器
    memory_manager = MemoryManager(storage_type="hybrid")
    
    # 存儲不同類型的記憶
    memories = [
        ("學習了 CrewAI 的基本架構", MemoryType.LONG_TERM, ["學習", "架構"]),
        ("當前正在開發演示腳本", MemoryType.WORKING, ["開發", "演示"]),
        ("參加了 AI 研討會", MemoryType.EPISODIC, ["會議", "AI"]),
        ("掌握了 Python 異步編程", MemoryType.LONG_TERM, ["技能", "Python"])
    ]
    
    memory_ids = []
    
    for content, memory_type, tags in memories:
        memory_id = await memory_manager.store_memory(
            content=content,
            memory_type=memory_type,
            tags=tags
        )
        memory_ids.append(memory_id)
        print(f"✓ 存儲記憶: {content[:30]}...")
    
    # 搜索記憶
    print("\n記憶搜索結果:")
    search_results = await memory_manager.search_memories("CrewAI")
    for result in search_results:
        print(f"  - {result.content}")
    
    # 獲取統計資訊
    stats = memory_manager.get_memory_statistics()
    print(f"\n記憶統計: {stats}")
    
    return memory_manager


def demo_tool_registry():
    """演示工具註冊表功能"""
    print_banner("工具註冊表演示")
    
    # 獲取工具註冊表
    registry = ToolRegistry()
    
    # 創建並註冊工具
    search_tool = WebSearchTool()
    code_tool = CodeInterpreterTool()
    
    print("已註冊的工具:")
    tools = registry.list_tools()
    for tool_name in tools:
        tool_info = registry.get_tool_info(tool_name)
        if tool_info:
            print(f"  - {tool_name}: {tool_info['description']}")
    
    # 工具統計
    stats = registry.get_tool_statistics()
    print(f"\n工具統計: {stats}")
    
    return registry, search_tool, code_tool


def demo_reflection_pattern():
    """演示 Reflection Pattern 功能"""
    print_banner("Reflection Pattern 演示")
    
    # 創建自我批評引擎
    critique_engine = SelfCritiqueEngine()
    
    # 測試內容
    test_content = """
    人工智慧正在快速發展。AI 技術包括機器學習和深度學習。
    這些技術在很多領域都有應用。醫療、金融、教育等行業都在使用 AI。
    AI 的發展會改變我們的生活和工作方式。
    """
    
    print("原始內容:")
    print(test_content.strip())
    
    # 執行反思分析
    reflection_result = critique_engine.critique(
        content=test_content,
        context={
            "content_type": "article",
            "min_length": 200,
            "required_keywords": ["機器學習", "應用場景"]
        }
    )
    
    print(f"\n反思結果:")
    print(f"  整體評分: {reflection_result.overall_score:.2f}")
    print(f"  是否需要修訂: {reflection_result.needs_revision}")
    print(f"  反思時間: {reflection_result.reflection_time:.3f}秒")
    
    print(f"\n發現的問題:")
    for point in reflection_result.critique_points:
        severity = "🚨" if point.is_critical else "⚠️" if point.is_major else "💡"
        print(f"  {severity} [{point.aspect.value}] {point.description}")
        print(f"     建議: {point.suggestion}")
    
    print(f"\n改進建議:")
    for suggestion in reflection_result.improvement_suggestions:
        print(f"  • {suggestion}")
    
    return reflection_result


def demo_planning_pattern():
    """演示 Planning Pattern 功能"""
    print_banner("Planning Pattern 演示")
    
    # 創建 WBS 規劃器
    planner = WBSPlanner()
    
    # 創建項目計劃
    project_plan = planner.create_project_plan(
        project_description="開發一個多代理 AI 助手系統",
        context={
            "project_type": "software_development",
            "duration_weeks": 6,
            "team_size": 3,
            "available_skills": ["programming", "ai", "design"],
            "decomposition_strategy": "functional"
        }
    )
    
    print("項目分析:")
    analysis = project_plan['project_analysis']
    print(f"  複雜度: {analysis['complexity_level']}")
    print(f"  預計時長: {analysis['estimated_duration_weeks']} 週")
    print(f"  所需技能: {', '.join(analysis['required_skills'])}")
    
    print(f"\nWBS 結構:")
    wbs = project_plan['wbs_structure']
    print(f"  總節點數: {wbs['total_nodes']}")
    print(f"  最大層級: {wbs['max_level']}")
    print(f"  總估算工時: {wbs['total_estimated_hours']} 小時")
    
    print(f"\n主要任務階段:")
    for node_id, node_data in wbs['nodes'].items():
        if node_data['level'] == 1:  # 第一層任務
            print(f"  - {node_data['name']}: {node_data['estimated_hours']}小時")
    
    print(f"\n項目排程:")
    schedule = project_plan['schedule']
    print(f"  項目開始: {schedule['project_start']}")
    print(f"  項目結束: {schedule['project_end']}")
    print(f"  總持續時間: {schedule['total_duration_days']} 天")
    print(f"  關鍵路徑任務數: {len(schedule['critical_path'])}")
    
    print(f"\n風險評估:")
    risks = project_plan['risk_assessment']
    if risks['high_risk_tasks']:
        print(f"  高風險任務: {len(risks['high_risk_tasks'])} 個")
        for risk_task in risks['high_risk_tasks'][:2]:  # 顯示前2個
            print(f"    - {risk_task['task_name']} (風險分數: {risk_task['risk_score']:.2f})")
    
    if risks['mitigation_strategies']:
        print(f"  緩解策略:")
        for strategy in risks['mitigation_strategies']:
            print(f"    • {strategy}")
    
    return project_plan


def demo_code_interpreter():
    """演示代碼解釋器功能"""
    print_banner("代碼解釋器演示")
    
    # 創建代碼解釋器
    interpreter = CodeInterpreterTool()
    
    # 測試 Python 代碼
    python_code = """
# 計算斐波那契數列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 計算前8個數字
result = [fibonacci(i) for i in range(8)]
print("斐波那契數列:", result)
print("總和:", sum(result))

# 簡單數據分析
import math
mean = sum(result) / len(result)
print(f"平均值: {mean:.2f}")
"""
    
    print("執行 Python 代碼:")
    print("```python")
    print(python_code.strip())
    print("```")
    
    # 執行代碼
    result = interpreter._run(python_code, "python")
    print("\n執行結果:")
    print(result)
    
    return interpreter


async def main():
    """主演示函數"""
    print("🤖 CrewAI × Agentic Design Patterns 演示")
    print("=" * 80)
    print("本演示將展示已完成的核心模組和設計模式功能")
    
    try:
        # 1. Agent 工廠演示
        agents = demo_agent_factory()
        
        # 2. 記憶系統演示
        memory_manager = await demo_memory_system()
        
        # 3. 工具註冊表演示
        registry, search_tool, code_tool = demo_tool_registry()
        
        # 4. Reflection Pattern 演示
        reflection_result = demo_reflection_pattern()
        
        # 5. Planning Pattern 演示
        project_plan = demo_planning_pattern()
        
        # 6. 代碼解釋器演示
        interpreter = demo_code_interpreter()
        
        # 總結
        print_banner("演示總結")
        print("✅ 已完成的核心功能:")
        print("  • Agent 基礎類別和工廠模式")
        print("  • 多層次記憶系統（工作記憶、長期記憶、情境記憶）")
        print("  • 工具註冊表和動態工具管理")
        print("  • 網路搜索工具（支援多引擎）")
        print("  • 代碼解釋器（支援多語言安全執行）")
        print("  • Reflection Pattern（自我批評和迭代改進）")
        print("  • Planning Pattern（WBS 規劃和關鍵路徑分析）")
        
        print("\n🚧 開發中的功能:")
        print("  • Tool Use Pattern（智能工具選擇和容錯機制）")
        print("  • Multi-Agent Pattern（團隊協作和通訊機制）")
        print("  • 高階工作流程管道")
        print("  • 週次實驗室內容")
        
        print("\n📊 系統統計:")
        print(f"  • 已創建 Agent: {len(agents)} 個")
        print(f"  • 記憶系統健康: {'正常' if memory_manager.is_healthy() else '異常'}")
        print(f"  • 已註冊工具: {len(registry.list_tools())} 個")
        print(f"  • 反思分析耗時: {reflection_result.reflection_time:.3f}秒")
        print(f"  • 項目規劃節點: {project_plan['wbs_structure']['total_nodes']} 個")
        
        print("\n🎯 下一步計劃:")
        print("  1. 完成 Tool Use Pattern 和 Multi-Agent Pattern")
        print("  2. 實作高階工作流程管道")
        print("  3. 創建週次實驗室教學內容")
        print("  4. 建立完整的測試覆蓋")
        print("  5. 部署和監控系統設置")
        
        print("\n🌟 感謝使用 CrewAI × Agentic Design Patterns！")
        print("如有問題或建議，請查看 README.md 或聯繫開發團隊。")
        
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        print("請檢查環境配置或聯繫開發團隊")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main()) 