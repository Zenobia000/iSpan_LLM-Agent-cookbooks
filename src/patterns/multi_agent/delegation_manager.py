#!/usr/bin/env python3
"""
Multi-Agent Pattern: Delegation Manager
任務委派管理器 - 智能任務分解、代理分配和執行協調

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timedelta
import heapq


class TaskPriority(Enum):
    """任務優先級"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AgentStatus(Enum):
    """代理狀態"""
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class TaskRequest:
    """任務請求"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    task_type: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    required_capabilities: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """任務結果"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    assigned_agent: Optional[str] = None
    attempts: int = 1
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentProfile:
    """代理檔案"""
    agent_id: str
    name: str
    capabilities: Set[str]
    max_concurrent_tasks: int = 3
    performance_score: float = 1.0
    reliability_score: float = 1.0
    availability_schedule: Optional[Dict[str, Any]] = None
    current_load: int = 0
    status: AgentStatus = AgentStatus.IDLE
    last_seen: datetime = field(default_factory=datetime.now)
    task_history: List[str] = field(default_factory=list)
    
    @property
    def is_available(self) -> bool:
        """檢查代理是否可用"""
        return (
            self.status in [AgentStatus.IDLE, AgentStatus.BUSY] and
            self.current_load < self.max_concurrent_tasks
        )
    
    @property
    def load_factor(self) -> float:
        """負載因子"""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return self.current_load / self.max_concurrent_tasks


@dataclass
class DelegationResult:
    """委派結果"""
    task_id: str
    assigned_agent: str
    assignment_score: float
    estimated_completion_time: Optional[datetime] = None
    backup_agents: List[str] = field(default_factory=list)


class TaskDecomposer:
    """任務分解器"""
    
    def __init__(self):
        self.decomposition_strategies = {
            'sequential': self._sequential_decomposition,
            'parallel': self._parallel_decomposition,
            'hierarchical': self._hierarchical_decomposition,
            'pipeline': self._pipeline_decomposition
        }
    
    def decompose_task(
        self, 
        task: TaskRequest, 
        strategy: str = 'auto'
    ) -> List[TaskRequest]:
        """
        分解任務
        
        Args:
            task: 原始任務
            strategy: 分解策略
            
        Returns:
            分解後的子任務列表
        """
        if strategy == 'auto':
            strategy = self._determine_best_strategy(task)
        
        decomposition_func = self.decomposition_strategies.get(strategy)
        if not decomposition_func:
            # 如果無法分解，返回原任務
            return [task]
        
        try:
            subtasks = decomposition_func(task)
            # 為子任務設定依賴關係
            self._set_dependencies(subtasks, strategy)
            return subtasks
        except Exception as e:
            logging.warning(f"Task decomposition failed: {e}")
            return [task]
    
    def _sequential_decomposition(self, task: TaskRequest) -> List[TaskRequest]:
        """序列分解"""
        # 基於任務類型的序列分解邏輯
        if task.task_type == "data_analysis":
            return self._decompose_data_analysis(task)
        elif task.task_type == "content_generation":
            return self._decompose_content_generation(task)
        else:
            return self._generic_sequential_decomposition(task)
    
    def _parallel_decomposition(self, task: TaskRequest) -> List[TaskRequest]:
        """並行分解"""
        # 識別可並行執行的部分
        if "batch_processing" in task.description.lower():
            return self._decompose_batch_processing(task)
        return [task]
    
    def _hierarchical_decomposition(self, task: TaskRequest) -> List[TaskRequest]:
        """階層分解"""
        # 基於複雜度的階層分解
        complexity_level = self._assess_complexity(task)
        if complexity_level > 3:
            return self._create_hierarchical_subtasks(task)
        return [task]
    
    def _pipeline_decomposition(self, task: TaskRequest) -> List[TaskRequest]:
        """流水線分解"""
        # 創建流水線式的任務序列
        if "pipeline" in task.metadata:
            return self._create_pipeline_tasks(task)
        return [task]
    
    def _determine_best_strategy(self, task: TaskRequest) -> str:
        """確定最佳分解策略"""
        if task.estimated_duration and task.estimated_duration > timedelta(hours=1):
            return 'hierarchical'
        elif len(task.required_capabilities) > 3:
            return 'parallel'
        elif "sequential" in task.metadata:
            return 'sequential'
        else:
            return 'parallel'
    
    def _set_dependencies(self, subtasks: List[TaskRequest], strategy: str):
        """設定任務依賴關係"""
        if strategy == 'sequential':
            for i in range(1, len(subtasks)):
                subtasks[i].metadata['dependencies'] = [subtasks[i-1].task_id]
        elif strategy == 'hierarchical':
            # 第一個任務是主任務，其他任務依賴於它
            if len(subtasks) > 1:
                main_task = subtasks[0]
                for subtask in subtasks[1:]:
                    subtask.metadata['dependencies'] = [main_task.task_id]
    
    def _decompose_data_analysis(self, task: TaskRequest) -> List[TaskRequest]:
        """分解數據分析任務"""
        subtasks = []
        
        # 數據獲取
        data_fetch_task = TaskRequest(
            description="Fetch and validate data",
            task_type="data_fetch",
            priority=task.priority,
            required_capabilities=["data_access"],
            inputs=task.inputs,
            metadata={"parent_task": task.task_id}
        )
        subtasks.append(data_fetch_task)
        
        # 數據預處理
        preprocess_task = TaskRequest(
            description="Preprocess and clean data",
            task_type="data_preprocessing",
            priority=task.priority,
            required_capabilities=["data_processing"],
            metadata={"parent_task": task.task_id}
        )
        subtasks.append(preprocess_task)
        
        # 數據分析
        analysis_task = TaskRequest(
            description="Perform statistical analysis",
            task_type="statistical_analysis",
            priority=task.priority,
            required_capabilities=["statistics", "analysis"],
            metadata={"parent_task": task.task_id}
        )
        subtasks.append(analysis_task)
        
        return subtasks
    
    def _assess_complexity(self, task: TaskRequest) -> int:
        """評估任務複雜度"""
        complexity = 1
        complexity += len(task.required_capabilities)
        complexity += len(task.inputs) // 3
        if task.estimated_duration:
            complexity += task.estimated_duration.total_seconds() // 3600  # 每小時增加1點複雜度
        return int(complexity)


