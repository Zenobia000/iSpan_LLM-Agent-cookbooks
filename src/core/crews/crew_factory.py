"""
CrewAI 團隊工廠模組

基於 Multi-Agent Systems 設計原理：
1. Crew = 具備共同目標的 Agent 集合
2. 協作模式：順序執行、階層管理、平行處理
3. 工作流程：任務分配、進度監控、結果整合

參考文檔: docs/core/crews_fundamentals.md
"""

from typing import List, Dict, Optional, Any, Union, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import asyncio
import json

from crewai import Crew, Process, Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..agents.agent_base import BaseAgent, AgentConfig, AgentFactory
from ..tasks.task_base import BaseTask, TaskConfig, TaskChain
from ..memory.memory_manager import MemoryManager


class CrewProcess(Enum):
    """團隊協作流程"""
    SEQUENTIAL = "sequential"      # 順序執行
    HIERARCHICAL = "hierarchical"  # 階層管理
    CONSENSUS = "consensus"        # 共識決策
    PARALLEL = "parallel"          # 平行處理


class CrewStatus(Enum):
    """團隊狀態"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COORDINATING = "coordinating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CrewMetrics:
    """團隊執行指標"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    agent_utilization: Dict[str, float] = field(default_factory=dict)
    communication_count: int = 0
    coordination_overhead: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """任務成功率"""
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 0.0
    
    @property
    def average_agent_utilization(self) -> float:
        """平均 Agent 利用率"""
        if not self.agent_utilization:
            return 0.0
        return sum(self.agent_utilization.values()) / len(self.agent_utilization)


class CrewConfig(BaseModel):
    """團隊配置模型"""
    
    # 基本屬性
    name: str = Field(..., description="團隊名稱")
    description: str = Field(..., description="團隊描述")
    process: CrewProcess = Field(default=CrewProcess.SEQUENTIAL, description="協作流程")
    
    # 執行控制
    max_execution_time: int = Field(default=1800, description="最大執行時間(秒)")
    max_iterations: int = Field(default=1, description="最大迭代次數")
    verbose: bool = Field(default=True, description="詳細輸出")
    
    # 協作配置
    allow_delegation: bool = Field(default=True, description="允許任務委派")
    memory_enabled: bool = Field(default=True, description="啟用共享記憶")
    planning_enabled: bool = Field(default=False, description="啟用動態規劃")
    
    # 品質控制
    output_validation: bool = Field(default=False, description="啟用輸出驗證")
    consensus_threshold: float = Field(default=0.7, description="共識閾值")
    
    # 監控配置
    step_callback: Optional[str] = Field(default=None, description="步驟回調函數")
    task_callback: Optional[str] = Field(default=None, description="任務回調函數")
    
    # 元數據
    tags: List[str] = Field(default_factory=list, description="標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")


