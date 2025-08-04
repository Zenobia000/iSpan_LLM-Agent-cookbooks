"""
CrewAI 核心 Agent 基礎類別

基於 First Principles 設計：
1. Agent = 具備特定角色、目標和工具的自主實體
2. 所有 Agent 都需要：身份定義、執行能力、互動機制
3. 擴展性原則：統一介面，可插拔組件

參考文檔: docs/core/agents_fundamentals.md
"""

from typing import List, Dict, Optional, Any, Union, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import json
from datetime import datetime

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator

from ..memory.memory_manager import MemoryManager
from ..tools.tool_registry import ToolRegistry


class AgentState(Enum):
    """Agent 狀態枚舉"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentType(Enum):
    """Agent 類型枚舉"""
    WORKER = "worker"           # 工作執行者
    MANAGER = "manager"         # 管理協調者
    SPECIALIST = "specialist"   # 專業領域專家
    REVIEWER = "reviewer"       # 品質審查者
    FACILITATOR = "facilitator" # 協作促進者


@dataclass
class AgentMetrics:
    """Agent 效能指標"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    last_active: Optional[datetime] = None
    
    def update_success_rate(self):
        """更新成功率"""
        total_tasks = self.tasks_completed + self.tasks_failed
        self.success_rate = self.tasks_completed / total_tasks if total_tasks > 0 else 0.0