class AgentMatcher:
    """代理匹配器"""
    
    def __init__(self):
        self.matching_strategies = {
            'capability_based': self._capability_based_matching,
            'performance_based': self._performance_based_matching,
            'load_balanced': self._load_balanced_matching,
            'hybrid': self._hybrid_matching
        }
    
    def find_best_agent(
        self,
        task: TaskRequest,
        available_agents: List[AgentProfile],
        strategy: str = 'hybrid'
    ) -> Optional[DelegationResult]:
        """
        尋找最適合的代理
        
        Args:
            task: 任務請求
            available_agents: 可用代理列表
            strategy: 匹配策略
            
        Returns:
            委派結果或None
        """
        if not available_agents:
            return None
        
        # 過濾可用代理
        available_agents = [agent for agent in available_agents if agent.is_available]
        
        if not available_agents:
            return None
        
        matching_func = self.matching_strategies.get(strategy, self._hybrid_matching)
        return matching_func(task, available_agents)
    
    def _capability_based_matching(
        self, 
        task: TaskRequest, 
        agents: List[AgentProfile]
    ) -> Optional[DelegationResult]:
        """基於能力的匹配"""
        scored_agents = []
        
        for agent in agents:
            # 計算能力匹配分數
            required_caps = set(task.required_capabilities)
            agent_caps = agent.capabilities
            
            # 必須具備所有必需能力
            if not required_caps.issubset(agent_caps):
                continue
            
            # 計算能力覆蓋率
            coverage_score = len(required_caps & agent_caps) / max(len(required_caps), 1)
            
            # 額外能力獎勵
            extra_capabilities = len(agent_caps - required_caps)
            versatility_bonus = min(extra_capabilities * 0.1, 0.5)
            
            total_score = coverage_score + versatility_bonus
            scored_agents.append((agent, total_score))
        
        if not scored_agents:
            return None
        
        # 選擇最高分代理
        best_agent, score = max(scored_agents, key=lambda x: x[1])
        
        return DelegationResult(
            task_id=task.task_id,
            assigned_agent=best_agent.agent_id,
            assignment_score=score,
            backup_agents=[agent.agent_id for agent, _ in sorted(scored_agents, key=lambda x: x[1], reverse=True)[1:3]]
        )
    
    def _performance_based_matching(
        self, 
        task: TaskRequest, 
        agents: List[AgentProfile]
    ) -> Optional[DelegationResult]:
        """基於性能的匹配"""
        eligible_agents = []
        
        for agent in agents:
            required_caps = set(task.required_capabilities)
            if required_caps.issubset(agent.capabilities):
                # 綜合性能分數
                performance_score = (
                    agent.performance_score * 0.6 +
                    agent.reliability_score * 0.4
                )
                eligible_agents.append((agent, performance_score))
        
        if not eligible_agents:
            return None
        
        best_agent, score = max(eligible_agents, key=lambda x: x[1])
        
        return DelegationResult(
            task_id=task.task_id,
            assigned_agent=best_agent.agent_id,
            assignment_score=score
        )
    
    def _load_balanced_matching(
        self, 
        task: TaskRequest, 
        agents: List[AgentProfile]
    ) -> Optional[DelegationResult]:
        """基於負載均衡的匹配"""
        eligible_agents = []
        
        for agent in agents:
            required_caps = set(task.required_capabilities)
            if required_caps.issubset(agent.capabilities):
                # 負載分數（負載越低分數越高）
                load_score = 1.0 - agent.load_factor
                eligible_agents.append((agent, load_score))
        
        if not eligible_agents:
            return None
        
        best_agent, score = max(eligible_agents, key=lambda x: x[1])
        
        return DelegationResult(
            task_id=task.task_id,
            assigned_agent=best_agent.agent_id,
            assignment_score=score
        )
    
    def _hybrid_matching(
        self, 
        task: TaskRequest, 
        agents: List[AgentProfile]
    ) -> Optional[DelegationResult]:
        """混合策略匹配"""
        scored_agents = []
        
        for agent in agents:
            required_caps = set(task.required_capabilities)
            if not required_caps.issubset(agent.capabilities):
                continue
            
            # 能力匹配分數
            capability_score = len(required_caps & agent.capabilities) / max(len(required_caps), 1)
            
            # 性能分數
            performance_score = (agent.performance_score * 0.6 + agent.reliability_score * 0.4)
            
            # 負載分數
            load_score = 1.0 - agent.load_factor
            
            # 優先級調整
            priority_weight = {
                TaskPriority.CRITICAL: 1.2,
                TaskPriority.HIGH: 1.1,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.LOW: 0.9
            }.get(task.priority, 1.0)
            
            # 綜合分數
            total_score = (
                capability_score * 0.4 +
                performance_score * 0.4 +
                load_score * 0.2
            ) * priority_weight
            
            scored_agents.append((agent, total_score))
        
        if not scored_agents:
            return None
        
        best_agent, score = max(scored_agents, key=lambda x: x[1])
        
        return DelegationResult(
            task_id=task.task_id,
            assigned_agent=best_agent.agent_id,
            assignment_score=score,
            backup_agents=[agent.agent_id for agent, _ in sorted(scored_agents, key=lambda x: x[1], reverse=True)[1:3]]
        )


