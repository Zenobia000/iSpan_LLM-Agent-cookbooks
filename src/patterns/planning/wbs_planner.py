"""
Planning Pattern: 工作分解結構（WBS）規劃器

基於項目管理的 First Principles 設計：
1. 分解原理：複雜任務可以分解為可管理的子任務
2. 階層結構：任務之間存在層次和依賴關係
3. 動態調整：計劃應該能夠根據執行情況動態調整

參考文檔: docs/patterns/planning.md
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import json
from datetime import datetime, timedelta
import networkx as nx
from pathlib import Path

from crewai import Agent, Task
from pydantic import BaseModel, Field

from ...core.agents.agent_base import BaseAgent
from ...core.tasks.task_base import BaseTask, TaskConfig


class TaskPriority(Enum):
    """任務優先級"""
    CRITICAL = 1    # 關鍵路徑任務
    HIGH = 2        # 高優先級
    MEDIUM = 3      # 中等優先級
    LOW = 4         # 低優先級


class TaskComplexity(Enum):
    """任務複雜度"""
    SIMPLE = "simple"           # 簡單任務：1-2小時完成
    MODERATE = "moderate"       # 中等任務：半天-1天完成
    COMPLEX = "complex"         # 複雜任務：數天完成
    VERY_COMPLEX = "very_complex"  # 非常複雜：需要進一步分解


class DependencyType(Enum):
    """依賴關係類型"""
    FINISH_TO_START = "FS"      # 前置任務完成後才能開始
    START_TO_START = "SS"       # 前置任務開始後才能開始
    FINISH_TO_FINISH = "FF"     # 前置任務完成後才能完成
    START_TO_FINISH = "SF"      # 前置任務開始後才能完成


@dataclass
class TaskDependency:
    """任務依賴關係"""
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_time: int = 0  # 延遲時間（小時）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "predecessor_id": self.predecessor_id,
            "successor_id": self.successor_id,
            "dependency_type": self.dependency_type.value,
            "lag_time": self.lag_time
        }


@dataclass
class WBSNode:
    """WBS 節點"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    level: int = 0  # WBS 層級：0=項目，1=主要階段，2=工作包，3=活動
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # 任務屬性
    estimated_hours: Optional[float] = None
    complexity: TaskComplexity = TaskComplexity.MODERATE
    priority: TaskPriority = TaskPriority.MEDIUM
    skills_required: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    
    # 狀態
    status: str = "planned"  # planned, in_progress, completed, cancelled
    actual_hours: Optional[float] = None
    completion_percentage: float = 0.0
    
    # 時間
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # 元數據
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    @property
    def is_leaf(self) -> bool:
        """是否為葉子節點（最小工作單元）"""
        return len(self.children_ids) == 0
    
    @property
    def wbs_code(self) -> str:
        """WBS 編碼（如：1.2.3）"""
        # 簡化實作，實際應該根據層次結構生成
        return f"{self.level}.{self.id[:4]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "estimated_hours": self.estimated_hours,
            "complexity": self.complexity.value,
            "priority": self.priority.value,
            "skills_required": self.skills_required,
            "resources_needed": self.resources_needed,
            "status": self.status,
            "actual_hours": self.actual_hours,
            "completion_percentage": self.completion_percentage,
            "planned_start": self.planned_start.isoformat() if self.planned_start else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
            "wbs_code": self.wbs_code
        }


