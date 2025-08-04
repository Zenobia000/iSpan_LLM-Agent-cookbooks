"""
Reflection Pattern: 自我批評與改進機制

基於 First Principles 的反思設計：
1. 自我評估：Agent 能夠評估自己的輸出品質
2. 缺陷識別：自動發現輸出中的問題和不足
3. 迭代改進：基於批評進行持續優化

參考文檔: docs/patterns/reflection.md
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import re
from datetime import datetime

from crewai import Agent, Task
from pydantic import BaseModel, Field

from ...core.agents.agent_base import BaseAgent
from ...core.tasks.task_base import BaseTask


class CritiqueAspect(Enum):
    """批評維度"""
    ACCURACY = "accuracy"           # 準確性
    COMPLETENESS = "completeness"   # 完整性
    CLARITY = "clarity"             # 清晰度
    RELEVANCE = "relevance"         # 相關性
    COHERENCE = "coherence"         # 連貫性
    DEPTH = "depth"                 # 深度
    CREATIVITY = "creativity"       # 創意性
    PRACTICALITY = "practicality"   # 實用性


class ReflectionLevel(Enum):
    """反思層級"""
    SURFACE = "surface"       # 表面反思：基本錯誤檢查
    STRUCTURAL = "structural" # 結構反思：邏輯和組織
    DEEP = "deep"            # 深度反思：概念和洞察
    META = "meta"            # 元反思：反思過程本身


@dataclass
class CritiquePoint:
    """批評要點"""
    aspect: CritiqueAspect
    severity: float = 0.0  # 0-1, 1表示最嚴重
    description: str = ""
    suggestion: str = ""
    evidence: str = ""
    location: Optional[str] = None  # 問題位置
    
    @property
    def is_critical(self) -> bool:
        return self.severity >= 0.8
    
    @property
    def is_major(self) -> bool:
        return self.severity >= 0.5
    
    @property
    def is_minor(self) -> bool:
        return self.severity < 0.3


@dataclass
class ReflectionResult:
    """反思結果"""
    original_content: str
    critique_points: List[CritiquePoint] = field(default_factory=list)
    overall_score: float = 0.0
    reflection_level: ReflectionLevel = ReflectionLevel.SURFACE
    improvement_suggestions: List[str] = field(default_factory=list)
    revised_content: Optional[str] = None
    reflection_time: float = 0.0
    iteration_count: int = 0
    
    @property
    def needs_revision(self) -> bool:
        """是否需要修訂"""
        return (self.overall_score < 0.7 or 
                any(point.is_critical for point in self.critique_points))
    
    @property
    def critical_issues_count(self) -> int:
        return sum(1 for point in self.critique_points if point.is_critical)
    
    @property
    def major_issues_count(self) -> int:
        return sum(1 for point in self.critique_points if point.is_major)


class CritiqueStrategy(ABC):
    """批評策略抽象基類"""
    
    @abstractmethod
    def critique(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """執行批評分析"""
        pass
    
    @abstractmethod
    def get_supported_aspects(self) -> List[CritiqueAspect]:
        """獲取支援的批評維度"""
        pass


class AccuracyCritiqueStrategy(CritiqueStrategy):
    """準確性批評策略"""
    
    def critique(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查內容準確性"""
        critique_points = []
        
        # 檢查數據準確性
        critique_points.extend(self._check_factual_accuracy(content, context))
        
        # 檢查引用和來源
        critique_points.extend(self._check_citations(content))
        
        # 檢查數字和統計
        critique_points.extend(self._check_numerical_accuracy(content))
        
        return critique_points
    
    def _check_factual_accuracy(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查事實準確性"""
        points = []
        
        # 查找可能的事實陳述
        fact_patterns = [
            r'\d{4}年.*?發生',  # 時間相關事實
            r'根據.*?研究',      # 研究引用
            r'統計顯示.*?',      # 統計數據
            r'專家.*?表示',      # 專家意見
        ]
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # 這裡可以整合事實檢查 API
                fact_statement = match.group()
                confidence = self._assess_fact_confidence(fact_statement, context)
                
                if confidence < 0.6:
                    points.append(CritiquePoint(
                        aspect=CritiqueAspect.ACCURACY,
                        severity=1.0 - confidence,
                        description=f"事實陳述可信度較低: {fact_statement}",
                        suggestion="請提供可靠來源或重新驗證此信息",
                        evidence=fact_statement,
                        location=f"位置 {match.start()}-{match.end()}"
                    ))
        
        return points
    
    def _check_citations(self, content: str) -> List[CritiquePoint]:
        """檢查引用格式"""
        points = []
        
        # 查找缺少引用的聲明
        claim_patterns = [
            r'研究表明',
            r'數據顯示',
            r'根據.*?',
            r'專家認為',
        ]
        
        for pattern in claim_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # 檢查附近是否有引用
                surrounding_text = content[max(0, match.start()-50):match.end()+50]
                if not re.search(r'\[.*?\]|\(.*?\)|\d{4}', surrounding_text):
                    points.append(CritiquePoint(
                        aspect=CritiqueAspect.ACCURACY,
                        severity=0.6,
                        description=f"缺少引用來源: {match.group()}",
                        suggestion="請添加可靠的引用來源",
                        evidence=match.group()
                    ))
        
        return points
    
    def _check_numerical_accuracy(self, content: str) -> List[CritiquePoint]:
        """檢查數字準確性"""
        points = []
        
        # 查找數字和單位
        number_patterns = [
            r'\d+(\.\d+)?%',      # 百分比
            r'\d+(\.\d+)?\s*萬',   # 萬單位
            r'\d+(\.\d+)?\s*億',   # 億單位
        ]
        
        for pattern in number_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                number_str = match.group()
                # 檢查數字合理性
                if self._is_suspicious_number(number_str):
                    points.append(CritiquePoint(
                        aspect=CritiqueAspect.ACCURACY,
                        severity=0.4,
                        description=f"數字可能不合理: {number_str}",
                        suggestion="請驗證數字的準確性和合理性",
                        evidence=number_str
                    ))
        
        return points
    
    def _assess_fact_confidence(self, fact_statement: str, context: Dict[str, Any]) -> float:
        """評估事實陳述的可信度"""
        # 簡化實作：基於關鍵詞評估
        high_confidence_indicators = ['根據官方', '政府統計', '科學研究']
        low_confidence_indicators = ['據說', '有人認為', '可能']
        
        confidence = 0.5  # 基準信心度
        
        for indicator in high_confidence_indicators:
            if indicator in fact_statement:
                confidence += 0.3
        
        for indicator in low_confidence_indicators:
            if indicator in fact_statement:
                confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _is_suspicious_number(self, number_str: str) -> bool:
        """檢查數字是否可疑"""
        # 簡化實作：檢查是否為明顯不合理的數字
        if '%' in number_str:
            percentage = float(re.search(r'\d+(\.\d+)?', number_str).group())
            return percentage > 100 or percentage < 0
        
        return False
    
    def get_supported_aspects(self) -> List[CritiqueAspect]:
        return [CritiqueAspect.ACCURACY]


class CompletenessCritiqueStrategy(CritiqueStrategy):
    """完整性批評策略"""
    
    def critique(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查內容完整性"""
        critique_points = []
        
        # 檢查結構完整性
        critique_points.extend(self._check_structural_completeness(content, context))
        
        # 檢查論點覆蓋度
        critique_points.extend(self._check_argument_coverage(content, context))
        
        # 檢查必要元素
        critique_points.extend(self._check_required_elements(content, context))
        
        return critique_points
    
    def _check_structural_completeness(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查結構完整性"""
        points = []
        
        required_sections = context.get('required_sections', ['引言', '主體', '結論'])
        content_type = context.get('content_type', 'general')
        
        if content_type == 'report':
            required_sections = ['摘要', '引言', '方法', '結果', '討論', '結論']
        elif content_type == 'analysis':
            required_sections = ['背景', '分析', '發現', '建議']
        
        for section in required_sections:
            if not self._has_section(content, section):
                points.append(CritiquePoint(
                    aspect=CritiqueAspect.COMPLETENESS,
                    severity=0.7,
                    description=f"缺少必要章節: {section}",
                    suggestion=f"請添加 {section} 章節",
                    evidence=f"未找到 {section} 相關內容"
                ))
        
        return points
    
    def _check_argument_coverage(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查論點覆蓋度"""
        points = []
        
        expected_topics = context.get('expected_topics', [])
        covered_topics = self._extract_covered_topics(content)
        
        for topic in expected_topics:
            if topic not in covered_topics:
                points.append(CritiquePoint(
                    aspect=CritiqueAspect.COMPLETENESS,
                    severity=0.5,
                    description=f"未涵蓋重要主題: {topic}",
                    suggestion=f"請增加關於 {topic} 的討論",
                    evidence=f"內容中未發現 {topic} 相關討論"
                ))
        
        return points
    
    def _check_required_elements(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查必要元素"""
        points = []
        
        # 檢查長度要求
        min_length = context.get('min_length', 0)
        if len(content) < min_length:
            points.append(CritiquePoint(
                aspect=CritiqueAspect.COMPLETENESS,
                severity=0.6,
                description=f"內容長度不足 (當前: {len(content)}, 要求: {min_length})",
                suggestion="請擴充內容以滿足長度要求",
                evidence=f"字數: {len(content)}"
            ))
        
        # 檢查關鍵詞密度
        required_keywords = context.get('required_keywords', [])
        for keyword in required_keywords:
            if keyword.lower() not in content.lower():
                points.append(CritiquePoint(
                    aspect=CritiqueAspect.COMPLETENESS,
                    severity=0.4,
                    description=f"缺少關鍵詞: {keyword}",
                    suggestion=f"請在內容中包含關鍵詞 '{keyword}'",
                    evidence=f"未找到關鍵詞 '{keyword}'"
                ))
        
        return points
    
    def _has_section(self, content: str, section_name: str) -> bool:
        """檢查是否包含特定章節"""
        section_patterns = [
            f'{section_name}',
            f'## {section_name}',
            f'# {section_name}',
            f'{section_name}：',
            f'{section_name}:',
        ]
        
        for pattern in section_patterns:
            if pattern in content:
                return True
        
        return False
    
    def _extract_covered_topics(self, content: str) -> List[str]:
        """提取已涵蓋的主題"""
        # 簡化實作：基於關鍵詞提取
        topics = []
        
        # 這裡可以使用更複雜的 NLP 技術
        topic_keywords = {
            'technology': ['技術', '科技', '創新'],
            'business': ['商業', '營收', '市場'],
            'society': ['社會', '文化', '人群'],
            'environment': ['環境', '生態', '永續'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_supported_aspects(self) -> List[CritiqueAspect]:
        return [CritiqueAspect.COMPLETENESS]


class ClarityCritiqueStrategy(CritiqueStrategy):
    """清晰度批評策略"""
    
    def critique(self, content: str, context: Dict[str, Any]) -> List[CritiquePoint]:
        """檢查內容清晰度"""
        critique_points = []
        
        # 檢查語言清晰度
        critique_points.extend(self._check_language_clarity(content))
        
        # 檢查結構清晰度
        critique_points.extend(self._check_structural_clarity(content))
        
        # 檢查邏輯清晰度
        critique_points.extend(self._check_logical_clarity(content))
        
        return critique_points
    
    def _check_language_clarity(self, content: str) -> List[CritiquePoint]:
        """檢查語言清晰度"""
        points = []
        
        # 檢查句子長度
        sentences = re.split(r'[。！？]', content)
        for sentence in sentences:
            if len(sentence) > 100:  # 過長的句子
                points.append(CritiquePoint(
                    aspect=CritiqueAspect.CLARITY,
                    severity=0.4,
                    description="句子過長，影響閱讀理解",
                    suggestion="建議將長句拆分為多個短句",
                    evidence=sentence[:50] + "..."
                ))
        
        # 檢查專業術語
        jargon_patterns = [
            r'\b[A-Z]{3,}\b',  # 全大寫縮寫
            r'\b\w*(?:tion|ment|ness|ity)\b',  # 複雜詞彙
        ]
        
        jargon_count = 0
        for pattern in jargon_patterns:
            jargon_count += len(re.findall(pattern, content))
        
        jargon_density = jargon_count / max(len(content.split()), 1)
        if jargon_density > 0.1:  # 專業術語密度過高
            points.append(CritiquePoint(
                aspect=CritiqueAspect.CLARITY,
                severity=0.5,
                description="專業術語過多，可能影響理解",
                suggestion="建議解釋專業術語或使用更通俗的表達",
                evidence=f"專業術語密度: {jargon_density:.2%}"
            ))
        
        return points
    
    def _check_structural_clarity(self, content: str) -> List[CritiquePoint]:
        """檢查結構清晰度"""
        points = []
        
        # 檢查段落結構
        paragraphs = content.split('\n\n')
        
        # 檢查段落長度
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 500:  # 段落過長
                points.append(CritiquePoint(
                    aspect=CritiqueAspect.CLARITY,
                    severity=0.3,
                    description=f"第 {i+1} 段過長",
                    suggestion="建議將長段落拆分以提高可讀性",
                    evidence=paragraph[:100] + "..."
                ))
        
        # 檢查標題結構
        headings = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        if len(paragraphs) > 5 and len(headings) == 0:
            points.append(CritiquePoint(
                aspect=CritiqueAspect.CLARITY,
                severity=0.6,
                description="缺少章節標題，結構不清晰",
                suggestion="請添加適當的章節標題來組織內容",
                evidence=f"內容有 {len(paragraphs)} 段但無標題"
            ))
        
        return points
    
    def _check_logical_clarity(self, content: str) -> List[CritiquePoint]:
        """檢查邏輯清晰度"""
        points = []
        
        # 檢查邏輯連接詞
        logical_connectors = ['因此', '所以', '然而', '但是', '此外', '首先', '其次', '最後']
        connector_count = sum(content.count(connector) for connector in logical_connectors)
        
        paragraphs = content.split('\n\n')
        connector_density = connector_count / max(len(paragraphs), 1)
        
        if connector_density < 0.5:  # 邏輯連接詞不足
            points.append(CritiquePoint(
                aspect=CritiqueAspect.CLARITY,
                severity=0.4,
                description="邏輯連接詞不足，段落間缺乏銜接",
                suggestion="請添加適當的邏輯連接詞以改善文章流暢度",
                evidence=f"邏輯連接詞密度: {connector_density:.2f}"
            ))
        
        return points
    
    def get_supported_aspects(self) -> List[CritiqueAspect]:
        return [CritiqueAspect.CLARITY]


class SelfCritiqueEngine:
    """自我批評引擎"""
    
    def __init__(self):
        self.strategies: Dict[CritiqueAspect, CritiqueStrategy] = {
            CritiqueAspect.ACCURACY: AccuracyCritiqueStrategy(),
            CritiqueAspect.COMPLETENESS: CompletenessCritiqueStrategy(),
            CritiqueAspect.CLARITY: ClarityCritiqueStrategy(),
        }
        
        # 評分權重
        self.aspect_weights = {
            CritiqueAspect.ACCURACY: 0.3,
            CritiqueAspect.COMPLETENESS: 0.25,
            CritiqueAspect.CLARITY: 0.2,
            CritiqueAspect.RELEVANCE: 0.15,
            CritiqueAspect.COHERENCE: 0.1,
        }
    
    def critique(self, content: str, context: Dict[str, Any] = None, 
                aspects: List[CritiqueAspect] = None,
                reflection_level: ReflectionLevel = ReflectionLevel.STRUCTURAL) -> ReflectionResult:
        """執行全面批評分析"""
        if context is None:
            context = {}
        
        if aspects is None:
            aspects = list(self.strategies.keys())
        
        import time
        start_time = time.time()
        
        # 收集所有批評要點
        all_critique_points = []
        
        for aspect in aspects:
            if aspect in self.strategies:
                try:
                    points = self.strategies[aspect].critique(content, context)
                    all_critique_points.extend(points)
                except Exception as e:
                    # 記錄策略執行錯誤
                    all_critique_points.append(CritiquePoint(
                        aspect=aspect,
                        severity=0.3,
                        description=f"批評分析出錯: {str(e)}",
                        suggestion="請檢查內容格式或聯繫系統管理員",
                        evidence=str(e)
                    ))
        
        # 計算整體評分
        overall_score = self._calculate_overall_score(all_critique_points, aspects)
        
        # 生成改進建議
        improvement_suggestions = self._generate_improvement_suggestions(all_critique_points)
        
        reflection_time = time.time() - start_time
        
        return ReflectionResult(
            original_content=content,
            critique_points=all_critique_points,
            overall_score=overall_score,
            reflection_level=reflection_level,
            improvement_suggestions=improvement_suggestions,
            reflection_time=reflection_time,
            iteration_count=1
        )
    
    def _calculate_overall_score(self, critique_points: List[CritiquePoint], 
                               aspects: List[CritiqueAspect]) -> float:
        """計算整體評分"""
        if not aspects:
            return 1.0
        
        aspect_scores = {}
        
        # 計算每個維度的得分
        for aspect in aspects:
            aspect_points = [p for p in critique_points if p.aspect == aspect]
            
            if not aspect_points:
                aspect_scores[aspect] = 1.0  # 沒有問題 = 滿分
            else:
                # 基於問題嚴重程度計算得分
                total_penalty = sum(point.severity for point in aspect_points)
                max_penalty = len(aspect_points)  # 假設每個問題最多扣1分
                aspect_scores[aspect] = max(0.0, 1.0 - (total_penalty / max_penalty))
        
        # 加權平均
        weighted_score = 0.0
        total_weight = 0.0
        
        for aspect, score in aspect_scores.items():
            weight = self.aspect_weights.get(aspect, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / max(total_weight, 1.0)
    
    def _generate_improvement_suggestions(self, critique_points: List[CritiquePoint]) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        # 按嚴重程度排序
        sorted_points = sorted(critique_points, key=lambda p: p.severity, reverse=True)
        
        # 優先處理嚴重問題
        critical_points = [p for p in sorted_points if p.is_critical]
        major_points = [p for p in sorted_points if p.is_major and not p.is_critical]
        
        if critical_points:
            suggestions.append("🚨 優先處理關鍵問題:")
            for point in critical_points[:3]:  # 最多顯示3個
                suggestions.append(f"   • {point.suggestion}")
        
        if major_points:
            suggestions.append("⚠️  重要改進建議:")
            for point in major_points[:3]:  # 最多顯示3個
                suggestions.append(f"   • {point.suggestion}")
        
        # 按維度分組的建議
        aspect_suggestions = {}
        for point in sorted_points:
            if point.aspect not in aspect_suggestions:
                aspect_suggestions[point.aspect] = []
            if len(aspect_suggestions[point.aspect]) < 2:  # 每個維度最多2個建議
                aspect_suggestions[point.aspect].append(point.suggestion)
        
        if len(aspect_suggestions) > 1:
            suggestions.append("📋 分類改進建議:")
            for aspect, asp_suggestions in aspect_suggestions.items():
                suggestions.append(f"   {aspect.value}:")
                for suggestion in asp_suggestions:
                    suggestions.append(f"     - {suggestion}")
        
        return suggestions


class ReflectiveAgent(BaseAgent):
    """具備反思能力的 Agent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.critique_engine = SelfCritiqueEngine()
        self.max_reflection_iterations = 3
        self.quality_threshold = 0.7
        
        # 反思歷史
        self.reflection_history: List[ReflectionResult] = []
    
    def execute_with_reflection(self, task_description: str, 
                              reflection_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """帶反思的任務執行"""
        if reflection_context is None:
            reflection_context = {}
        
        # 初始執行
        initial_result = self.execute(task_description)
        current_content = str(initial_result)
        
        # 反思迭代
        iteration = 0
        while iteration < self.max_reflection_iterations:
            # 執行反思分析
            reflection_result = self.critique_engine.critique(
                content=current_content,
                context=reflection_context,
                reflection_level=ReflectionLevel.STRUCTURAL
            )
            
            reflection_result.iteration_count = iteration + 1
            self.reflection_history.append(reflection_result)
            
            # 檢查是否需要改進
            if not reflection_result.needs_revision:
                break
            
            # 基於反思結果改進內容
            improved_content = self._improve_based_on_reflection(
                current_content, reflection_result
            )
            
            if improved_content == current_content:
                # 無法進一步改進
                break
            
            current_content = improved_content
            iteration += 1
        
        # 返回最終結果
        final_reflection = self.reflection_history[-1] if self.reflection_history else None
        
        return {
            "final_result": current_content,
            "reflection_summary": self._create_reflection_summary(final_reflection),
            "iterations": iteration + 1,
            "improvement_achieved": len(self.reflection_history) > 1,
            "quality_score": final_reflection.overall_score if final_reflection else 0.0
        }
    
    def _improve_based_on_reflection(self, content: str, 
                                   reflection: ReflectionResult) -> str:
        """基於反思結果改進內容"""
        # 這裡可以整合 LLM 來實際改進內容
        # 當前實作返回改進提示
        
        improvement_prompt = f"""
請根據以下反思分析改進內容:

原始內容:
{content}

主要問題:
{chr(10).join(f"• {point.description}: {point.suggestion}" for point in reflection.critique_points if point.is_major or point.is_critical)}

改進建議:
{chr(10).join(reflection.improvement_suggestions)}

請提供改進後的內容，確保解決上述問題。
"""
        
        # 實際應用中，這裡會調用 LLM 生成改進內容
        # 暫時返回帶有改進提示的內容
        return f"{content}\n\n[改進提示: {reflection.improvement_suggestions[0] if reflection.improvement_suggestions else '無具體建議'}]"
    
    def _create_reflection_summary(self, reflection: Optional[ReflectionResult]) -> Dict[str, Any]:
        """創建反思摘要"""
        if not reflection:
            return {"status": "no_reflection"}
        
        return {
            "quality_score": reflection.overall_score,
            "critical_issues": reflection.critical_issues_count,
            "major_issues": reflection.major_issues_count,
            "improvement_suggestions": reflection.improvement_suggestions,
            "reflection_time": reflection.reflection_time,
            "needs_revision": reflection.needs_revision
        }


# 使用範例
if __name__ == "__main__":
    # 創建批評引擎
    critique_engine = SelfCritiqueEngine()
    
    # 測試內容
    test_content = """
人工智慧發展迅速。它改變了很多行業。AI技術包括機器學習、深度學習、自然語言處理等。
這些技術在醫療、金融、教育等領域都有應用。未來AI會更加普及。
但也需要注意AI的倫理問題和潛在風險。
"""
    
    # 執行批評分析
    result = critique_engine.critique(
        content=test_content,
        context={
            "content_type": "analysis",
            "min_length": 200,
            "required_keywords": ["機器學習", "應用場景"],
            "expected_topics": ["technology", "society"]
        },
        aspects=[CritiqueAspect.ACCURACY, CritiqueAspect.COMPLETENESS, CritiqueAspect.CLARITY]
    )
    
    print("=== 反思分析結果 ===")
    print(f"整體評分: {result.overall_score:.2f}")
    print(f"是否需要修訂: {result.needs_revision}")
    print(f"反思時間: {result.reflection_time:.3f}秒")
    
    print("\n=== 發現的問題 ===")
    for point in result.critique_points:
        severity_icon = "🚨" if point.is_critical else "⚠️" if point.is_major else "💡"
        print(f"{severity_icon} [{point.aspect.value}] {point.description}")
        print(f"   建議: {point.suggestion}")
        if point.evidence:
            print(f"   證據: {point.evidence}")
        print()
    
    print("=== 改進建議 ===")
    for suggestion in result.improvement_suggestions:
        print(suggestion) 