class DelegationManager:
    """
    任務委派管理器
    
    負責任務分解、代理匹配、任務分配和執行監控的核心組件。
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        default_timeout: timedelta = timedelta(minutes=30),
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化委派管理器
        
        Args:
            max_queue_size: 最大任務佇列大小
            default_timeout: 預設任務超時時間
            logger: 日誌記錄器
        """
        self.max_queue_size = max_queue_size
        self.default_timeout = default_timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # 核心組件
        self.task_decomposer = TaskDecomposer()
        self.agent_matcher = AgentMatcher()
        
        # 狀態管理
        self.agents: Dict[str, AgentProfile] = {}
        self.task_queue: List[Tuple[float, TaskRequest]] = []  # 優先級佇列
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        # 統計數據
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_completion_time': 0.0,
            'agent_utilization': {}
        }
        
        # 控制標誌
        self.running = False
        self._monitor_task = None
    
    def register_agent(self, agent: AgentProfile):
        """註冊代理"""
        self.agents[agent.agent_id] = agent
        self.stats['agent_utilization'][agent.agent_id] = 0.0
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
    
    def unregister_agent(self, agent_id: str):
        """註銷代理"""
        if agent_id in self.agents:
            # 重新分配該代理的任務
            self._reassign_agent_tasks(agent_id)
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def submit_task(self, task: TaskRequest) -> str:
        """
        提交任務
        
        Args:
            task: 任務請求
            
        Returns:
            任務ID
        """
        if len(self.task_queue) >= self.max_queue_size:
            raise ValueError("Task queue is full")
        
        # 任務分解
        subtasks = self.task_decomposer.decompose_task(task)
        
        # 將任務加入佇列
        for subtask in subtasks:
            priority_value = subtask.priority.value
            heapq.heappush(self.task_queue, (priority_value, subtask))
            self.stats['total_tasks'] += 1
        
        self.logger.info(f"Submitted task {task.task_id}, decomposed into {len(subtasks)} subtasks")
        return task.task_id
    
    async def start(self):
        """啟動委派管理器"""
        if self.running:
            return
        
        self.running = True
        self._monitor_task = asyncio.create_task(self._task_monitoring_loop())
        self.logger.info("Delegation manager started")
    
    async def stop(self):
        """停止委派管理器"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Delegation manager stopped")
    
    async def _task_monitoring_loop(self):
        """任務監控循環"""
        while self.running:
            try:
                # 分配任務
                await self._assign_pending_tasks()
                
                # 檢查超時任務
                await self._check_timeout_tasks()
                
                # 更新代理狀態
                self._update_agent_status()
                
                # 短暫等待
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in task monitoring loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _assign_pending_tasks(self):
        """分配待處理任務"""
        assigned_count = 0
        
        while self.task_queue and assigned_count < 10:  # 每次最多分配10個任務
            # 獲取最高優先級任務
            priority, task = heapq.heappop(self.task_queue)
            
            # 檢查依賴關係
            if not self._check_dependencies(task):
                # 依賴未滿足，重新加入佇列
                heapq.heappush(self.task_queue, (priority, task))
                break
            
            # 尋找合適的代理
            available_agents = [agent for agent in self.agents.values() if agent.is_available]
            delegation_result = self.agent_matcher.find_best_agent(task, available_agents)
            
            if delegation_result:
                # 分配任務
                await self._assign_task_to_agent(task, delegation_result.assigned_agent)
                assigned_count += 1
            else:
                # 無可用代理，重新加入佇列
                heapq.heappush(self.task_queue, (priority, task))
                break
    
    def _check_dependencies(self, task: TaskRequest) -> bool:
        """檢查任務依賴關係"""
        dependencies = task.metadata.get('dependencies', [])
        for dep_task_id in dependencies:
            if dep_task_id not in self.completed_tasks:
                return False
            if not self.completed_tasks[dep_task_id].success:
                return False
        return True
    
    async def _assign_task_to_agent(self, task: TaskRequest, agent_id: str):
        """將任務分配給代理"""
        if agent_id not in self.agents:
            self.logger.error(f"Agent {agent_id} not found")
            return
        
        agent = self.agents[agent_id]
        
        # 更新狀態
        task.metadata['assigned_at'] = datetime.now()
        task.metadata['assigned_agent'] = agent_id
        
        self.active_tasks[task.task_id] = task
        self.task_assignments[task.task_id] = agent_id
        
        # 更新代理負載
        agent.current_load += 1
        agent.status = AgentStatus.BUSY if agent.current_load > 0 else AgentStatus.IDLE
        
        self.logger.info(f"Assigned task {task.task_id} to agent {agent.name}")
        
        # 這裡應該實際調用代理執行任務
        # 在真實實現中，這會是對代理系統的 API 調用
        asyncio.create_task(self._simulate_task_execution(task, agent))
    
    async def _simulate_task_execution(self, task: TaskRequest, agent: AgentProfile):
        """模擬任務執行（在實際系統中會被真實的代理調用替代）"""
        try:
            # 模擬執行時間
            execution_time = task.estimated_duration.total_seconds() if task.estimated_duration else 10.0
            await asyncio.sleep(min(execution_time, 30.0))  # 最多等待30秒
            
            # 模擬成功結果
            result = TaskResult(
                task_id=task.task_id,
                success=True,
                result=f"Task {task.task_id} completed by {agent.name}",
                execution_time=execution_time,
                assigned_agent=agent.agent_id,
                completed_at=datetime.now()
            )
            
            await self.complete_task(result)
            
        except Exception as e:
            # 模擬失敗結果
            result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=e,
                assigned_agent=agent.agent_id,
                completed_at=datetime.now()
            )
            
            await self.complete_task(result)
    
    async def complete_task(self, result: TaskResult):
        """完成任務"""
        task_id = result.task_id
        
        if task_id not in self.active_tasks:
            self.logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        # 移除活動任務
        task = self.active_tasks.pop(task_id)
        agent_id = self.task_assignments.pop(task_id, None)
        
        # 更新代理狀態
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.current_load = max(0, agent.current_load - 1)
            agent.status = AgentStatus.BUSY if agent.current_load > 0 else AgentStatus.IDLE
            
            # 更新性能統計
            if result.success:
                agent.performance_score = min(1.0, agent.performance_score + 0.01)
            else:
                agent.performance_score = max(0.1, agent.performance_score - 0.05)
        
        # 保存結果
        self.completed_tasks[task_id] = result
        
        # 更新統計
        if result.success:
            self.stats['completed_tasks'] += 1
        else:
            self.stats['failed_tasks'] += 1
        
        self.logger.info(f"Task {task_id} completed: {'SUCCESS' if result.success else 'FAILED'}")
    
    async def _check_timeout_tasks(self):
        """檢查超時任務"""
        current_time = datetime.now()
        timeout_tasks = []
        
        for task_id, task in self.active_tasks.items():
            assigned_at = task.metadata.get('assigned_at')
            if assigned_at:
                timeout_limit = task.deadline or (assigned_at + self.default_timeout)
                if current_time > timeout_limit:
                    timeout_tasks.append(task_id)
        
        # 處理超時任務
        for task_id in timeout_tasks:
            await self._handle_timeout_task(task_id)
    
    async def _handle_timeout_task(self, task_id: str):
        """處理超時任務"""
        if task_id not in self.active_tasks:
            return
        
        task = self.active_tasks[task_id]
        agent_id = self.task_assignments.get(task_id)
        
        # 創建超時結果
        result = TaskResult(
            task_id=task_id,
            success=False,
            error=TimeoutError(f"Task {task_id} timed out"),
            assigned_agent=agent_id,
            completed_at=datetime.now()
        )
        
        await self.complete_task(result)
        
        # 如果有重試次數，重新提交任務
        if task.max_retries > 0:
            task.max_retries -= 1
            await self.submit_task(task)
    
    def _update_agent_status(self):
        """更新代理狀態"""
        current_time = datetime.now()
        
        for agent in self.agents.values():
            # 檢查代理是否長時間未響應
            if current_time - agent.last_seen > timedelta(minutes=5):
                if agent.status != AgentStatus.OFFLINE:
                    agent.status = AgentStatus.OFFLINE
                    self.logger.warning(f"Agent {agent.name} appears to be offline")
    
    def _reassign_agent_tasks(self, agent_id: str):
        """重新分配代理任務"""
        tasks_to_reassign = [
            task_id for task_id, assigned_agent_id in self.task_assignments.items()
            if assigned_agent_id == agent_id
        ]
        
        for task_id in tasks_to_reassign:
            if task_id in self.active_tasks:
                task = self.active_tasks.pop(task_id)
                self.task_assignments.pop(task_id, None)
                
                # 重新加入佇列
                priority = task.priority.value
                heapq.heappush(self.task_queue, (priority, task))
                
                self.logger.info(f"Reassigned task {task_id} due to agent {agent_id} unavailability")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        active_agents = len([a for a in self.agents.values() if a.status in [AgentStatus.IDLE, AgentStatus.BUSY]])
        
        return {
            'running': self.running,
            'total_agents': len(self.agents),
            'active_agents': active_agents,
            'pending_tasks': len(self.task_queue),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'statistics': self.stats.copy()
        }


# 使用範例
if __name__ == "__main__":
    async def main():
        # 創建委派管理器
        manager = DelegationManager()
        
        # 註冊代理
        analyst_agent = AgentProfile(
            agent_id="analyst_001",
            name="Data Analyst",
            capabilities={"data_analysis", "statistics", "reporting"}
        )
        
        writer_agent = AgentProfile(
            agent_id="writer_001", 
            name="Content Writer",
            capabilities={"writing", "content_generation", "editing"}
        )
        
        manager.register_agent(analyst_agent)
        manager.register_agent(writer_agent)
        
        # 啟動管理器
        await manager.start()
        
        # 提交任務
        analysis_task = TaskRequest(
            description="Analyze sales data and generate insights",
            task_type="data_analysis",
            priority=TaskPriority.HIGH,
            required_capabilities=["data_analysis", "statistics"],
            estimated_duration=timedelta(minutes=15)
        )
        
        task_id = await manager.submit_task(analysis_task)
        print(f"Submitted task: {task_id}")
        
        # 等待一段時間觀察執行
        await asyncio.sleep(20)
        
        # 獲取狀態
        status = manager.get_status()
        print(f"System status: {status}")
        
        # 停止管理器
        await manager.stop()
    
    asyncio.run(main()) 