class DecompositionStrategy(ABC):
    """任務分解策略抽象基類"""
    
    @abstractmethod
    def decompose(self, task_description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """分解任務為子任務"""
        pass
    
    @abstractmethod
    def estimate_effort(self, node: WBSNode, context: Dict[str, Any]) -> float:
        """估算任務工作量"""
        pass


class FunctionalDecomposition(DecompositionStrategy):
    """功能分解策略：按功能模組分解"""
    
    def decompose(self, task_description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """按功能模組分解任務"""
        project_type = context.get("project_type", "general")
        
        if project_type == "software_development":
            return self._decompose_software_project(task_description, context)
        elif project_type == "content_creation":
            return self._decompose_content_project(task_description, context)
        elif project_type == "research":
            return self._decompose_research_project(task_description, context)
        else:
            return self._decompose_general_project(task_description, context)
    
    def _decompose_software_project(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """軟體開發項目分解"""
        phases = [
            ("需求分析", "分析和定義系統需求", ["業務分析", "系統分析"]),
            ("設計階段", "設計系統架構和介面", ["架構設計", "UI/UX設計"]),
            ("開發實作", "編碼實現系統功能", ["前端開發", "後端開發", "資料庫"]),
            ("測試驗證", "測試系統功能和性能", ["單元測試", "整合測試", "系統測試"]),
            ("部署上線", "部署到生產環境", ["環境配置", "部署腳本", "監控設定"])
        ]
        
        nodes = []
        for i, (name, desc, skills) in enumerate(phases):
            node = WBSNode(
                name=name,
                description=desc,
                level=1,
                complexity=TaskComplexity.COMPLEX,
                priority=TaskPriority.HIGH if i < 3 else TaskPriority.MEDIUM,
                skills_required=skills,
                estimated_hours=40.0 + i * 20  # 估算工時
            )
            nodes.append(node)
        
        return nodes
    
    def _decompose_content_project(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """內容創作項目分解"""
        phases = [
            ("內容策劃", "規劃內容主題和結構", ["內容策略", "主題研究"]),
            ("資料收集", "收集相關資料和素材", ["資料研究", "素材準備"]),
            ("內容創作", "撰寫和製作內容", ["寫作", "編輯", "設計"]),
            ("審查優化", "審查和優化內容品質", ["校對", "SEO優化"]),
            ("發布推廣", "發布內容並進行推廣", ["發布管理", "社群推廣"])
        ]
        
        nodes = []
        for i, (name, desc, skills) in enumerate(phases):
            node = WBSNode(
                name=name,
                description=desc,
                level=1,
                complexity=TaskComplexity.MODERATE,
                priority=TaskPriority.HIGH if i < 3 else TaskPriority.MEDIUM,
                skills_required=skills,
                estimated_hours=16.0 + i * 8
            )
            nodes.append(node)
        
        return nodes
    
    def _decompose_research_project(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """研究項目分解"""
        phases = [
            ("文獻回顧", "回顧相關研究文獻", ["研究方法", "文獻分析"]),
            ("研究設計", "設計研究方法和流程", ["實驗設計", "數據收集"]),
            ("數據收集", "收集和整理研究數據", ["數據收集", "數據清理"]),
            ("數據分析", "分析研究數據和結果", ["統計分析", "數據視覺化"]),
            ("報告撰寫", "撰寫研究報告和論文", ["學術寫作", "報告製作"])
        ]
        
        nodes = []
        for i, (name, desc, skills) in enumerate(phases):
            node = WBSNode(
                name=name,
                description=desc,
                level=1,
                complexity=TaskComplexity.COMPLEX if i in [1, 3] else TaskComplexity.MODERATE,
                priority=TaskPriority.HIGH,
                skills_required=skills,
                estimated_hours=32.0 + i * 16
            )
            nodes.append(node)
        
        return nodes
    
    def _decompose_general_project(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """通用項目分解"""
        phases = [
            ("項目啟動", "定義項目範圍和目標", ["項目管理"]),
            ("計劃制定", "制定詳細執行計劃", ["規劃", "資源分配"]),
            ("執行實施", "執行項目主要工作", ["執行管理"]),
            ("監控控制", "監控進度和品質", ["監控", "品質管理"]),
            ("項目收尾", "完成項目並總結經驗", ["交付", "總結"])
        ]
        
        nodes = []
        for i, (name, desc, skills) in enumerate(phases):
            node = WBSNode(
                name=name,
                description=desc,
                level=1,
                complexity=TaskComplexity.MODERATE,
                priority=TaskPriority.MEDIUM,
                skills_required=skills,
                estimated_hours=24.0
            )
            nodes.append(node)
        
        return nodes
    
    def estimate_effort(self, node: WBSNode, context: Dict[str, Any]) -> float:
        """估算任務工作量"""
        base_hours = {
            TaskComplexity.SIMPLE: 4.0,
            TaskComplexity.MODERATE: 16.0,
            TaskComplexity.COMPLEX: 40.0,
            TaskComplexity.VERY_COMPLEX: 80.0
        }
        
        # 基礎工時
        estimated_hours = base_hours[node.complexity]
        
        # 技能複雜度調整
        skill_multiplier = 1.0 + (len(node.skills_required) - 1) * 0.2
        estimated_hours *= skill_multiplier
        
        # 優先級調整（高優先級任務可能需要更多品質保證時間）
        if node.priority == TaskPriority.CRITICAL:
            estimated_hours *= 1.3
        elif node.priority == TaskPriority.HIGH:
            estimated_hours *= 1.1
        
        return estimated_hours


class TemporalDecomposition(DecompositionStrategy):
    """時間分解策略：按時間階段分解"""
    
    def decompose(self, task_description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """按時間階段分解任務"""
        duration_weeks = context.get("duration_weeks", 4)
        
        if duration_weeks <= 1:
            return self._create_daily_breakdown(task_description, context)
        elif duration_weeks <= 4:
            return self._create_weekly_breakdown(task_description, context)
        else:
            return self._create_monthly_breakdown(task_description, context)
    
    def _create_weekly_breakdown(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """週次分解"""
        weeks = context.get("duration_weeks", 4)
        
        nodes = []
        for week in range(1, weeks + 1):
            node = WBSNode(
                name=f"第 {week} 週",
                description=f"第 {week} 週的工作安排",
                level=1,
                complexity=TaskComplexity.MODERATE,
                priority=TaskPriority.MEDIUM,
                estimated_hours=40.0  # 一週工作時數
            )
            nodes.append(node)
        
        return nodes
    
    def _create_daily_breakdown(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """日次分解"""
        days = context.get("duration_days", 5)
        
        nodes = []
        for day in range(1, days + 1):
            node = WBSNode(
                name=f"第 {day} 天",
                description=f"第 {day} 天的工作安排",
                level=1,
                complexity=TaskComplexity.SIMPLE,
                priority=TaskPriority.MEDIUM,
                estimated_hours=8.0  # 一天工作時數
            )
            nodes.append(node)
        
        return nodes
    
    def _create_monthly_breakdown(self, description: str, context: Dict[str, Any]) -> List[WBSNode]:
        """月份分解"""
        months = (context.get("duration_weeks", 12) + 3) // 4
        
        nodes = []
        for month in range(1, months + 1):
            node = WBSNode(
                name=f"第 {month} 個月",
                description=f"第 {month} 個月的工作安排",
                level=1,
                complexity=TaskComplexity.COMPLEX,
                priority=TaskPriority.MEDIUM,
                estimated_hours=160.0  # 一個月工作時數
            )
            nodes.append(node)
        
        return nodes
    
    def estimate_effort(self, node: WBSNode, context: Dict[str, Any]) -> float:
        """基於時間估算工作量"""
        return node.estimated_hours or 8.0


class WBSPlanner:
    """
    工作分解結構規劃器
    
    核心功能：
    1. 任務分解：將複雜任務分解為可管理的子任務
    2. 依賴分析：識別任務間的依賴關係
    3. 資源分配：合理分配人力和物力資源
    4. 時程規劃：制定合理的時間計劃
    5. 風險評估：識別和評估項目風險
    """
    
    def __init__(self):
        self.strategies: Dict[str, DecompositionStrategy] = {
            "functional": FunctionalDecomposition(),
            "temporal": TemporalDecomposition(),
        }
        
        self.wbs_nodes: Dict[str, WBSNode] = {}
        self.dependencies: List[TaskDependency] = []
        self.project_graph = nx.DiGraph()
        
        # 規劃配置
        self.max_decomposition_levels = 4
        self.min_task_hours = 2.0
        self.max_task_hours = 80.0
    
    def create_project_plan(self, project_description: str, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        創建完整的項目計劃
        
        Args:
            project_description: 項目描述
            context: 項目上下文資訊
            
        Returns:
            完整的項目計劃
        """
        if context is None:
            context = {}
        
        # 1. 項目分析
        project_analysis = self._analyze_project(project_description, context)
        
        # 2. 任務分解
        wbs_structure = self._decompose_project(project_description, context)
        
        # 3. 依賴分析
        dependencies = self._analyze_dependencies(wbs_structure)
        
        # 4. 資源分配
        resource_allocation = self._allocate_resources(wbs_structure, context)
        
        # 5. 時程規劃
        schedule = self._create_schedule(wbs_structure, dependencies, context)
        
        # 6. 風險評估
        risk_assessment = self._assess_risks(wbs_structure, context)
        
        return {
            "project_id": str(uuid.uuid4()),
            "project_description": project_description,
            "project_analysis": project_analysis,
            "wbs_structure": wbs_structure,
            "dependencies": dependencies,
            "resource_allocation": resource_allocation,
            "schedule": schedule,
            "risk_assessment": risk_assessment,
            "created_at": datetime.now().isoformat(),
            "context": context
        }
    
    def _analyze_project(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析項目特性"""
        return {
            "complexity_level": self._assess_complexity(description, context),
            "estimated_duration_weeks": self._estimate_duration(description, context),
            "required_skills": self._identify_required_skills(description, context),
            "success_criteria": self._define_success_criteria(description, context),
            "constraints": self._identify_constraints(description, context)
        }
    
    def _assess_complexity(self, description: str, context: Dict[str, Any]) -> str:
        """評估項目複雜度"""
        complexity_indicators = {
            "simple": ["簡單", "基礎", "入門", "快速"],
            "moderate": ["中等", "標準", "常規", "一般"],
            "complex": ["複雜", "高級", "深入", "全面"],
            "very_complex": ["非常複雜", "企業級", "大型", "綜合"]
        }
        
        description_lower = description.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return level
        
        # 基於項目類型的默認複雜度
        project_type = context.get("project_type", "general")
        if project_type == "software_development":
            return "complex"
        elif project_type == "research":
            return "complex"
        else:
            return "moderate"
    
    def _estimate_duration(self, description: str, context: Dict[str, Any]) -> int:
        """估算項目持續時間（週）"""
        # 從上下文獲取
        if "duration_weeks" in context:
            return context["duration_weeks"]
        
        # 基於複雜度估算
        complexity = self._assess_complexity(description, context)
        duration_mapping = {
            "simple": 2,
            "moderate": 4,
            "complex": 8,
            "very_complex": 16
        }
        
        return duration_mapping.get(complexity, 4)
    
    def _identify_required_skills(self, description: str, context: Dict[str, Any]) -> List[str]:
        """識別所需技能"""
        skill_keywords = {
            "programming": ["程式", "代碼", "開發", "編程"],
            "design": ["設計", "UI", "UX", "界面"],
            "analysis": ["分析", "研究", "數據"],
            "writing": ["寫作", "文檔", "內容"],
            "management": ["管理", "協調", "規劃"]
        }
        
        identified_skills = []
        description_lower = description.lower()
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                identified_skills.append(skill)
        
        return identified_skills or ["general"]
    
    def _define_success_criteria(self, description: str, context: Dict[str, Any]) -> List[str]:
        """定義成功標準"""
        return [
            "按時完成所有計劃任務",
            "達到預期的品質標準",
            "在預算範圍內完成",
            "滿足主要利益相關者需求"
        ]
    
    def _identify_constraints(self, description: str, context: Dict[str, Any]) -> List[str]:
        """識別項目約束"""
        constraints = []
        
        if "budget" in context:
            constraints.append(f"預算限制: {context['budget']}")
        
        if "deadline" in context:
            constraints.append(f"時間限制: {context['deadline']}")
        
        if "team_size" in context:
            constraints.append(f"團隊規模: {context['team_size']} 人")
        
        return constraints or ["無特殊約束"]
    
    def _decompose_project(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分解項目為 WBS 結構"""
        strategy_name = context.get("decomposition_strategy", "functional")
        strategy = self.strategies.get(strategy_name, self.strategies["functional"])
        
        # 創建根節點
        root_node = WBSNode(
            name="項目根節點",
            description=description,
            level=0,
            complexity=TaskComplexity.VERY_COMPLEX
        )
        
        self.wbs_nodes[root_node.id] = root_node
        
        # 分解第一層
        level_1_nodes = strategy.decompose(description, context)
        
        for node in level_1_nodes:
            node.parent_id = root_node.id
            root_node.children_ids.append(node.id)
            self.wbs_nodes[node.id] = node
            
            # 進一步分解複雜任務
            if node.complexity == TaskComplexity.VERY_COMPLEX:
                self._further_decompose(node, strategy, context, 2)
        
        return self._build_wbs_structure()
    
    def _further_decompose(self, parent_node: WBSNode, strategy: DecompositionStrategy, 
                          context: Dict[str, Any], level: int):
        """進一步分解複雜任務"""
        if level > self.max_decomposition_levels:
            return
        
        # 為複雜任務創建子任務
        if parent_node.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            sub_tasks = self._create_sub_tasks(parent_node, context)
            
            for sub_task in sub_tasks:
                sub_task.parent_id = parent_node.id
                sub_task.level = level
                parent_node.children_ids.append(sub_task.id)
                self.wbs_nodes[sub_task.id] = sub_task
                
                # 遞歸分解
                if sub_task.complexity == TaskComplexity.VERY_COMPLEX:
                    self._further_decompose(sub_task, strategy, context, level + 1)
    
    def _create_sub_tasks(self, parent_node: WBSNode, context: Dict[str, Any]) -> List[WBSNode]:
        """為父任務創建子任務"""
        # 根據父任務特性創建子任務
        if "分析" in parent_node.name:
            return [
                WBSNode(
                    name="需求收集",
                    description="收集和整理需求資訊",
                    complexity=TaskComplexity.MODERATE,
                    estimated_hours=16.0
                ),
                WBSNode(
                    name="需求分析",
                    description="分析和評估需求",
                    complexity=TaskComplexity.MODERATE,
                    estimated_hours=24.0
                ),
                WBSNode(
                    name="需求文檔",
                    description="撰寫需求規格文檔",
                    complexity=TaskComplexity.SIMPLE,
                    estimated_hours=8.0
                )
            ]
        elif "設計" in parent_node.name:
            return [
                WBSNode(
                    name="概念設計",
                    description="制定總體設計概念",
                    complexity=TaskComplexity.MODERATE,
                    estimated_hours=20.0
                ),
                WBSNode(
                    name="詳細設計",
                    description="完成詳細設計規格",
                    complexity=TaskComplexity.COMPLEX,
                    estimated_hours=40.0
                ),
                WBSNode(
                    name="設計評審",
                    description="進行設計評審和優化",
                    complexity=TaskComplexity.SIMPLE,
                    estimated_hours=8.0
                )
            ]
        else:
            # 通用分解
            return [
                WBSNode(
                    name=f"{parent_node.name} - 準備",
                    description="準備工作和資源",
                    complexity=TaskComplexity.SIMPLE,
                    estimated_hours=8.0
                ),
                WBSNode(
                    name=f"{parent_node.name} - 執行",
                    description="執行主要工作",
                    complexity=TaskComplexity.MODERATE,
                    estimated_hours=24.0
                ),
                WBSNode(
                    name=f"{parent_node.name} - 驗收",
                    description="驗收和總結",
                    complexity=TaskComplexity.SIMPLE,
                    estimated_hours=4.0
                )
            ]
    
    def _build_wbs_structure(self) -> Dict[str, Any]:
        """構建 WBS 結構數據"""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.wbs_nodes.items()},
            "total_nodes": len(self.wbs_nodes),
            "max_level": max(node.level for node in self.wbs_nodes.values()),
            "total_estimated_hours": sum(
                node.estimated_hours or 0 
                for node in self.wbs_nodes.values() 
                if node.is_leaf
            )
        }
    
    def _analyze_dependencies(self, wbs_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析任務依賴關係"""
        dependencies = []
        
        # 獲取所有葉子節點（實際任務）
        leaf_nodes = [
            node for node in self.wbs_nodes.values() 
            if node.is_leaf and node.level > 0
        ]
        
        # 為同一父節點下的任務建立順序依賴
        parent_groups = {}
        for node in leaf_nodes:
            if node.parent_id not in parent_groups:
                parent_groups[node.parent_id] = []
            parent_groups[node.parent_id].append(node)
        
        for parent_id, children in parent_groups.items():
            if len(children) > 1:
                # 按任務名稱排序並建立順序依賴
                children.sort(key=lambda x: x.name)
                for i in range(len(children) - 1):
                    dependency = TaskDependency(
                        predecessor_id=children[i].id,
                        successor_id=children[i + 1].id,
                        dependency_type=DependencyType.FINISH_TO_START
                    )
                    dependencies.append(dependency.to_dict())
                    self.dependencies.append(dependency)
        
        return dependencies
    
    def _allocate_resources(self, wbs_structure: Dict[str, Any], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """分配項目資源"""
        team_size = context.get("team_size", 3)
        available_skills = context.get("available_skills", ["general"])
        
        allocation = {
            "team_assignments": {},
            "skill_requirements": {},
            "resource_conflicts": [],
            "recommendations": []
        }
        
        # 分析技能需求
        for node in self.wbs_nodes.values():
            if node.is_leaf and node.skills_required:
                for skill in node.skills_required:
                    if skill not in allocation["skill_requirements"]:
                        allocation["skill_requirements"][skill] = []
                    allocation["skill_requirements"][skill].append(node.id)
        
        # 檢查技能缺口
        missing_skills = set()
        for required_skill in allocation["skill_requirements"].keys():
            if required_skill not in available_skills:
                missing_skills.add(required_skill)
        
        if missing_skills:
            allocation["recommendations"].append(
                f"需要額外技能: {', '.join(missing_skills)}"
            )
        
        return allocation
    
    def _create_schedule(self, wbs_structure: Dict[str, Any], 
                        dependencies: List[Dict[str, Any]], 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """創建項目時程"""
        start_date = context.get("start_date", datetime.now())
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        
        # 使用關鍵路徑法（CPM）計算時程
        schedule = self._calculate_critical_path(start_date)
        
        return schedule
    
    def _calculate_critical_path(self, start_date: datetime) -> Dict[str, Any]:
        """計算關鍵路徑"""
        # 建立項目網絡圖
        self._build_project_graph()
        
        # 計算最早開始時間（前向計算）
        earliest_times = self._forward_pass(start_date)
        
        # 計算最晚開始時間（後向計算）
        latest_times = self._backward_pass(earliest_times)
        
        # 識別關鍵路徑
        critical_path = self._identify_critical_path(earliest_times, latest_times)
        
        return {
            "project_start": start_date.isoformat(),
            "project_end": max(earliest_times.values()).isoformat(),
            "critical_path": critical_path,
            "total_duration_days": (max(earliest_times.values()) - start_date).days,
            "task_schedule": {
                task_id: {
                    "earliest_start": earliest_times[task_id].isoformat(),
                    "latest_start": latest_times[task_id].isoformat(),
                    "is_critical": task_id in critical_path
                }
                for task_id in earliest_times.keys()
            }
        }
    
    def _build_project_graph(self):
        """建立項目網絡圖"""
        self.project_graph.clear()
        
        # 添加節點
        for node in self.wbs_nodes.values():
            if node.is_leaf:
                self.project_graph.add_node(
                    node.id, 
                    duration=node.estimated_hours or 8.0,
                    name=node.name
                )
        
        # 添加邊（依賴關係）
        for dependency in self.dependencies:
            self.project_graph.add_edge(
                dependency.predecessor_id,
                dependency.successor_id,
                lag=dependency.lag_time
            )
    
    def _forward_pass(self, start_date: datetime) -> Dict[str, datetime]:
        """前向計算最早開始時間"""
        earliest_times = {}
        
        # 拓撲排序
        try:
            sorted_nodes = list(nx.topological_sort(self.project_graph))
        except nx.NetworkXError:
            # 如果有循環依賴，使用簡單排序
            sorted_nodes = list(self.project_graph.nodes())
        
        for node_id in sorted_nodes:
            predecessors = list(self.project_graph.predecessors(node_id))
            
            if not predecessors:
                # 起始任務
                earliest_times[node_id] = start_date
            else:
                # 取所有前置任務的最晚完成時間
                max_predecessor_end = start_date
                for pred_id in predecessors:
                    if pred_id in earliest_times:
                        pred_duration = self.project_graph.nodes[pred_id]['duration']
                        pred_end = earliest_times[pred_id] + timedelta(hours=pred_duration)
                        
                        edge_data = self.project_graph.get_edge_data(pred_id, node_id)
                        lag = edge_data.get('lag', 0) if edge_data else 0
                        pred_end += timedelta(hours=lag)
                        
                        max_predecessor_end = max(max_predecessor_end, pred_end)
                
                earliest_times[node_id] = max_predecessor_end
        
        return earliest_times
    
    def _backward_pass(self, earliest_times: Dict[str, datetime]) -> Dict[str, datetime]:
        """後向計算最晚開始時間"""
        latest_times = {}
        
        # 從項目結束時間開始後向計算
        project_end = max(earliest_times.values())
        
        # 反向拓撲排序
        try:
            sorted_nodes = list(reversed(list(nx.topological_sort(self.project_graph))))
        except nx.NetworkXError:
            sorted_nodes = list(reversed(list(self.project_graph.nodes())))
        
        for node_id in sorted_nodes:
            successors = list(self.project_graph.successors(node_id))
            
            if not successors:
                # 結束任務
                node_duration = self.project_graph.nodes[node_id]['duration']
                latest_times[node_id] = project_end - timedelta(hours=node_duration)
            else:
                # 取所有後續任務的最早開始時間
                min_successor_start = project_end
                for succ_id in successors:
                    if succ_id in latest_times:
                        edge_data = self.project_graph.get_edge_data(node_id, succ_id)
                        lag = edge_data.get('lag', 0) if edge_data else 0
                        succ_start = latest_times[succ_id] - timedelta(hours=lag)
                        min_successor_start = min(min_successor_start, succ_start)
                
                node_duration = self.project_graph.nodes[node_id]['duration']
                latest_times[node_id] = min_successor_start - timedelta(hours=node_duration)
        
        return latest_times
    
    def _identify_critical_path(self, earliest_times: Dict[str, datetime], 
                              latest_times: Dict[str, datetime]) -> List[str]:
        """識別關鍵路徑"""
        critical_tasks = []
        
        for task_id in earliest_times.keys():
            # 浮動時間為0的任務在關鍵路徑上
            float_time = (latest_times[task_id] - earliest_times[task_id]).total_seconds()
            if abs(float_time) < 3600:  # 容許1小時誤差
                critical_tasks.append(task_id)
        
        return critical_tasks
    
    def _assess_risks(self, wbs_structure: Dict[str, Any], 
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """評估項目風險"""
        risks = {
            "high_risk_tasks": [],
            "resource_risks": [],
            "schedule_risks": [],
            "mitigation_strategies": []
        }
        
        # 識別高風險任務
        for node in self.wbs_nodes.values():
            if node.is_leaf:
                risk_score = self._calculate_task_risk(node)
                if risk_score > 0.7:
                    risks["high_risk_tasks"].append({
                        "task_id": node.id,
                        "task_name": node.name,
                        "risk_score": risk_score,
                        "risk_factors": self._identify_risk_factors(node)
                    })
        
        # 資源風險
        total_hours = sum(
            node.estimated_hours or 0 
            for node in self.wbs_nodes.values() 
            if node.is_leaf
        )
        
        team_size = context.get("team_size", 3)
        duration_weeks = context.get("duration_weeks", 4)
        available_hours = team_size * duration_weeks * 40  # 假設每週40小時
        
        if total_hours > available_hours * 0.8:  # 80%利用率閾值
            risks["resource_risks"].append("人力資源可能不足")
        
        # 時程風險
        if duration_weeks < 2:
            risks["schedule_risks"].append("時程過於緊湊")
        
        # 風險緩解策略
        if risks["high_risk_tasks"]:
            risks["mitigation_strategies"].append("為高風險任務增加緩衝時間")
        
        if risks["resource_risks"]:
            risks["mitigation_strategies"].append("考慮增加團隊成員或延長項目時間")
        
        return risks
    
    def _calculate_task_risk(self, node: WBSNode) -> float:
        """計算任務風險分數"""
        risk_score = 0.0
        
        # 複雜度風險
        complexity_risk = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MODERATE: 0.3,
            TaskComplexity.COMPLEX: 0.6,
            TaskComplexity.VERY_COMPLEX: 0.9
        }
        risk_score += complexity_risk[node.complexity] * 0.4
        
        # 技能需求風險
        if len(node.skills_required) > 2:
            risk_score += 0.3
        
        # 工時估算風險
        if node.estimated_hours and node.estimated_hours > 40:
            risk_score += 0.2
        
        # 優先級風險
        if node.priority == TaskPriority.CRITICAL:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _identify_risk_factors(self, node: WBSNode) -> List[str]:
        """識別任務風險因素"""
        factors = []
        
        if node.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            factors.append("任務複雜度高")
        
        if len(node.skills_required) > 2:
            factors.append("需要多種專業技能")
        
        if node.estimated_hours and node.estimated_hours > 40:
            factors.append("預估工時較長")
        
        if node.priority == TaskPriority.CRITICAL:
            factors.append("關鍵任務，影響項目成功")
        
        return factors
    
    def export_to_gantt(self, file_path: str) -> bool:
        """匯出為甘特圖格式"""
        try:
            gantt_data = {
                "tasks": [],
                "dependencies": []
            }
            
            for node in self.wbs_nodes.values():
                if node.is_leaf:
                    gantt_data["tasks"].append({
                        "id": node.id,
                        "name": node.name,
                        "start": node.planned_start.isoformat() if node.planned_start else None,
                        "end": node.planned_end.isoformat() if node.planned_end else None,
                        "duration": node.estimated_hours or 8.0,
                        "progress": node.completion_percentage,
                        "priority": node.priority.value
                    })
            
            for dependency in self.dependencies:
                gantt_data["dependencies"].append(dependency.to_dict())
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(gantt_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"匯出甘特圖失敗: {e}")
            return False


# 使用範例
if __name__ == "__main__":
    # 創建 WBS 規劃器
    planner = WBSPlanner()
    
    # 創建項目計劃
    project_plan = planner.create_project_plan(
        project_description="開發一個 CrewAI 教學平台",
        context={
            "project_type": "software_development",
            "duration_weeks": 8,
            "team_size": 4,
            "available_skills": ["programming", "design", "analysis"],
            "decomposition_strategy": "functional"
        }
    )
    
    print("=== 項目計劃摘要 ===")
    print(f"項目ID: {project_plan['project_id']}")
    print(f"複雜度: {project_plan['project_analysis']['complexity_level']}")
    print(f"預計時長: {project_plan['project_analysis']['estimated_duration_weeks']} 週")
    print(f"總估算工時: {project_plan['wbs_structure']['total_estimated_hours']} 小時")
    
    print("\n=== WBS 結構 ===")
    for node_id, node_data in project_plan['wbs_structure']['nodes'].items():
        if node_data['level'] == 1:  # 只顯示第一層
            print(f"- {node_data['name']}: {node_data['estimated_hours']}小時")
    
    print("\n=== 關鍵路徑 ===")
    critical_path = project_plan['schedule']['critical_path']
    for task_id in critical_path:
        node_data = project_plan['wbs_structure']['nodes'][task_id]
        print(f"- {node_data['name']}")
    
    print("\n=== 風險評估 ===")
    risks = project_plan['risk_assessment']
    if risks['high_risk_tasks']:
        print("高風險任務:")
        for risk_task in risks['high_risk_tasks']:
            print(f"- {risk_task['task_name']} (風險分數: {risk_task['risk_score']:.2f})")
    
    if risks['mitigation_strategies']:
        print("緩解策略:")
        for strategy in risks['mitigation_strategies']:
            print(f"- {strategy}")
    
    # 匯出甘特圖
    planner.export_to_gantt("project_gantt.json")
    print("\n甘特圖已匯出到 project_gantt.json") 