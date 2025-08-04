#!/usr/bin/env python3
"""
Agent Base Debug 測試腳本
測試修復後的 agent_base.py 功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.agents.agent_base import AgentConfig, AgentFactory, AgentType

def test_agent_creation():
    """測試 Agent 創建功能"""
    print("=== 測試 Agent 創建 ===")
    
    # 創建基本配置
    config = AgentConfig(
        role="測試工程師",
        goal="驗證系統功能正常運作",
        backstory="具備豐富的軟體測試經驗，專精於自動化測試"
    )
    
    print(f"✅ 配置創建成功: {config.role}")
    
    # 創建 Worker Agent
    worker = AgentFactory.create_worker_agent(
        role="數據分析師",
        goal="深入分析用戶行為數據，提供有價值的洞察",
        backstory="專業的數據科學家，具備豐富的分析經驗"
    )
    
    print(f"✅ Worker Agent 創建成功: {worker.agent_id}")
    print(f"   - 角色: {worker.role}")
    print(f"   - 類型: {worker.agent_type.value}")
    print(f"   - 狀態: {worker.state.value}")
    
    # 創建 Manager Agent
    manager = AgentFactory.create_manager_agent(
        role="專案經理",
        goal="有效協調團隊資源，確保專案按時高質量完成",
        backstory="具備豐富的專案管理經驗，擅長跨部門協作"
    )
    
    print(f"✅ Manager Agent 創建成功: {manager.agent_id}")
    print(f"   - 角色: {manager.role}")
    print(f"   - 委派權限: {manager.allow_delegation}")
    
    # 創建 Specialist Agent
    specialist = AgentFactory.create_specialist_agent(
        role="AI研究員",
        goal="設計並開發創新的機器學習模型，推動AI技術發展",
        backstory="AI領域的資深專家，具備深厚的理論基礎和實戰經驗",
        specialization="machine_learning"
    )
    
    print(f"✅ Specialist Agent 創建成功: {specialist.agent_id}")
    print(f"   - 專業領域: {specialist.specialization}")
    
    return worker, manager, specialist

def test_agent_metrics():
    """測試 Agent 指標功能"""
    print("\n=== 測試 Agent 指標 ===")
    
    config = AgentConfig(
        role="測試助手",
        goal="執行各種基本測試任務，確保系統穩定性",
        backstory="專業的AI測試助手，具備自動化測試能力",
        reasoning=False,  # 關閉推理以避免 LLM 錯誤
        memory=False      # 關閉記憶以簡化測試
    )
    
    agent = AgentFactory.create_agent("base", config)
    
    # 測試狀態更新
    agent.update_state(agent.state.THINKING)
    print(f"✅ 狀態更新成功: {agent.state.value}")
    
    # 測試指標
    print(f"✅ 初始指標: 完成任務={agent.metrics.tasks_completed}, 成功率={agent.metrics.success_rate}")
    
    # 測試狀態摘要
    summary = agent.status_summary
    print(f"✅ 狀態摘要: {summary}")
    
    return agent

def test_agent_tools():
    """測試 Agent 工具功能"""
    print("\n=== 測試 Agent 工具 ===")
    
    config = AgentConfig(
        role="工具測試員",
        goal="全面測試各種工具功能，確保工具正常運作",
        backstory="經驗豐富的工具專家，精通各種開發和測試工具"
    )
    
    agent = AgentFactory.create_agent("base", config)
    
    # 測試工具列表
    tools = agent.get_available_tools()
    print(f"✅ 可用工具: {len(tools)} 個")
    
    # 測試導出狀態
    state = agent.export_state()
    print(f"✅ 狀態導出成功: 包含 {len(state.keys())} 個欄位")
    
    return agent

if __name__ == "__main__":
    try:
        print("🚀 開始 Agent Debug 測試\n")
        
        # 測試 Agent 創建
        worker, manager, specialist = test_agent_creation()
        
        # 測試指標功能
        test_agent = test_agent_metrics()
        
        # 測試工具功能
        tool_agent = test_agent_tools()
        
        print("\n🎉 所有測試通過！Agent Base 功能正常。")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()