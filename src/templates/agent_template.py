"""
CrewAI Agent 開發範本

本檔案提供標準化的 Agent 建立模式，涵蓋四大 Agentic Pattern：
- Reflection: 自我反思能力
- Planning: 任務規劃能力  
- Tool Use: 工具使用能力
- Multi-Agent: 協作溝通能力
"""

from typing import List, Dict, Optional, Any
from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent 配置模型"""
    
    role: str = Field(..., description="Agent 的角色定義")
    goal: str = Field(..., description="Agent 的目標")
    backstory: str = Field(..., description="Agent 的背景故事")
    reasoning: bool = Field(default=True, description="是否啟用推理功能")
    memory: bool = Field(default=True, description="是否啟用記憶功能") 
    allow_delegation: bool = Field(default=False, description="是否允許委派任務")
    max_iter: int = Field(default=3, description="最大迭代次數")
    tools: List[str] = Field(default_factory=list, description="工具清單")


class StandardAgent(Agent):
    """標準化 Agent 基礎類別"""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        """
        初始化標準 Agent
        
        Args:
            config: Agent 配置
            tools: 工具清單
        """
        super().__init__(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            reasoning=config.reasoning,
            memory=config.memory,
            allow_delegation=config.allow_delegation,
            max_iter=config.max_iter,
            tools=tools or [],
            verbose=True
        )
        
        self.config = config
        self.execution_history = []
        self.reflection_log = []


class ReflectionAgent(StandardAgent):
    """具備反思能力的 Agent"""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        super().__init__(config, tools)
        self.quality_threshold = 8.0
        self.max_reflections = 3
    
    def reflect_on_output(self, output: str, context: str = "") -> Dict[str, Any]:
        """
        對輸出進行反思評估
        
        Args:
            output: 要評估的輸出
            context: 評估上下文
            
        Returns:
            反思結果字典
        """
        reflection_prompt = f"""
        請評估以下輸出的品質：
        
        輸出內容: {output}
        上下文: {context}
        
        評估維度：
        1. 準確性 (0-10分)
        2. 清晰度 (0-10分)
        3. 完整性 (0-10分)
        4. 實用性 (0-10分)
        
        請提供：
        - 各維度評分
        - 總分 (平均分)
        - 具體改進建議
        - 是否需要重新執行 (true/false)
        """
        
        # 這裡可以調用 LLM 進行評估
        reflection_result = {
            "accuracy_score": 8.5,
            "clarity_score": 7.8,
            "completeness_score": 8.2,
            "usefulness_score": 8.0,
            "overall_score": 8.1,
            "improvement_suggestions": [
                "增加更多具體範例",
                "改善表達清晰度",
                "補充缺失的技術細節"
            ],
            "needs_refinement": False
        }
        
        self.reflection_log.append(reflection_result)
        return reflection_result
    
    def iterative_refinement(self, initial_output: str, max_iterations: int = 3) -> str:
        """
        迭代式改進輸出
        
        Args:
            initial_output: 初始輸出
            max_iterations: 最大迭代次數
            
        Returns:
            改進後的最終輸出
        """
        current_output = initial_output
        
        for iteration in range(max_iterations):
            reflection = self.reflect_on_output(current_output)
            
            if reflection["overall_score"] >= self.quality_threshold:
                break
            
            # 基於反思結果改進輸出
            refinement_prompt = f"""
            原始輸出: {current_output}
            
            改進建議: {reflection["improvement_suggestions"]}
            
            請基於以上建議改進輸出內容，提升品質。
            """
            
            # 這裡調用 LLM 進行改進
            current_output = self.execute(refinement_prompt)
        
        return current_output


class PlanningAgent(StandardAgent):
    """具備規劃能力的 Agent"""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        super().__init__(config, tools)
        self.planning_strategy = "work_breakdown_structure"
    
    def create_plan(self, goal: str, constraints: Optional[Dict] = None) -> List[Dict]:
        """
        創建執行計劃
        
        Args:
            goal: 目標描述
            constraints: 約束條件
            
        Returns:
            任務計劃列表
        """
        planning_prompt = f"""
        目標: {goal}
        約束條件: {constraints or "無特殊約束"}
        
        請創建詳細的執行計劃，包含：
        1. 任務分解 (Work Breakdown Structure)
        2. 任務優先級
        3. 預估時間
        4. 所需資源
        5. 依賴關係
        
        請以 JSON 格式返回計劃。
        """
        
        # 這裡調用 LLM 生成計劃
        plan = [
            {
                "task_id": "task_1",
                "name": "需求分析",
                "description": "分析並明確化需求",
                "priority": "high", 
                "estimated_time": "2 hours",
                "dependencies": [],
                "resources": ["業務分析師"]
            },
            {
                "task_id": "task_2", 
                "name": "技術設計",
                "description": "設計技術架構",
                "priority": "high",
                "estimated_time": "4 hours", 
                "dependencies": ["task_1"],
                "resources": ["系統架構師"]
            }
        ]
        
        return plan
    
    def monitor_progress(self, plan: List[Dict], current_status: Dict) -> Dict:
        """
        監控執行進度
        
        Args:
            plan: 執行計劃
            current_status: 當前狀態
            
        Returns:
            進度報告
        """
        completed_tasks = sum(1 for task in plan if current_status.get(task["task_id"]) == "completed")
        total_tasks = len(plan)
        progress_percentage = (completed_tasks / total_tasks) * 100
        
        return {
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "progress_percentage": progress_percentage,
            "status": "on_track" if progress_percentage >= 50 else "behind_schedule"
        }


class ToolUseAgent(StandardAgent):
    """具備工具使用能力的 Agent"""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        super().__init__(config, tools)
        self.tool_usage_log = []
        self.fallback_strategies = {}
    
    def execute_with_tools(self, task: str, preferred_tools: Optional[List[str]] = None) -> str:
        """
        使用工具執行任務
        
        Args:
            task: 任務描述
            preferred_tools: 偏好使用的工具
            
        Returns:
            執行結果
        """
        available_tools = [tool.name for tool in self.tools] if self.tools else []
        
        if preferred_tools:
            # 檢查偏好工具是否可用
            usable_tools = [tool for tool in preferred_tools if tool in available_tools]
        else:
            usable_tools = available_tools
        
        execution_log = {
            "task": task,
            "attempted_tools": [],
            "successful_tool": None,
            "result": None,
            "errors": []
        }
        
        for tool_name in usable_tools:
            try:
                tool = next(tool for tool in self.tools if tool.name == tool_name)
                result = tool.run(task)
                
                execution_log["attempted_tools"].append(tool_name)
                execution_log["successful_tool"] = tool_name
                execution_log["result"] = result
                
                self.tool_usage_log.append(execution_log)
                return result
                
            except Exception as e:
                execution_log["attempted_tools"].append(tool_name)
                execution_log["errors"].append(f"{tool_name}: {str(e)}")
                continue
        
        # 如果所有工具都失敗，使用 fallback 策略
        fallback_result = self.execute_fallback_strategy(task)
        execution_log["result"] = fallback_result
        self.tool_usage_log.append(execution_log)
        
        return fallback_result
    
    def execute_fallback_strategy(self, task: str) -> str:
        """
        執行備用策略
        
        Args:
            task: 任務描述
            
        Returns:
            備用策略執行結果
        """
        return f"使用備用策略處理任務: {task}"
    
    def analyze_tool_performance(self) -> Dict[str, Any]:
        """
        分析工具使用效能
        
        Returns:
            效能分析報告
        """
        if not self.tool_usage_log:
            return {"message": "暫無工具使用記錄"}
        
        tool_success_rate = {}
        tool_usage_count = {}
        
        for log in self.tool_usage_log:
            for tool in log["attempted_tools"]:
                tool_usage_count[tool] = tool_usage_count.get(tool, 0) + 1
                
                if tool == log["successful_tool"]:
                    tool_success_rate[tool] = tool_success_rate.get(tool, 0) + 1
        
        # 計算成功率
        performance_report = {}
        for tool, usage_count in tool_usage_count.items():
            success_count = tool_success_rate.get(tool, 0)
            performance_report[tool] = {
                "usage_count": usage_count,
                "success_count": success_count,
                "success_rate": (success_count / usage_count) * 100
            }
        
        return performance_report


class CollaborativeAgent(StandardAgent):
    """具備協作能力的 Agent"""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[BaseTool]] = None):
        config.allow_delegation = True  # 啟用委派功能
        super().__init__(config, tools)
        self.collaboration_log = []
        self.peer_agents = []
    
    def register_peers(self, agents: List[Agent]):
        """
        註冊合作夥伴 Agent
        
        Args:
            agents: 合作夥伴 Agent 列表
        """
        self.peer_agents = agents
    
    def delegate_task(self, task: str, target_agent: Optional[str] = None) -> str:
        """
        委派任務給其他 Agent
        
        Args:
            task: 要委派的任務
            target_agent: 目標 Agent (可選)
            
        Returns:
            委派結果
        """
        if not self.peer_agents:
            return "沒有可用的合作夥伴 Agent"
        
        # 選擇最適合的 Agent
        if target_agent:
            selected_agent = next(
                (agent for agent in self.peer_agents if agent.role == target_agent), 
                None
            )
        else:
            selected_agent = self.select_best_agent_for_task(task)
        
        if not selected_agent:
            return "找不到適合的 Agent 執行任務"
        
        # 記錄協作
        collaboration_record = {
            "delegator": self.role,
            "delegate": selected_agent.role,
            "task": task,
            "timestamp": "2025-01-01T00:00:00Z"  # 實際應使用當前時間
        }
        
        self.collaboration_log.append(collaboration_record)
        
        return f"任務已委派給 {selected_agent.role}: {task}"
    
    def select_best_agent_for_task(self, task: str) -> Optional[Agent]:
        """
        為任務選擇最適合的 Agent
        
        Args:
            task: 任務描述
            
        Returns:
            最適合的 Agent
        """
        # 這裡可以實作更複雜的選擇邏輯
        # 例如基於 Agent 的專長、歷史表現等
        
        if "分析" in task or "研究" in task:
            return next((agent for agent in self.peer_agents if "分析師" in agent.role), None)
        elif "撰寫" in task or "編輯" in task:
            return next((agent for agent in self.peer_agents if "寫手" in agent.role), None)
        else:
            return self.peer_agents[0] if self.peer_agents else None
    
    def request_assistance(self, question: str, expert_type: Optional[str] = None) -> str:
        """
        向專家 Agent 請求協助
        
        Args:
            question: 問題描述
            expert_type: 專家類型
            
        Returns:
            專家回應
        """
        if expert_type:
            expert = next(
                (agent for agent in self.peer_agents if expert_type in agent.role),
                None
            )
        else:
            expert = self.peer_agents[0] if self.peer_agents else None
        
        if not expert:
            return "找不到相關專家"
        
        # 記錄求助
        assistance_record = {
            "requester": self.role,
            "expert": expert.role,
            "question": question,
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
        self.collaboration_log.append(assistance_record)
        
        return f"已向 {expert.role} 專家諮詢: {question}"


# 工廠模式創建 Agent
class AgentFactory:
    """Agent 工廠類別"""
    
    @staticmethod
    def create_reflection_agent(role: str, goal: str, backstory: str) -> ReflectionAgent:
        """創建反思型 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal, 
            backstory=backstory,
            reasoning=True,
            memory=True
        )
        return ReflectionAgent(config)
    
    @staticmethod
    def create_planning_agent(role: str, goal: str, backstory: str) -> PlanningAgent:
        """創建規劃型 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            reasoning=True,
            memory=True
        )
        return PlanningAgent(config)
    
    @staticmethod
    def create_tool_agent(role: str, goal: str, backstory: str, tools: List[BaseTool]) -> ToolUseAgent:
        """創建工具型 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            reasoning=True,
            memory=True
        )
        return ToolUseAgent(config, tools)
    
    @staticmethod
    def create_collaborative_agent(role: str, goal: str, backstory: str) -> CollaborativeAgent:
        """創建協作型 Agent"""
        config = AgentConfig(
            role=role,
            goal=goal,
            backstory=backstory,
            reasoning=True,
            memory=True,
            allow_delegation=True
        )
        return CollaborativeAgent(config)


# 使用範例
if __name__ == "__main__":
    # 創建反思型內容創作 Agent
    content_creator = AgentFactory.create_reflection_agent(
        role="技術內容創作專家",
        goal="創作高品質的技術文章和教學內容",
        backstory="擁有10年技術寫作經驗，專精於 AI 和軟體開發領域"
    )
    
    # 創建規劃型專案經理 Agent
    project_manager = AgentFactory.create_planning_agent(
        role="AI 專案經理",
        goal="規劃和管理 AI 專案的完整生命週期",
        backstory="具備豐富的 AI 專案管理經驗，擅長將複雜目標分解為可執行的任務"
    )
    
    # 展示使用方式
    print("=== Agent 範本示例 ===")
    print(f"內容創作專家: {content_creator.role}")
    print(f"專案經理: {project_manager.role}")
    
    # 展示反思功能
    sample_output = "這是一篇關於 CrewAI 的技術文章..."
    reflection_result = content_creator.reflect_on_output(sample_output)
    print(f"反思評分: {reflection_result['overall_score']}")
    
    # 展示規劃功能
    sample_plan = project_manager.create_plan("開發一個 CrewAI 教學專案")
    print(f"生成計劃包含 {len(sample_plan)} 個任務") 