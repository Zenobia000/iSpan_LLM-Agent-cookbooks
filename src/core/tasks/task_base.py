"""
CrewAI 核心 Task 基礎類別

基於 First Principles 設計：
1. Task = 明確定義的可執行工作單元
2. 每個 Task 都需要：描述、期望輸出、執行者、依賴關係
3. 可組合性原則：Task 可以組合成更複雜的工作流

參考文檔: docs/core/tasks_fundamentals.md
"""

# 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3

from typing import List, Dict, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json
import asyncio
from abc import ABC, abstractmethod

from crewai import Task, Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator

# 任務狀態
class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"

# 任務優先級
class TaskPriority(Enum):
    """任務優先級"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# 任務類型
class TaskType(Enum):
    """任務類型"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATION = "creation"
    COMMUNICATION = "communication"
    VALIDATION = "validation"
    COORDINATION = "coordination"

# 任務執行指標
@dataclass
class TaskMetrics:
    """任務執行指標"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_duration: Optional[float] = None
    retry_count: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    quality_score: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """成功率（基於重試次數）"""
        return 1.0 / (self.retry_count + 1)

# 任務配置
class TaskConfig(BaseModel):
    """任務配置模型"""
    
    # 基本屬性
    description: str = Field(..., description="任務描述")
    expected_output: str = Field(..., description="期望輸出")
    
    # 執行控制
    task_type: TaskType = Field(default=TaskType.ANALYSIS, description="任務類型")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="優先級")
    async_execution: bool = Field(default=False, description="是否異步執行")
    
    # 時間控制
    max_execution_time: int = Field(default=300, description="最大執行時間(秒)")
    deadline: Optional[datetime] = Field(default=None, description="截止時間")
    
    # 重試機制
    max_retries: int = Field(default=3, description="最大重試次數")
    retry_delay: int = Field(default=1, description="重試間隔(秒)")
    
    # 品質控制
    quality_threshold: float = Field(default=0.8, description="品質閾值")
    validation_required: bool = Field(default=False, description="是否需要驗證")
    
    # 其他配置
    tags: List[str] = Field(default_factory=list, description="標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("任務描述至少需要10個字符")
        return v.strip()
    
    @validator('expected_output')
    def validate_expected_output(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("期望輸出至少需要5個字符")
        return v.strip()

# 任務依賴關係
class TaskDependency:
    """任務依賴關係"""
    
    def __init__(self, task_id: str, dependency_type: str = "output"):
        self.task_id = task_id
        self.dependency_type = dependency_type  # output, completion, condition
        self.condition: Optional[Callable] = None
    
    def is_satisfied(self, task_results: Dict[str, Any]) -> bool:
        """檢查依賴是否滿足"""
        if self.task_id not in task_results:
            return False
        
        if self.dependency_type == "completion":
            return task_results[self.task_id].get("status") == "completed"
        elif self.dependency_type == "condition" and self.condition:
            return self.condition(task_results[self.task_id])
        
        return True

# 基礎任務包裝器
class BaseTask:
    """
    CrewAI 基礎 Task 包裝器
    
    First Principles:
    - Task 是最小的可執行工作單元
    - 必須有明確的輸入、處理邏輯和輸出
    - 應該是冪等的和可重複執行的
    
    Fundamentals:
    - 任務描述：清晰的工作定義
    - 執行控制：超時、重試、優先級
    - 依賴管理：任務間的順序和條件
    - 品質保證：驗證和評估機制
    """
    
    def __init__(self, config: TaskConfig, agent: Optional[Agent] = None, 
                 tools: Optional[List[BaseTool]] = None):
        """
        初始化基礎 Task
        
        Args:
            config: 任務配置
            agent: 執行 Agent
            tools: 任務專用工具
        """
        # 創建內部 CrewAI Task 實例
        self._crewai_task = Task(
            description=config.description,
            expected_output=config.expected_output,
            agent=agent,
            tools=tools or [],
            async_execution=config.async_execution
        )
        
        # 儲存配置和初始化狀態
        self.config = config
        self.task_id = str(uuid.uuid4())
        self.status = TaskStatus.PENDING
        self.metrics = TaskMetrics()
        
        # 依賴管理
        self.dependencies: List[TaskDependency] = []
        self.dependents: List[str] = []  # 依賴此任務的其他任務ID
        
        # 執行控制
        self.execution_context: Dict[str, Any] = {}
        self.validation_functions: List[Callable] = []
        self.callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_complete": [],
            "on_error": [],
            "on_retry": []
        }
        
        # 結果存儲
        self.result: Optional[Any] = None
        self.error: Optional[Exception] = None
        self.execution_history: List[Dict[str, Any]] = []
    
    # 代理 CrewAI Task 的屬性和方法
    @property
    def description(self):
        return self._crewai_task.description
    
    @property
    def expected_output(self):
        return self._crewai_task.expected_output
    
    @property
    def agent(self):
        return self._crewai_task.agent
    
    @property
    def tools(self):
        return self._crewai_task.tools
    
    def execute(self, context: Optional[Dict[str, Any]] = None):
        """執行 CrewAI Task"""
        return self._crewai_task.execute(context)
    
    async def execute_async(self, context: Optional[Dict[str, Any]] = None):
        """異步執行 CrewAI Task"""
        return await self._crewai_task.execute_async(context)
    
    def add_dependency(self, task_id: str, dependency_type: str = "output"):
        """添加任務依賴"""
        dependency = TaskDependency(task_id, dependency_type)
        self.dependencies.append(dependency)
    
    def add_validation(self, validation_func: Callable[[Any], bool]):
        """添加驗證函數"""
        self.validation_functions.append(validation_func)
    
    def add_callback(self, event: str, callback: Callable):
        """添加回調函數"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def check_dependencies(self, task_results: Dict[str, Any]) -> bool:
        """檢查所有依賴是否滿足"""
        return all(dep.is_satisfied(task_results) for dep in self.dependencies)
    
    def validate_output(self, output: Any) -> bool:
        """驗證輸出品質"""
        if not self.validation_functions:
            return True
        
        return all(validator(output) for validator in self.validation_functions)
    
    def execute_with_control(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        帶控制機制的任務執行
        
        Args:
            context: 執行上下文
            
        Returns:
            執行結果字典
        """
        self.execution_context.update(context or {})
        self.status = TaskStatus.RUNNING
        self.metrics.start_time = datetime.now()
        
        # 觸發開始回調
        self._trigger_callbacks("on_start")
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                # 執行任務
                if self.config.async_execution:
                    result = asyncio.run(self._execute_async())
                else:
                    result = self._execute_sync()
                
                # 驗證輸出
                if self.config.validation_required and not self.validate_output(result):
                    raise ValueError("輸出驗證失敗")
                
                # 成功完成
                self.result = result
                self.status = TaskStatus.COMPLETED
                self.metrics.end_time = datetime.now()
                self.metrics.execution_duration = (
                    self.metrics.end_time - self.metrics.start_time
                ).total_seconds()
                self.metrics.retry_count = retry_count
                
                # 記錄執行歷史
                self._record_execution("success", result)
                
                # 觸發完成回調
                self._trigger_callbacks("on_complete")
                
                return {
                    "task_id": self.task_id,
                    "status": "completed",
                    "result": result,
                    "metrics": self.metrics,
                    "execution_time": self.metrics.execution_duration
                }
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # 記錄錯誤
                self._record_execution("error", str(e))
                
                if retry_count <= self.config.max_retries:
                    # 觸發重試回調
                    self._trigger_callbacks("on_retry", {"attempt": retry_count, "error": e})
                    
                    # 等待重試間隔
                    if self.config.retry_delay > 0:
                        asyncio.sleep(self.config.retry_delay)
                else:
                    break
        
        # 所有重試都失敗
        self.error = last_error
        self.status = TaskStatus.FAILED
        self.metrics.end_time = datetime.now()
        self.metrics.retry_count = retry_count - 1
        
        # 觸發錯誤回調
        self._trigger_callbacks("on_error", {"error": last_error})
        
        return {
            "task_id": self.task_id,
            "status": "failed",
            "error": str(last_error),
            "metrics": self.metrics,
            "retry_count": retry_count - 1
        }
    
    def _execute_sync(self) -> Any:
        """同步執行"""
        return self.execute(self.execution_context)
    
    async def _execute_async(self) -> Any:
        """異步執行"""
        return await self.execute_async(self.execution_context)
    
    def _trigger_callbacks(self, event: str, data: Optional[Dict[str, Any]] = None):
        """觸發回調函數"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(self, data or {})
            except Exception as e:
                print(f"回調執行失敗: {e}")
    
    def _record_execution(self, status: str, result: Any):
        """記錄執行歷史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "result": str(result)[:1000],  # 限制長度
            "context": self.execution_context.copy()
        }
        self.execution_history.append(record)
    
    def cancel(self):
        """取消任務"""
        if self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            self.status = TaskStatus.CANCELLED
            self.metrics.end_time = datetime.now()
    
    def reset(self):
        """重置任務狀態"""
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.metrics = TaskMetrics()
        self.execution_history.clear()
    
    @property
    def is_ready(self) -> bool:
        """檢查任務是否準備執行"""
        return (self.status == TaskStatus.PENDING and 
                self._crewai_task.agent is not None)
    
    @property
    def is_completed(self) -> bool:
        """檢查任務是否已完成"""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """檢查任務是否失敗"""
        return self.status == TaskStatus.FAILED
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取任務摘要"""
        return {
            "task_id": self.task_id,
            "description": self.config.description[:100] + "..." if len(self.config.description) > 100 else self.config.description,
            "type": self.config.task_type.value,
            "priority": self.config.priority.value,
            "status": self.status.value,
            "agent": self._crewai_task.agent.role if self._crewai_task.agent else None,
            "dependencies": len(self.dependencies),
            "execution_time": self.metrics.execution_duration,
            "retry_count": self.metrics.retry_count,
            "quality_score": self.metrics.quality_score
        }
    
    def export_state(self) -> Dict[str, Any]:
        """匯出任務狀態"""
        return {
            "task_id": self.task_id,
            "config": self.config.dict(),
            "status": self.status.value,
            "metrics": self.metrics.__dict__,
            "execution_context": self.execution_context,
            "execution_history": self.execution_history,
            "result": self.result,
            "error": str(self.error) if self.error else None
        }

# 任務鏈管理器
class TaskChain:
    """任務鏈管理器"""
    
    def __init__(self):
        self.tasks: List[BaseTask] = []
        self.task_map: Dict[str, BaseTask] = {}
        self.execution_order: List[str] = []
    
    def add_task(self, task: BaseTask) -> str:
        """添加任務到鏈中"""
        self.tasks.append(task)
        self.task_map[task.task_id] = task
        return task.task_id
    
    def add_dependency(self, task_id: str, depends_on: str, dependency_type: str = "output"):
        """添加任務依賴關係"""
        if task_id in self.task_map and depends_on in self.task_map:
            self.task_map[task_id].add_dependency(depends_on, dependency_type)
            self.task_map[depends_on].dependents.append(task_id)
    
    def calculate_execution_order(self) -> List[str]:
        """計算任務執行順序（拓撲排序）"""
        # 簡化版拓撲排序
        in_degree = {task.task_id: len(task.dependencies) for task in self.tasks}
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 更新依賴此任務的其他任務
            for dependent_id in self.task_map[current].dependents:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        if len(result) != len(self.tasks):
            raise ValueError("任務依賴存在循環")
        
        self.execution_order = result
        return result
    
    def execute_chain(self) -> Dict[str, Any]:
        """執行整個任務鏈"""
        if not self.execution_order:
            self.calculate_execution_order()
        
        results = {}
        
        for task_id in self.execution_order:
            task = self.task_map[task_id]
            
            # 檢查依賴
            if not task.check_dependencies(results):
                results[task_id] = {
                    "status": "skipped",
                    "reason": "dependencies not satisfied"
                }
                continue
            
            # 執行任務
            result = task.execute_with_control({"chain_results": results})
            results[task_id] = result
            
            # 如果任務失敗且是關鍵任務，停止執行
            if result["status"] == "failed" and task.config.priority == TaskPriority.CRITICAL:
                break
        
        return results


# 任務工廠
class TaskFactory:
    """任務工廠類別"""
    
    @staticmethod
    def create_research_task(description: str, expected_output: str, **kwargs) -> BaseTask:
        """創建研究任務"""
        config = TaskConfig(
            description=description,
            expected_output=expected_output,
            task_type=TaskType.RESEARCH,
            **kwargs
        )
        return BaseTask(config)
    
    @staticmethod
    def create_analysis_task(description: str, expected_output: str, **kwargs) -> BaseTask:
        """創建分析任務"""
        config = TaskConfig(
            description=description,
            expected_output=expected_output,
            task_type=TaskType.ANALYSIS,
            **kwargs
        )
        return BaseTask(config)
    
    @staticmethod
    def create_creation_task(description: str, expected_output: str, **kwargs) -> BaseTask:
        """創建內容創作任務"""
        config = TaskConfig(
            description=description,
            expected_output=expected_output,
            task_type=TaskType.CREATION,
            **kwargs
        )
        return BaseTask(config)


# 使用範例
if __name__ == "__main__":
    # 創建任務配置
    config = TaskConfig(
        description="分析競爭對手的產品特性和市場定位",
        expected_output="包含競爭對手分析和市場機會的詳細報告",
        task_type=TaskType.RESEARCH,
        priority=TaskPriority.HIGH,
        max_execution_time=600
    )
    
    # 創建任務
    task = BaseTask(config)
    
    # 添加驗證函數
    def validate_analysis_output(output: str) -> bool:
        return len(output) > 500 and "競爭對手" in output
    
    task.add_validation(validate_analysis_output)
    
    # 創建任務鏈
    chain = TaskChain()
    task_id = chain.add_task(task)
    
    print(f"任務已創建，ID: {task_id}")
    print(f"任務摘要: {task.get_summary()}") 