class BaseCrew(Crew):
    """
    CrewAI 基礎團隊類別
    
    First Principles:
    - Crew 是自組織的 Agent 集合
    - 必須有明確的協作機制和溝通協議
    - 應該能夠適應動態變化和處理衝突
    
    Fundamentals:
    - 成員管理：Agent 的添加、移除和角色分配
    - 任務分配：根據能力和負載分配任務
    - 協作機制：順序、階層、共識等不同模式
    - 品質保證：輸出驗證和共識決策
    """
    
    def __init__(self, config: CrewConfig, agents: List[BaseAgent], 
                 tasks: List[BaseTask], tools: Optional[List[BaseTool]] = None):
        """
        初始化基礎 Crew
        
        Args:
            config: 團隊配置
            agents: Agent 列表
            tasks: 任務列表
            tools: 共享工具
        """
        # 轉換為 CrewAI 所需的 Process 類型
        process_mapping = {
            CrewProcess.SEQUENTIAL: Process.sequential,
            CrewProcess.HIERARCHICAL: Process.hierarchical
        }
        
        # 呼叫父類別建構子
        super().__init__(
            agents=[agent for agent in agents],
            tasks=[task for task in tasks],
            process=process_mapping.get(config.process, Process.sequential),
            verbose=config.verbose,
            max_execution_time=config.max_execution_time,
            max_iter=config.max_iterations
        )
        
        # 儲存配置和狀態
        self.config = config
        self.crew_id = str(uuid.uuid4())
        self.status = CrewStatus.IDLE
        self.metrics = CrewMetrics()
        
        # 成員管理
        self.agent_registry: Dict[str, BaseAgent] = {
            agent.agent_id: agent for agent in agents
        }
        self.task_registry: Dict[str, BaseTask] = {
            task.task_id: task for task in tasks
        }
        
        # 協作機制
        self.shared_memory = MemoryManager() if config.memory_enabled else None
        self.communication_log: List[Dict[str, Any]] = []
        self.coordination_state: Dict[str, Any] = {}
        
        # 工具管理
        self.shared_tools = tools or []
        self._distribute_tools()
        
        # 執行歷史
        self.execution_history: List[Dict[str, Any]] = []
        self.iteration_results: List[Dict[str, Any]] = []
    
    def _distribute_tools(self):
        """分發共享工具給所有 Agent"""
        for agent in self.agents:
            for tool in self.shared_tools:
                if hasattr(agent, 'add_tool'):
                    agent.add_tool(tool)
    
    def add_agent(self, agent: BaseAgent, role: Optional[str] = None) -> str:
        """動態添加 Agent"""
        self.agents.append(agent)
        self.agent_registry[agent.agent_id] = agent
        
        # 分發共享工具
        for tool in self.shared_tools:
            if hasattr(agent, 'add_tool'):
                agent.add_tool(tool)
        
        # 記錄變更
        self._log_crew_change("agent_added", {
            "agent_id": agent.agent_id,
            "role": role or agent.role
        })
        
        return agent.agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        """移除 Agent"""
        if agent_id in self.agent_registry:
            agent = self.agent_registry[agent_id]
            
            # 從列表中移除
            if agent in self.agents:
                self.agents.remove(agent)
            
            # 從註冊表移除
            del self.agent_registry[agent_id]
            
            # 記錄變更
            self._log_crew_change("agent_removed", {
                "agent_id": agent_id,
                "role": agent.role
            })
            
            return True
        return False
    
    def add_task(self, task: BaseTask) -> str:
        """動態添加任務"""
        self.tasks.append(task)
        self.task_registry[task.task_id] = task
        
        # 記錄變更
        self._log_crew_change("task_added", {
            "task_id": task.task_id,
            "description": task.config.description[:100]
        })
        
        return task.task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """手動分配任務給特定 Agent"""
        if task_id in self.task_registry and agent_id in self.agent_registry:
            task = self.task_registry[task_id]
            agent = self.agent_registry[agent_id]
            
            task.agent = agent
            
            # 記錄分配
            self._log_communication({
                "type": "task_assignment",
                "from": "crew_manager",
                "to": agent_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
        return False
    
    def execute_with_monitoring(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        帶監控的團隊執行
        
        Args:
            inputs: 執行輸入
            
        Returns:
            執行結果
        """
        self.status = CrewStatus.PLANNING
        self.metrics.start_time = datetime.now()
        
        try:
            # 執行前規劃
            if self.config.planning_enabled:
                self._dynamic_planning()
            
            # 狀態轉換
            self.status = CrewStatus.EXECUTING
            
            # 執行團隊任務
            if self.config.process == CrewProcess.CONSENSUS:
                result = self._execute_with_consensus(inputs)
            elif self.config.process == CrewProcess.PARALLEL:
                result = self._execute_parallel(inputs)
            else:
                result = self.kickoff(inputs)
            
            # 記錄成功
            self.status = CrewStatus.COMPLETED
            self.metrics.end_time = datetime.now()
            self.metrics.total_execution_time = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            
            # 更新 Agent 利用率
            self._calculate_agent_utilization()
            
            # 儲存到共享記憶
            if self.shared_memory:
                asyncio.run(self.shared_memory.store_memory(
                    content={
                        "crew_execution": {
                            "crew_id": self.crew_id,
                            "result": result,
                            "metrics": self.metrics.__dict__
                        }
                    },
                    tags=["crew_execution", self.config.name]
                ))
            
            return {
                "crew_id": self.crew_id,
                "status": "completed",
                "result": result,
                "metrics": self.metrics.__dict__,
                "agent_count": len(self.agents),
                "task_count": len(self.tasks)
            }
            
        except Exception as e:
            # 處理執行錯誤
            self.status = CrewStatus.FAILED
            self.metrics.end_time = datetime.now()
            
            error_info = {
                "crew_id": self.crew_id,
                "status": "failed",
                "error": str(e),
                "metrics": self.metrics.__dict__
            }
            
            # 記錄錯誤
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "error",
                "data": error_info
            })
            
            return error_info
    
    def _execute_with_consensus(self, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """共識決策執行模式"""
        self.status = CrewStatus.COORDINATING
        
        # 收集所有 Agent 的初始建議
        proposals = []
        for agent in self.agents:
            if hasattr(agent, 'propose_solution'):
                proposal = agent.propose_solution(inputs)
                proposals.append({
                    "agent_id": agent.agent_id,
                    "proposal": proposal
                })
        
        # 進行共識決策
        consensus_result = self._reach_consensus(proposals)
        
        return consensus_result
    
    def _execute_parallel(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """平行執行模式"""
        async def execute_tasks_parallel():
            tasks_coroutines = []
            
            for task in self.tasks:
                if hasattr(task, 'execute_async'):
                    tasks_coroutines.append(task.execute_async(inputs))
                else:
                    # 將同步任務包裝為異步
                    async def sync_to_async(t, i):
                        return t.execute(i)
                    tasks_coroutines.append(sync_to_async(task, inputs))
            
            results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
            return dict(zip([task.task_id for task in self.tasks], results))
        
        return asyncio.run(execute_tasks_parallel())
    
    def _reach_consensus(self, proposals: List[Dict[str, Any]]) -> Any:
        """達成共識"""
        # 簡化的共識算法 - 實際應用中會更複雜
        if not proposals:
            return None
        
        # 如果只有一個提案，直接採用
        if len(proposals) == 1:
            return proposals[0]["proposal"]
        
        # 簡單投票機制（實際應該更複雜）
        return proposals[0]["proposal"]  # 暫時返回第一個提案
    
    def _dynamic_planning(self):
        """動態規劃"""
        # 分析當前任務負載
        task_complexity = self._analyze_task_complexity()
        
        # 評估 Agent 能力
        agent_capabilities = self._assess_agent_capabilities()
        
        # 重新分配任務（如果需要）
        self._rebalance_tasks(task_complexity, agent_capabilities)
    
    def _analyze_task_complexity(self) -> Dict[str, float]:
        """分析任務複雜度"""
        complexity_scores = {}
        
        for task in self.tasks:
            # 基於描述長度、期望輸出複雜度等估算
            description_complexity = len(task.config.description) / 1000
            output_complexity = len(task.config.expected_output) / 500
            
            complexity_scores[task.task_id] = min(
                description_complexity + output_complexity, 1.0
            )
        
        return complexity_scores
    
    def _assess_agent_capabilities(self) -> Dict[str, Dict[str, float]]:
        """評估 Agent 能力"""
        capabilities = {}
        
        for agent in self.agents:
            agent_capability = {
                "experience": agent.metrics.success_rate,
                "tools_count": len(agent.tools) if agent.tools else 0,
                "workload": 1.0 - (agent.metrics.success_rate or 0.5)  # 簡化計算
            }
            capabilities[agent.agent_id] = agent_capability
        
        return capabilities
    
    def _rebalance_tasks(self, task_complexity: Dict[str, float], 
                        agent_capabilities: Dict[str, Dict[str, float]]):
        """重新平衡任務分配"""
        # 簡化的任務重分配邏輯
        unassigned_tasks = [task for task in self.tasks if task.agent is None]
        
        for task in unassigned_tasks:
            # 找到最適合的 Agent
            best_agent = self._find_best_agent_for_task(task, agent_capabilities)
            if best_agent:
                task.agent = best_agent
    
    def _find_best_agent_for_task(self, task: BaseTask, 
                                 capabilities: Dict[str, Dict[str, float]]) -> Optional[BaseAgent]:
        """為任務找到最佳 Agent"""
        best_score = -1
        best_agent = None
        
        for agent_id, capability in capabilities.items():
            # 簡化的匹配算法
            score = capability["experience"] * 0.5 + capability["tools_count"] * 0.1
            
            if score > best_score:
                best_score = score
                best_agent = self.agent_registry[agent_id]
        
        return best_agent
    
    def _calculate_agent_utilization(self):
        """計算 Agent 利用率"""
        total_time = self.metrics.total_execution_time
        
        for agent in self.agents:
            if hasattr(agent, 'metrics') and agent.metrics.total_execution_time > 0:
                utilization = min(
                    agent.metrics.total_execution_time / total_time, 1.0
                ) if total_time > 0 else 0.0
                self.metrics.agent_utilization[agent.agent_id] = utilization
    
    def _log_communication(self, message: Dict[str, Any]):
        """記錄通訊"""
        self.communication_log.append(message)
        self.metrics.communication_count += 1
    
    def _log_crew_change(self, change_type: str, details: Dict[str, Any]):
        """記錄團隊變更"""
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": change_type,
            "details": details
        })
    
    def get_crew_status(self) -> Dict[str, Any]:
        """獲取團隊狀態"""
        return {
            "crew_id": self.crew_id,
            "name": self.config.name,
            "status": self.status.value,
            "agent_count": len(self.agents),
            "task_count": len(self.tasks),
            "process": self.config.process.value,
            "metrics": {
                "success_rate": self.metrics.success_rate,
                "avg_utilization": self.metrics.average_agent_utilization,
                "communication_count": self.metrics.communication_count
            },
            "shared_memory_enabled": self.shared_memory is not None
        }
    
    def export_execution_report(self) -> Dict[str, Any]:
        """匯出執行報告"""
        return {
            "crew_info": {
                "id": self.crew_id,
                "name": self.config.name,
                "description": self.config.description
            },
            "execution_summary": {
                "status": self.status.value,
                "start_time": self.metrics.start_time.isoformat() if self.metrics.start_time else None,
                "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                "total_time": self.metrics.total_execution_time,
                "success_rate": self.metrics.success_rate
            },
            "team_composition": [
                {
                    "agent_id": agent.agent_id,
                    "role": agent.role,
                    "utilization": self.metrics.agent_utilization.get(agent.agent_id, 0.0)
                }
                for agent in self.agents
            ],
            "task_summary": [
                {
                    "task_id": task.task_id,
                    "description": task.config.description[:100],
                    "status": task.status.value if hasattr(task, 'status') else "unknown",
                    "assigned_agent": task.agent.role if task.agent else None
                }
                for task in self.tasks
            ],
            "communication_stats": {
                "total_messages": len(self.communication_log),
                "coordination_overhead": self.metrics.coordination_overhead
            },
            "execution_history": self.execution_history
        }


class CrewFactory:
    """團隊工廠類別"""
    
    @staticmethod
    def create_research_crew(research_topic: str, **kwargs) -> BaseCrew:
        """創建研究團隊"""
        # 創建研究相關的 Agent
        researcher = AgentFactory.create_specialist_agent(
            role="研究員",
            goal=f"深入研究 {research_topic} 相關資訊",
            backstory="具備專業研究背景和資料分析能力",
            specialization="research"
        )
        
        analyst = AgentFactory.create_specialist_agent(
            role="資料分析師",
            goal="分析和整理研究資料",
            backstory="專精於數據分析和資訊整理",
            specialization="data_analysis"
        )
        
        writer = AgentFactory.create_specialist_agent(
            role="報告撰寫員",
            goal="撰寫專業研究報告",
            backstory="具備優秀的寫作和表達能力",
            specialization="content_creation"
        )
        
        # 創建任務
        research_task = BaseTask(TaskConfig(
            description=f"收集和整理關於 {research_topic} 的詳細資訊",
            expected_output="包含多個來源的綜合研究資料"
        ))
        research_task.agent = researcher
        
        analysis_task = BaseTask(TaskConfig(
            description="分析研究資料並找出關鍵洞察",
            expected_output="資料分析結果和重要發現"
        ))
        analysis_task.agent = analyst
        
        writing_task = BaseTask(TaskConfig(
            description="撰寫完整的研究報告",
            expected_output="結構完整的專業研究報告"
        ))
        writing_task.agent = writer
        
        # 設定任務依賴
        analysis_task.add_dependency(research_task.task_id)
        writing_task.add_dependency(analysis_task.task_id)
        
        # 創建團隊配置
        config = CrewConfig(
            name=f"{research_topic} 研究團隊",
            description=f"專門研究 {research_topic} 的專業團隊",
            process=CrewProcess.SEQUENTIAL,
            memory_enabled=True,
            **kwargs
        )
        
        return BaseCrew(
            config=config,
            agents=[researcher, analyst, writer],
            tasks=[research_task, analysis_task, writing_task]
        )
    
    @staticmethod
    def create_content_creation_crew(content_type: str, **kwargs) -> BaseCrew:
        """創建內容創作團隊"""
        # 創建內容創作相關的 Agent
        planner = AgentFactory.create_specialist_agent(
            role="內容策劃師",
            goal=f"策劃優質的 {content_type} 內容",
            backstory="具備豐富的內容策劃和創意發想經驗",
            specialization="planning"
        )
        
        creator = AgentFactory.create_specialist_agent(
            role="內容創作者",
            goal="創作高品質內容",
            backstory="擅長創作各種類型的內容",
            specialization="content_creation"
        )
        
        reviewer = AgentFactory.create_specialist_agent(
            role="品質審查員",
            goal="確保內容品質和準確性",
            backstory="具備專業的內容審查和編輯能力",
            specialization="quality_assurance"
        )
        
        # 創建任務鏈
        planning_task = BaseTask(TaskConfig(
            description=f"規劃 {content_type} 內容的結構和要點",
            expected_output="詳細的內容規劃和大綱"
        ))
        planning_task.agent = planner
        
        creation_task = BaseTask(TaskConfig(
            description="根據規劃創作內容",
            expected_output=f"完整的 {content_type} 內容"
        ))
        creation_task.agent = creator
        
        review_task = BaseTask(TaskConfig(
            description="審查和改進內容品質",
            expected_output="經過審查和優化的最終內容"
        ))
        review_task.agent = reviewer
        
        # 設定依賴關係
        creation_task.add_dependency(planning_task.task_id)
        review_task.add_dependency(creation_task.task_id)
        
        # 創建團隊配置
        config = CrewConfig(
            name=f"{content_type} 創作團隊",
            description=f"專門創作 {content_type} 內容的團隊",
            process=CrewProcess.SEQUENTIAL,
            output_validation=True,
            **kwargs
        )
        
        return BaseCrew(
            config=config,
            agents=[planner, creator, reviewer],
            tasks=[planning_task, creation_task, review_task]
        )
    
    @staticmethod
    def create_problem_solving_crew(problem_description: str, **kwargs) -> BaseCrew:
        """創建問題解決團隊"""
        # 創建問題解決相關的 Agent
        analyzer = AgentFactory.create_specialist_agent(
            role="問題分析師",
            goal="深入分析問題的根本原因",
            backstory="擅長問題分解和根因分析",
            specialization="analysis"
        )
        
        strategist = AgentFactory.create_specialist_agent(
            role="策略規劃師", 
            goal="制定解決問題的策略方案",
            backstory="具備豐富的策略規劃和方案設計經驗",
            specialization="planning"
        )
        
        implementer = AgentFactory.create_specialist_agent(
            role="方案執行者",
            goal="執行解決方案並監控結果",
            backstory="專精於方案執行和效果評估",
            specialization="execution"
        )
        
        # 創建協作任務
        analysis_task = BaseTask(TaskConfig(
            description=f"分析問題: {problem_description}",
            expected_output="問題分析報告，包含根本原因和影響範圍"
        ))
        analysis_task.agent = analyzer
        
        strategy_task = BaseTask(TaskConfig(
            description="制定問題解決策略",
            expected_output="詳細的解決方案和實施計劃"
        ))
        strategy_task.agent = strategist
        
        implementation_task = BaseTask(TaskConfig(
            description="執行解決方案",
            expected_output="執行結果和效果評估"
        ))
        implementation_task.agent = implementer
        
        # 設定依賴關係
        strategy_task.add_dependency(analysis_task.task_id)
        implementation_task.add_dependency(strategy_task.task_id)
        
        # 創建團隊配置
        config = CrewConfig(
            name="問題解決團隊",
            description=f"專門解決 '{problem_description}' 的團隊",
            process=CrewProcess.SEQUENTIAL,
            planning_enabled=True,
            **kwargs
        )
        
        return BaseCrew(
            config=config,
            agents=[analyzer, strategist, implementer],
            tasks=[analysis_task, strategy_task, implementation_task]
        )


# 使用範例
if __name__ == "__main__":
    # 創建研究團隊
    research_crew = CrewFactory.create_research_crew("人工智慧在教育領域的應用")
    
    # 執行團隊任務
    result = research_crew.execute_with_monitoring({
        "research_scope": "AI在教育領域的最新發展和應用案例"
    })
    
    print("=== 團隊執行結果 ===")
    print(f"狀態: {result['status']}")
    print(f"團隊ID: {result['crew_id']}")
    
    if result['status'] == 'completed':
        print(f"執行時間: {result['metrics']['total_execution_time']:.2f}秒")
        print(f"成功率: {result['metrics']['success_rate']:.2%}")
    
    # 獲取團隊狀態
    status = research_crew.get_crew_status()
    print(f"\n=== 團隊狀態 ===")
    print(f"團隊名稱: {status['name']}")
    print(f"成員數量: {status['agent_count']}")
    print(f"任務數量: {status['task_count']}")
    print(f"協作流程: {status['process']}") 