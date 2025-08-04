"""
CrewAI Agentic Patterns 測試配置

提供測試環境設定和共用 fixtures，支援：
- 單元測試
- 整合測試  
- 效能測試
- Agentic Pattern 測試
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

# 設定測試環境變數
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture(scope="session")
def event_loop():
    """為整個測試會話建立事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """模擬 LLM 回應"""
    return {
        "content": "這是一個模擬的 LLM 回應",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 150,
            "total_tokens": 250
        },
        "model": "gpt-4o-mini"
    }


@pytest.fixture
def sample_agent_config():
    """範例 Agent 配置"""
    return {
        "role": "測試專家",
        "goal": "執行全面的軟體測試",
        "backstory": "具備10年測試經驗的專業QA工程師",
        "reasoning": True,
        "memory": True,
        "verbose": False  # 測試時關閉詳細輸出
    }


@pytest.fixture
def mock_agent(sample_agent_config):
    """模擬 Agent"""
    agent = Mock(spec=Agent)
    agent.role = sample_agent_config["role"]
    agent.goal = sample_agent_config["goal"]
    agent.backstory = sample_agent_config["backstory"]
    agent.reasoning = sample_agent_config["reasoning"]
    agent.memory = sample_agent_config["memory"]
    agent.execute.return_value = "模擬 Agent 執行結果"
    return agent


@pytest.fixture
def sample_task_config():
    """範例 Task 配置"""
    return {
        "description": "執行單元測試並生成報告",
        "expected_output": "包含測試結果和覆蓋率的詳細報告",
        "async_execution": False
    }


@pytest.fixture
def mock_task(sample_task_config, mock_agent):
    """模擬 Task"""
    task = Mock(spec=Task)
    task.description = sample_task_config["description"]
    task.expected_output = sample_task_config["expected_output"]
    task.agent = mock_agent
    task.async_execution = sample_task_config["async_execution"]
    
    # 模擬執行結果
    task.execute.return_value = Mock()
    task.execute.return_value.raw = "測試執行完成，覆蓋率 95%"
    task.execute.return_value.pydantic = None
    task.execute.return_value.json_dict = {"coverage": 95, "tests_passed": 120}
    
    return task


@pytest.fixture
def mock_tool():
    """模擬工具"""
    tool = Mock(spec=BaseTool)
    tool.name = "測試工具"
    tool.description = "用於測試的模擬工具"
    tool.run.return_value = "工具執行成功"
    return tool


@pytest.fixture
def sample_crew_config():
    """範例 Crew 配置"""
    return {
        "verbose": False,
        "memory": True,
        "planning": True
    }


@pytest.fixture
def mock_crew(mock_agent, mock_task, sample_crew_config):
    """模擬 Crew"""
    crew = Mock(spec=Crew)
    crew.agents = [mock_agent]
    crew.tasks = [mock_task]
    crew.verbose = sample_crew_config["verbose"]
    crew.memory = sample_crew_config["memory"]
    
    # 模擬 kickoff 結果
    crew.kickoff.return_value = Mock()
    crew.kickoff.return_value.raw = "Crew 執行完成"
    crew.kickoff.return_value.tasks_output = [mock_task.execute.return_value]
    crew.kickoff.return_value.token_usage = {
        "total_tokens": 500,
        "prompt_tokens": 200,
        "completion_tokens": 300
    }
    
    return crew


# Reflection Pattern 測試 Fixtures
@pytest.fixture
def reflection_test_data():
    """反思模式測試資料"""
    return {
        "initial_content": "這是一個需要改進的初始內容。內容較為簡單，缺少深度。",
        "reflection_criteria": [
            "技術準確性",
            "內容深度",
            "表達清晰度",
            "實用性"
        ],
        "target_score": 8.0,
        "max_iterations": 3
    }


@pytest.fixture
def planning_test_data():
    """規劃模式測試資料"""
    return {
        "project_goal": "開發一個 CrewAI 聊天機器人",
        "constraints": {
            "timeline": "4週",
            "budget": "$10,000",
            "team_size": 3
        },
        "expected_tasks": [
            "需求分析",
            "系統設計", 
            "開發實作",
            "測試驗證",
            "部署上線"
        ]
    }


@pytest.fixture
def tool_use_test_data():
    """工具使用模式測試資料"""
    return {
        "task_description": "查詢最新的比特幣價格並進行分析",
        "available_tools": ["price_api", "data_analysis", "chart_generator"],
        "expected_workflow": [
            "使用 price_api 獲取價格",
            "使用 data_analysis 分析趨勢",
            "使用 chart_generator 生成圖表"
        ],
        "fallback_strategy": "使用快取數據"
    }


@pytest.fixture
def multi_agent_test_data():
    """多代理模式測試資料"""
    return {
        "agents": [
            {"role": "研究員", "speciality": "數據收集"},
            {"role": "分析師", "speciality": "數據分析"},
            {"role": "報告員", "speciality": "報告撰寫"}
        ],
        "collaboration_scenario": "市場研究報告",
        "expected_interactions": [
            "研究員收集市場資料",
            "分析師分析資料趨勢",
            "報告員撰寫最終報告"
        ]
    }


# 效能測試 Fixtures
@pytest.fixture
def performance_test_config():
    """效能測試配置"""
    return {
        "concurrent_requests": 10,
        "test_duration": 30,  # 秒
        "max_response_time": 5.0,  # 秒
        "min_success_rate": 0.95
    }


@pytest.fixture
def benchmark_data():
    """基準測試數據"""
    return {
        "baseline_metrics": {
            "avg_response_time": 2.5,
            "token_usage_per_request": 200,
            "success_rate": 0.98,
            "cost_per_request": 0.01
        },
        "test_cases": [
            {"complexity": "low", "expected_time": 1.0},
            {"complexity": "medium", "expected_time": 2.5},
            {"complexity": "high", "expected_time": 5.0}
        ]
    }