class AgentConfig(BaseModel):
    """Agent 配置模型"""
    
    # 基本屬性 (First Principles)
    role: str = Field(..., description="Agent 的角色定義")
    goal: str = Field(..., description="Agent 的目標描述")
    backstory: str = Field(..., description="Agent 的背景故事")
    
    # 能力配置 (Fundamentals)
    agent_type: AgentType = Field(default=AgentType.WORKER, description="Agent 類型")
    reasoning: bool = Field(default=True, description="是否啟用推理功能")
    memory: bool = Field(default=True, description="是否啟用記憶功能")
    allow_delegation: bool = Field(default=False, description="是否允許委派任務")
    
    # 執行控制 (Body of Knowledge)
    max_iter: int = Field(default=3, description="最大迭代次數")
    max_execution_time: int = Field(default=300, description="最大執行時間(秒)")
    verbose: bool = Field(default=True, description="是否輸出詳細資訊")
    
    # 工具與知識
    tools: List[str] = Field(default_factory=list, description="工具名稱列表")
    knowledge_sources: List[str] = Field(default_factory=list, description="知識源列表")
    
    # 高階配置
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM 配置")
    system_message: Optional[str] = Field(default=None, description="系統訊息")
    
    @validator('role')
    def validate_role(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("角色定義至少需要3個字符")
        return v.strip()
    
    @validator('goal')
    def validate_goal(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("目標描述至少需要10個字符")
        return v.strip()


class BaseAgent(Agent):
    """
    CrewAI 基礎 Agent 類別
    
    First Principles:
    - Agent 是具備身份、目標和能力的自主實體
    - 必須能夠接收任務、處理資訊、產生輸出
    - 需要具備學習和適應能力
    
    Fundamentals:
    - 角色定義：明確的身份和責任
    - 執行引擎：任務處理和工具使用
    - 互動機制：與其他 Agent 和系統的溝通
    - 記憶系統：經驗累積和知識管理
    
    Body of Knowledge:
    - 符合 Multi-Agent System 設計原則
    - 實作 Agent Communication Language (ACL) 概念
    - 整合 Cognitive Architecture 模式
    """
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        """
        初始化基礎 Agent
        
        Args:
            config: Agent 配置
            tools: 工具列表
        """
        # 解析工具
        resolved_tools = self._resolve_tools(config.tools, tools)
        
        # 呼叫父類別建構子
        super().__init__(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            reasoning=config.reasoning,
            memory=config.memory,
            allow_delegation=config.allow_delegation,
            max_iter=config.max_iter,
            max_execution_time=config.max_execution_time,
            tools=resolved_tools,
            verbose=config.verbose
        )
        
        # 儲存配置和初始化狀態
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.agent_type = config.agent_type
        self.state = AgentState.IDLE
        self.metrics = AgentMetrics()
        
        # 初始化子系統
        self.memory_manager = MemoryManager() if config.memory else None
        self.tool_registry = ToolRegistry()
        
        # 執行歷史和上下文
        self.execution_history: List[Dict[str, Any]] = []
        self.current_context: Dict[str, Any] = {}
        
        # 註冊工具
        for tool in resolved_tools:
            self.tool_registry.register_tool(tool)
    
    def _resolve_tools(self, tool_names: List[str], tools: Optional[List[BaseTool]]) -> List[BaseTool]:
        """解析工具名稱為實際工具物件"""
        resolved_tools = []
        
        # 加入傳入的工具
        if tools:
            resolved_tools.extend(tools)
        
        # 從工具註冊表解析工具名稱
        for tool_name in tool_names:
            tool = ToolRegistry.get_tool_by_name(tool_name)
            if tool:
                resolved_tools.append(tool)
            else:
                print(f"警告：找不到工具 '{tool_name}'")
        
        return resolved_tools
    
    @property
    def status_summary(self) -> Dict[str, Any]:
        """獲取 Agent 狀態摘要"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "type": self.agent_type.value,
            "state": self.state.value,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "success_rate": round(self.metrics.success_rate, 2),
                "avg_response_time": round(self.metrics.average_response_time, 2)
            },
            "tools_count": len(self.tools) if self.tools else 0,
            "memory_enabled": self.memory_manager is not None
        }
    
    def update_state(self, new_state: AgentState, context: Optional[Dict[str, Any]] = None):
        """更新 Agent 狀態"""
        old_state = self.state
        self.state = new_state
        
        # 記錄狀態變更
        state_change = {
            "timestamp": datetime.now().isoformat(),
            "from_state": old_state.value,
            "to_state": new_state.value,
            "context": context or {}
        }
        
        self.execution_history.append({
            "type": "state_change",
            "data": state_change
        })
        
        # 更新最後活動時間
        self.metrics.last_active = datetime.now()
    
    def execute_task_with_metrics(self, task_description: str, **kwargs) -> Dict[str, Any]:
        """
        執行任務並記錄指標
        
        Args:
            task_description: 任務描述
            **kwargs: 其他參數
            
        Returns:
            包含結果和指標的字典
        """
        start_time = time.time()
        self.update_state(AgentState.EXECUTING)
        
        try:
            # 執行任務
            result = self.execute(task_description, **kwargs)
            
            # 計算執行時間
            execution_time = time.time() - start_time
            
            # 更新指標
            self.metrics.tasks_completed += 1
            self.metrics.total_execution_time += execution_time
            self.metrics.average_response_time = (
                self.metrics.total_execution_time / 
                (self.metrics.tasks_completed + self.metrics.tasks_failed)
            )
            self.metrics.update_success_rate()
            
            # 記錄執行歷史
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "task_description": task_description,
                "execution_time": execution_time,
                "success": True,
                "result_length": len(str(result))
            }
            
            self.execution_history.append({
                "type": "task_execution",
                "data": execution_record
            })
            
            # 儲存到記憶系統
            if self.memory_manager:
                self.memory_manager.store_execution(
                    agent_id=self.agent_id,
                    task=task_description,
                    result=result,
                    metadata=execution_record
                )
            
            self.update_state(AgentState.COMPLETED)
            
            return {
                "result": result,
                "execution_time": execution_time,
                "success": True,
                "metrics": self.metrics
            }
            
        except Exception as e:
            # 處理錯誤
            execution_time = time.time() - start_time
            
            self.metrics.tasks_failed += 1
            self.metrics.update_success_rate()
            
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "task_description": task_description,
                "execution_time": execution_time,
                "success": False,
                "error": str(e)
            }
            
            self.execution_history.append({
                "type": "task_error",
                "data": error_record
            })
            
            self.update_state(AgentState.ERROR, {"error": str(e)})
            
            return {
                "result": None,
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "metrics": self.metrics
            }
    
    def get_execution_summary(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        獲取執行歷史摘要
        
        Args:
            limit: 限制返回的記錄數量
            
        Returns:
            執行歷史列表
        """
        history = self.execution_history
        if limit:
            history = history[-limit:]
        return history
    
    def reset_metrics(self):
        """重置指標"""
        self.metrics = AgentMetrics()
        self.execution_history = []
        self.update_state(AgentState.IDLE)
    
    def add_tool(self, tool: BaseTool):
        """動態添加工具"""
        if tool not in self.tools:
            self.tools.append(tool)
            self.tool_registry.register_tool(tool)
    
    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                self.tools.remove(tool)
                return True
        return False
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """獲取可用工具列表"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ] if self.tools else []
    
    def export_state(self) -> Dict[str, Any]:
        """匯出 Agent 狀態"""
        return {
            "agent_id": self.agent_id,
            "config": self.config.dict(),
            "state": self.state.value,
            "metrics": self.metrics.__dict__,
            "execution_history": self.execution_history,
            "available_tools": self.get_available_tools()
        }
    
    def import_state(self, state_data: Dict[str, Any]):
        """匯入 Agent 狀態"""
        self.agent_id = state_data.get("agent_id", self.agent_id)
        self.state = AgentState(state_data.get("state", AgentState.IDLE.value))
        
        # 還原指標
        metrics_data = state_data.get("metrics", {})
        for key, value in metrics_data.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        
        # 還原執行歷史
        self.execution_history = state_data.get("execution_history", [])


class SpecializedAgent(BaseAgent):
    """
    專業化 Agent 基礎類別
    
    為特定領域或功能提供專業化能力
    """
    
    def __init__(self, config: AgentConfig, specialization: str, tools: Optional[List[BaseTool]] = None):
        super().__init__(config, tools)
        self.specialization = specialization
        
        # 根據專業化調整配置
        self._customize_for_specialization()
    
    def _customize_for_specialization(self):
        """根據專業化自訂設定"""
        specialization_configs = {
            "data_analysis": {
                "reasoning": True,
                "required_tools": ["data_analysis", "visualization"]
            },
            "content_creation": {
                "reasoning": True,
                "required_tools": ["text_generation", "grammar_check"]
            },
            "research": {
                "memory": True,
                "required_tools": ["web_search", "document_analysis"]
            },
            "quality_assurance": {
                "reasoning": True,
                "required_tools": ["testing", "validation"]
            }
        }
        
        if self.specialization in specialization_configs:
            spec_config = specialization_configs[self.specialization]
            
            # 更新配置
            for key, value in spec_config.items():
                if key != "required_tools":
                    setattr(self.config, key, value)


# 工廠模式
class AgentFactory:
    """Agent 工廠類別"""
    
    @staticmethod
    def create_agent(agent_type: str, config: AgentConfig, tools: Optional[List[BaseTool]] = None) -> BaseAgent:
        """
        創建 Agent
        
        Args:
            agent_type: Agent 類型
            config: 配置
            tools: 工具列表
            
        Returns:
            Agent 實例
        """
        if agent_type == "specialized":
            specialization = config.llm_config.get("specialization", "general") if config.llm_config else "general"
            return SpecializedAgent(config, specialization, tools)
        else:
            return BaseAgent(config, tools)
    
    @staticmethod
    def create_worker_agent(role: str, goal: str, backstory: str, tools: Optional[List[BaseTool]] = None) -> BaseAgent:
        """創建工作者 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            agent_type=AgentType.WORKER,
            reasoning=True,
            memory=True
        )
        return BaseAgent(config, tools)
    
    @staticmethod
    def create_manager_agent(role: str, goal: str, backstory: str, tools: Optional[List[BaseTool]] = None) -> BaseAgent:
        """創建管理者 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            agent_type=AgentType.MANAGER,
            reasoning=True,
            memory=True,
            allow_delegation=True
        )
        return BaseAgent(config, tools)
    
    @staticmethod
    def create_specialist_agent(role: str, goal: str, backstory: str, specialization: str, tools: Optional[List[BaseTool]] = None) -> SpecializedAgent:
        """創建專家 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            agent_type=AgentType.SPECIALIST,
            reasoning=True,
            memory=True,
            llm_config={"specialization": specialization}
        )
        return SpecializedAgent(config, specialization, tools)


# 使用範例
if __name__ == "__main__":
    # 創建基礎配置
    config = AgentConfig(
        role="軟體架構師",
        goal="設計可擴展且高效的軟體系統",
        backstory="具備15年軟體開發經驗，專精於微服務架構和雲端技術"
    )
    
    # 創建 Agent
    architect = AgentFactory.create_specialist_agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        specialization="system_design"
    )
    
    # 執行任務
    result = architect.execute_task_with_metrics(
        "設計一個電商平台的微服務架構"
    )
    
    print("=== Agent 執行結果 ===")
    print(f"成功: {result['success']}")
    print(f"執行時間: {result['execution_time']:.2f}秒")
    print(f"Agent 狀態: {architect.status_summary}") 