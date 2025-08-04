#!/usr/bin/env python3
"""
Tool Use Pattern: Intelligent Tool Selection
智能工具選擇 - 基於上下文和歷史性能的動態工具選擇系統

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import math
from abc import ABC, abstractmethod


class SelectionStrategy(Enum):
    """工具選擇策略"""
    PERFORMANCE_BASED = "performance_based"
    COST_OPTIMIZED = "cost_optimized"
    RELIABILITY_FIRST = "reliability_first"
    SPEED_PRIORITY = "speed_priority"
    BALANCED = "balanced"
    LEARNED_PREFERENCE = "learned_preference"


class ToolCategory(Enum):
    """工具類別"""
    SEARCH = "search"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    FILE_OPERATION = "file_operation"
    WEB_INTERACTION = "web_interaction"
    AI_MODEL = "ai_model"
    DATABASE = "database"


@dataclass
class ToolMetrics:
    """工具性能指標"""
    total_uses: int = 0
    successful_uses: int = 0
    total_execution_time: float = 0.0
    total_cost: float = 0.0
    last_used: Optional[float] = None
    avg_confidence: float = 0.0
    error_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_uses == 0:
            return 0.0
        return self.successful_uses / self.total_uses
    
    @property
    def avg_execution_time(self) -> float:
        """平均執行時間"""
        if self.successful_uses == 0:
            return float('inf')
        return self.total_execution_time / self.successful_uses
    
    @property
    def avg_cost(self) -> float:
        """平均成本"""
        if self.total_uses == 0:
            return 0.0
        return self.total_cost / self.total_uses


@dataclass
class ToolDefinition:
    """工具定義"""
    name: str
    func: Callable
    category: ToolCategory
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    cost_per_use: float = 0.0
    expected_execution_time: float = 1.0
    reliability_score: float = 1.0
    metrics: ToolMetrics = field(default_factory=ToolMetrics)
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """檢查工具是否適用於當前上下文"""
        # 檢查需求是否滿足
        for requirement in self.requirements:
            if requirement not in context.get('available_resources', []):
                return False
        
        # 檢查能力是否匹配需求
        required_capabilities = context.get('required_capabilities', [])
        if required_capabilities:
            return any(cap in self.capabilities for cap in required_capabilities)
        
        return True


@dataclass
class SelectionContext:
    """選擇上下文"""
    task_description: str
    required_capabilities: List[str] = field(default_factory=list)
    available_resources: List[str] = field(default_factory=list)
    time_constraint: Optional[float] = None
    cost_constraint: Optional[float] = None
    quality_requirement: float = 0.8  # 0-1
    previous_tools: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectionResult:
    """選擇結果"""
    selected_tool: ToolDefinition
    confidence: float
    reasoning: str
    alternatives: List[Tuple[ToolDefinition, float]] = field(default_factory=list)
    selection_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolSelector(ABC):
    """工具選擇器抽象基類"""
    
    @abstractmethod
    def select_tool(
        self, 
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """選擇最適合的工具"""
        pass


class PerformanceBasedSelector(ToolSelector):
    """基於性能的選擇器"""
    
    def select_tool(
        self, 
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """基於歷史性能選擇工具"""
        applicable_tools = [
            tool for tool in available_tools 
            if tool.is_applicable(context.__dict__)
        ]
        
        if not applicable_tools:
            raise ValueError("沒有適用的工具")
        
        # 計算性能分數
        scored_tools = []
        for tool in applicable_tools:
            score = self._calculate_performance_score(tool, context)
            scored_tools.append((tool, score))
        
        # 按分數排序
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        
        best_tool, best_score = scored_tools[0]
        alternatives = scored_tools[1:6]  # 取前5個替代方案
        
        return SelectionResult(
            selected_tool=best_tool,
            confidence=best_score,
            reasoning=f"基於性能選擇，成功率: {best_tool.metrics.success_rate:.2%}",
            alternatives=alternatives
        )
    
    def _calculate_performance_score(
        self, 
        tool: ToolDefinition, 
        context: SelectionContext
    ) -> float:
        """計算性能分數"""
        metrics = tool.metrics
        
        # 基礎分數組件
        success_rate = metrics.success_rate
        reliability = tool.reliability_score
        
        # 時間約束懲罰
        time_penalty = 0.0
        if context.time_constraint:
            if metrics.avg_execution_time > context.time_constraint:
                time_penalty = 0.5
        
        # 品質獎勵
        quality_bonus = 0.0
        if metrics.avg_confidence >= context.quality_requirement:
            quality_bonus = 0.2
        
        # 最終分數
        score = (success_rate * 0.4 + reliability * 0.3 + 
                quality_bonus - time_penalty)
        
        return max(0.0, min(1.0, score))


class CostOptimizedSelector(ToolSelector):
    """基於成本優化的選擇器"""
    
    def select_tool(
        self, 
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """基於成本效益選擇工具"""
        applicable_tools = [
            tool for tool in available_tools 
            if tool.is_applicable(context.__dict__)
        ]
        
        if not applicable_tools:
            raise ValueError("沒有適用的工具")
        
        # 過濾超過成本約束的工具
        if context.cost_constraint:
            applicable_tools = [
                tool for tool in applicable_tools
                if tool.cost_per_use <= context.cost_constraint
            ]
        
        if not applicable_tools:
            raise ValueError("沒有符合成本約束的工具")
        
        # 計算成本效益分數
        scored_tools = []
        for tool in applicable_tools:
            score = self._calculate_cost_benefit_score(tool, context)
            scored_tools.append((tool, score))
        
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        
        best_tool, best_score = scored_tools[0]
        alternatives = scored_tools[1:6]
        
        return SelectionResult(
            selected_tool=best_tool,
            confidence=best_score,
            reasoning=f"基於成本效益選擇，成本: ${best_tool.cost_per_use:.4f}",
            alternatives=alternatives
        )
    
    def _calculate_cost_benefit_score(
        self, 
        tool: ToolDefinition, 
        context: SelectionContext
    ) -> float:
        """計算成本效益分數"""
        # 避免除零錯誤
        cost = max(tool.cost_per_use, 0.001)
        
        # 效益 = 成功率 × 可靠性
        benefit = tool.metrics.success_rate * tool.reliability_score
        
        # 成本效益比
        cost_benefit_ratio = benefit / cost
        
        # 正規化到 0-1
        # 使用對數函數來處理大範圍的比值
        normalized_score = math.log(cost_benefit_ratio + 1) / math.log(10)
        
        return max(0.0, min(1.0, normalized_score))


class IntelligentToolSelector:
    """
    智能工具選擇器
    
    整合多種選擇策略，支援學習和適應性選擇。
    """
    
    def __init__(
        self,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        learning_enabled: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化智能工具選擇器
        
        Args:
            strategy: 選擇策略
            learning_enabled: 是否啟用學習功能
            logger: 日誌記錄器
        """
        self.strategy = strategy
        self.learning_enabled = learning_enabled
        self.logger = logger or logging.getLogger(__name__)
        
        # 選擇器策略對映
        self.selectors = {
            SelectionStrategy.PERFORMANCE_BASED: PerformanceBasedSelector(),
            SelectionStrategy.COST_OPTIMIZED: CostOptimizedSelector(),
            # 可以添加更多選擇器
        }
        
        # 學習數據
        self.selection_history: List[Dict[str, Any]] = []
        self.preference_weights = {
            'performance': 0.4,
            'cost': 0.3,
            'reliability': 0.2,
            'speed': 0.1
        }
    
    def select_tool(
        self,
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """
        選擇最適合的工具
        
        Args:
            available_tools: 可用工具列表
            context: 選擇上下文
            
        Returns:
            SelectionResult: 選擇結果
        """
        start_time = time.time()
        
        # 根據策略選擇
        if self.strategy == SelectionStrategy.BALANCED:
            result = self._balanced_selection(available_tools, context)
        elif self.strategy == SelectionStrategy.LEARNED_PREFERENCE:
            result = self._learned_selection(available_tools, context)
        else:
            selector = self.selectors.get(self.strategy)
            if selector:
                result = selector.select_tool(available_tools, context)
            else:
                # 使用性能選擇器作為預設
                result = self.selectors[SelectionStrategy.PERFORMANCE_BASED].select_tool(
                    available_tools, context
                )
        
        # 記錄選擇時間
        result.selection_time = time.time() - start_time
        
        # 記錄選擇歷史（用於學習）
        if self.learning_enabled:
            self._record_selection(context, result)
        
        self.logger.info(
            f"Selected tool: {result.selected_tool.name}, "
            f"confidence: {result.confidence:.3f}, "
            f"time: {result.selection_time:.3f}s"
        )
        
        return result
    
    def _balanced_selection(
        self,
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """平衡選擇策略"""
        applicable_tools = [
            tool for tool in available_tools 
            if tool.is_applicable(context.__dict__)
        ]
        
        if not applicable_tools:
            raise ValueError("沒有適用的工具")
        
        # 計算綜合分數
        scored_tools = []
        for tool in applicable_tools:
            score = self._calculate_balanced_score(tool, context)
            scored_tools.append((tool, score))
        
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        
        best_tool, best_score = scored_tools[0]
        alternatives = scored_tools[1:6]
        
        return SelectionResult(
            selected_tool=best_tool,
            confidence=best_score,
            reasoning="平衡策略選擇，綜合考慮性能、成本、可靠性和速度",
            alternatives=alternatives
        )
    
    def _calculate_balanced_score(
        self,
        tool: ToolDefinition,
        context: SelectionContext
    ) -> float:
        """計算平衡分數"""
        metrics = tool.metrics
        
        # 性能分數
        performance_score = metrics.success_rate * 0.8 + tool.reliability_score * 0.2
        
        # 成本分數（低成本得高分）
        max_cost = max(t.cost_per_use for t in [tool]) if tool.cost_per_use > 0 else 1.0
        cost_score = 1.0 - (tool.cost_per_use / max(max_cost, 0.001))
        
        # 可靠性分數
        reliability_score = tool.reliability_score
        
        # 速度分數（快速得高分）
        speed_score = 1.0 / (metrics.avg_execution_time + 1.0)
        
        # 時間約束檢查
        if context.time_constraint and metrics.avg_execution_time > context.time_constraint:
            speed_score *= 0.5
        
        # 成本約束檢查
        if context.cost_constraint and tool.cost_per_use > context.cost_constraint:
            cost_score = 0.0
        
        # 加權計算最終分數
        final_score = (
            performance_score * self.preference_weights['performance'] +
            cost_score * self.preference_weights['cost'] +
            reliability_score * self.preference_weights['reliability'] +
            speed_score * self.preference_weights['speed']
        )
        
        return max(0.0, min(1.0, final_score))
    
    def _learned_selection(
        self,
        available_tools: List[ToolDefinition],
        context: SelectionContext
    ) -> SelectionResult:
        """基於學習的選擇策略"""
        # 簡單的學習機制：根據歷史成功率調整偏好權重
        if self.selection_history:
            self._update_preference_weights()
        
        # 使用更新後的權重進行平衡選擇
        return self._balanced_selection(available_tools, context)
    
    def _record_selection(self, context: SelectionContext, result: SelectionResult):
        """記錄選擇歷史"""
        record = {
            'timestamp': time.time(),
            'task_description': context.task_description,
            'selected_tool': result.selected_tool.name,
            'confidence': result.confidence,
            'selection_time': result.selection_time,
            'context': context.__dict__
        }
        self.selection_history.append(record)
        
        # 限制歷史記錄大小
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-800:]
    
    def _update_preference_weights(self):
        """根據歷史數據更新偏好權重"""
        if len(self.selection_history) < 10:
            return
        
        # 簡單的學習算法：分析最近的成功模式
        recent_selections = self.selection_history[-50:]
        
        # 統計高置信度選擇的特徵
        high_confidence_selections = [
            s for s in recent_selections if s['confidence'] > 0.8
        ]
        
        if high_confidence_selections:
            # 這裡可以實作更複雜的學習算法
            # 暫時使用簡單的適應性調整
            avg_confidence = sum(s['confidence'] for s in high_confidence_selections) / len(high_confidence_selections)
            
            # 根據平均置信度調整權重
            if avg_confidence > 0.9:
                # 如果置信度很高，增加性能權重
                self.preference_weights['performance'] = min(0.6, self.preference_weights['performance'] + 0.05)
                self.preference_weights['cost'] = max(0.1, self.preference_weights['cost'] - 0.02)
    
    def update_tool_metrics(
        self,
        tool_name: str,
        execution_time: float,
        success: bool,
        cost: float = 0.0,
        confidence: float = 0.0
    ):
        """
        更新工具性能指標
        
        Args:
            tool_name: 工具名稱
            execution_time: 執行時間
            success: 是否成功
            cost: 執行成本
            confidence: 置信度
        """
        # 這個方法需要配合工具註冊表使用
        # 在實際應用中，會從工具註冊表中查找工具並更新其指標
        self.logger.info(
            f"Updating metrics for {tool_name}: "
            f"time={execution_time:.3f}s, success={success}, cost=${cost:.4f}"
        )
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """獲取選擇統計"""
        if not self.selection_history:
            return {}
        
        total_selections = len(self.selection_history)
        avg_confidence = sum(s['confidence'] for s in self.selection_history) / total_selections
        avg_selection_time = sum(s['selection_time'] for s in self.selection_history) / total_selections
        
        # 工具使用頻率
        tool_usage = {}
        for record in self.selection_history:
            tool_name = record['selected_tool']
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return {
            'total_selections': total_selections,
            'avg_confidence': avg_confidence,
            'avg_selection_time': avg_selection_time,
            'tool_usage_frequency': tool_usage,
            'current_preference_weights': self.preference_weights
        }


# 使用範例
if __name__ == "__main__":
    # 創建示例工具
    search_tool = ToolDefinition(
        name="web_search",
        func=lambda x: f"搜索結果: {x}",
        category=ToolCategory.SEARCH,
        description="網頁搜索工具",
        capabilities=["search", "web_access"],
        cost_per_use=0.01,
        expected_execution_time=2.0,
        reliability_score=0.9
    )
    
    # 模擬使用歷史
    search_tool.metrics.total_uses = 100
    search_tool.metrics.successful_uses = 95
    search_tool.metrics.total_execution_time = 180.0
    
    calc_tool = ToolDefinition(
        name="calculator",
        func=lambda x: f"計算結果: {x}",
        category=ToolCategory.COMPUTATION,
        description="數學計算工具",
        capabilities=["calculation", "math"],
        cost_per_use=0.001,
        expected_execution_time=0.1,
        reliability_score=0.99
    )
    
    calc_tool.metrics.total_uses = 50
    calc_tool.metrics.successful_uses = 50
    calc_tool.metrics.total_execution_time = 5.0
    
    # 創建選擇器
    selector = IntelligentToolSelector(strategy=SelectionStrategy.BALANCED)
    
    # 測試選擇
    context = SelectionContext(
        task_description="需要搜索相關信息",
        required_capabilities=["search"],
        time_constraint=5.0,
        quality_requirement=0.8
    )
    
    tools = [search_tool, calc_tool]
    result = selector.select_tool(tools, context)
    
    print(f"選擇的工具: {result.selected_tool.name}")
    print(f"置信度: {result.confidence:.3f}")
    print(f"選擇原因: {result.reasoning}")
    print(f"選擇時間: {result.selection_time:.3f}秒") 