# 監控測試 Fixtures
@pytest.fixture
def monitoring_test_data():
    """監控測試資料"""
    return {
        "metrics": [
            "agent_execution_count",
            "task_completion_rate", 
            "error_rate",
            "token_usage",
            "response_time"
        ],
        "alerts": [
            {"metric": "error_rate", "threshold": 0.05, "severity": "high"},
            {"metric": "response_time", "threshold": 10.0, "severity": "medium"}
        ]
    }


# 整合測試 Fixtures
@pytest.fixture
def integration_test_env():
    """整合測試環境"""
    return {
        "database_url": "sqlite:///test.db",
        "redis_url": "redis://localhost:6379/1", 
        "chroma_host": "localhost",
        "chroma_port": 8001,
        "test_api_keys": {
            "openai": "test-openai-key",
            "anthropic": "test-anthropic-key"
        }
    }


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """自動清理測試資料"""
    yield
    
    # 清理測試檔案
    test_files = [
        "test_output.json",
        "test_log.txt",
        "test_cache.pkl"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


# 參數化測試資料
@pytest.fixture(params=["gpt-4o", "gpt-4o-mini", "claude-3-haiku"])
def llm_models(request):
    """參數化的 LLM 模型列表"""
    return request.param


@pytest.fixture(params=["sequential", "hierarchical", "consensual"])
def process_types(request):
    """參數化的 Process 類型"""
    return request.param


@pytest.fixture(params=[1, 3, 5])
def iteration_counts(request):
    """參數化的迭代次數"""
    return request.param


# 自訂標記
def pytest_configure(config):
    """配置自訂 pytest 標記"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "reflection: mark test as reflection pattern test"
    )
    config.addinivalue_line(
        "markers", "planning: mark test as planning pattern test"
    )
    config.addinivalue_line(
        "markers", "tooluse: mark test as tool use pattern test"
    )
    config.addinivalue_line(
        "markers", "multiagent: mark test as multi-agent pattern test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


# 測試會話鉤子
@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """測試會話設定"""
    print("\n🚀 開始 CrewAI Agentic Patterns 測試會話")
    
    # 設定測試環境
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # 降低測試時的日誌層級
    
    yield
    
    print("\n✅ CrewAI Agentic Patterns 測試會話完成")


# 錯誤處理輔助函數
@pytest.fixture
def assert_agent_execution():
    """斷言 Agent 執行的輔助函數"""
    def _assert_execution(agent, task, expected_keywords=None):
        """
        斷言 Agent 執行結果
        
        Args:
            agent: 執行的 Agent
            task: 執行的 Task  
            expected_keywords: 期望在結果中出現的關鍵字
        """
        assert agent is not None, "Agent 不能為空"
        assert task is not None, "Task 不能為空"
        
        result = agent.execute(task.description)
        assert result is not None, "執行結果不能為空"
        assert len(result) > 0, "執行結果不能為空字串"
        
        if expected_keywords:
            for keyword in expected_keywords:
                assert keyword in result, f"結果中應包含關鍵字: {keyword}"
        
        return result
    
    return _assert_execution


@pytest.fixture  
def mock_external_services():
    """模擬外部服務"""
    services = {
        "openai_api": Mock(),
        "serper_api": Mock(),
        "chroma_db": Mock(),
        "redis_cache": Mock()
    }
    
    # 設定預設回應
    services["openai_api"].chat.completions.create.return_value = Mock()
    services["openai_api"].chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="模擬的 OpenAI 回應"))
    ]
    
    services["serper_api"].search.return_value = {
        "organic": [
            {"title": "測試結果", "snippet": "這是測試搜尋結果"}
        ]
    }
    
    services["chroma_db"].query.return_value = {
        "documents": [["相關文件內容"]],
        "distances": [[0.1]]
    }
    
    services["redis_cache"].get.return_value = None
    services["redis_cache"].set.return_value = True
    
    return services


# 資料驗證輔助
@pytest.fixture
def validate_agentic_pattern():
    """驗證 Agentic Pattern 實作的輔助函數"""
    def _validate_pattern(pattern_type: str, implementation: Any, expected_features: List[str]):
        """
        驗證 Agentic Pattern 實作
        
        Args:
            pattern_type: 模式類型 (reflection/planning/tooluse/multiagent)
            implementation: 實作物件
            expected_features: 期望的功能特性
        """
        assert implementation is not None, f"{pattern_type} 實作不能為空"
        
        for feature in expected_features:
            assert hasattr(implementation, feature), f"{pattern_type} 應實作 {feature} 功能"
        
        # 根據不同模式進行特定驗證
        if pattern_type == "reflection":
            assert hasattr(implementation, "reflect_on_output"), "Reflection 模式應有反思功能"
            assert hasattr(implementation, "iterative_refinement"), "Reflection 模式應有迭代改進功能"
            
        elif pattern_type == "planning":
            assert hasattr(implementation, "create_plan"), "Planning 模式應有計劃創建功能"
            assert hasattr(implementation, "monitor_progress"), "Planning 模式應有進度監控功能"
            
        elif pattern_type == "tooluse":
            assert hasattr(implementation, "execute_with_tools"), "Tool Use 模式應有工具執行功能"
            assert hasattr(implementation, "execute_fallback_strategy"), "Tool Use 模式應有備用策略"
            
        elif pattern_type == "multiagent":
            assert hasattr(implementation, "delegate_task"), "Multi-Agent 模式應有任務委派功能"
            assert hasattr(implementation, "request_assistance"), "Multi-Agent 模式應有協助請求功能"
    
    return _validate_pattern 