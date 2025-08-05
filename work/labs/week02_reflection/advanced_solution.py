#!/usr/bin/env python3
"""
Week 02: 進階反思模式示範（簡化版）

一個簡化的進階自我反思工作流程示範。
此版本專注於一個清晰的、可自訂的「生成-評估-改進」循環，
展示了比標準 Self-Refine 模式更強大的客製化能力。

應用場景：為新產品撰寫一份高品質的介紹文案，並透過多輪迭代進行優化。
"""

# === 環境設置 ===
# 1. 將專案根目錄加入導入路徑
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from import_helper import init_labs
init_labs()

# 2. 修復 SQLite 版本兼容性（必須在導入 CrewAI 之前執行）
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
    print(f"✅ 成功啟用 pysqlite3，SQLite 版本: {sqlite3.sqlite_version}")
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")

# 3. 標準庫導入
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

# 4. 第三方庫導入
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process

# 5. 專案模組導入
from src.patterns.reflection import ReflectionCritiqueAgent, CritiqueConfig, CritiqueResult

# === 進階反思系統的核心組件 ===

class ContentType(Enum):
    """內容類型枚舉，用於動態選擇評估標準。"""
    PRODUCT_INTRO = "product_introduction"
    BLOG_POST = "blog_post"
    TECHNICAL_DOC = "technical_documentation"

class DifficultyLevel(Enum):
    """難度等級枚舉，用於動態設定品質閾值。"""
    STANDARD = "standard"  # 8.0/10 閾值
    EXPERT = "expert"      # 9.0/10 閾值

class AdvancedIterationRecord(BaseModel):
    """進階迭代記錄，用於追蹤每一次的改進過程。"""
    iteration: int = Field(..., description="迭代次數", ge=1)
    content_type: ContentType = Field(..., description="內容類型")
    critique_result: CritiqueResult = Field(..., description="評估結果")
    refined_content: str = Field(..., description="改進後內容", min_length=1)
    improvement_score: float = Field(..., description="改進分數", ge=0.0, le=10.0)
    execution_time: float = Field(..., description="執行時間(秒)", ge=0.0)

class AdvancedCritiqueConfigFactory:
    """進階評估配置工廠，根據內容類型生成不同的評估標準。"""
    
    BASE_CRITERIA = [
        "清晰度：內容是否清楚易懂？",
        "完整性：是否包含所有必要資訊？", 
        "準確性：資訊是否正確無誤？",
        "創意性：內容是否具有創新和吸引力？",
        "連貫性：邏輯結構是否清晰流暢？",
        "可讀性：是否易於閱讀和理解？",
        "吸引力：是否能吸引讀者繼續閱讀？",
        "說服力：是否能說服讀者採取行動？",
        "可信度：是否能建立讀者的信任？",
        "可分享性：是否能被分享和傳播？",
        "可搜尋性：是否能被搜尋引擎索引？",
    ]
    
    CONTENT_SPECIFIC_CRITERIA = {
        ContentType.PRODUCT_INTRO: [
            "產品價值：是否清楚傳達產品價值主張？",
            "差異化：是否突出與競品的差異？",
            "使用者導向：是否站在使用者角度思考？"
        ],
        ContentType.TECHNICAL_DOC: [
            "結構化：是否有清晰的章節和層次？",
            "範例品質：是否提供清楚的程式碼或操作範例？",
            "疑難排解：是否包含常見問題和解決方案？"
        ],
        ContentType.BLOG_POST: [
            "清晰度：內容是否清楚易懂？",
            "完整性：是否包含所有必要資訊？", 
            "準確性：資訊是否正確無誤？",
            "創意性：內容是否具有創新和吸引力？",
            "連貫性：邏輯結構是否清晰流暢？",
        ]
    }
    
    @classmethod
    def get_criteria_for_content(cls, content_type: ContentType) -> List[str]:
        """獲取特定內容類型的評估標準。"""
        criteria = cls.BASE_CRITERIA.copy()
        criteria.extend(cls.CONTENT_SPECIFIC_CRITERIA.get(content_type, []))
        return criteria

class DynamicThresholdManager:
    """動態閾值管理器，根據難度等級設定品質目標。"""
    THRESHOLD_MAP = {
        DifficultyLevel.STANDARD: 8.0,
        DifficultyLevel.EXPERT: 9.5
    }
    
    def __init__(self, level: DifficultyLevel = DifficultyLevel.STANDARD):
        self.level = level
    
    def get_threshold(self) -> float:
        """獲取當前閾值。"""
        return self.THRESHOLD_MAP.get(self.level, 8.0)

# === 進階評估 Agent 工廠函數 ===

def create_advanced_critique_agent(
    content_type: ContentType, 
    difficulty: DifficultyLevel = DifficultyLevel.STANDARD,
    max_iterations: int = 3
) -> ReflectionCritiqueAgent:
    """創建進階評估 Agent (通用工廠函數)"""
    criteria = AdvancedCritiqueConfigFactory.get_criteria_for_content(content_type)
    threshold_manager = DynamicThresholdManager(difficulty)
    threshold = threshold_manager.get_threshold()
    
    config = CritiqueConfig(
        quality_threshold=threshold,
        evaluation_criteria=criteria,
        max_iterations=max_iterations,
        custom_instructions=f"""
        這是針對 {content_type.value} 的專業評估。
        請根據以下標準嚴格評分，並提供具體、可執行的改進建議。
        評分標準：9-10分（卓越），7-8分（良好），5-6分（需改進），0-4分（不合格）。
        """
    )
    return ReflectionCritiqueAgent(config)

def create_product_intro_critique_agent(quality_threshold: float = 8.0) -> ReflectionCritiqueAgent:
    """創建產品介紹專用評估 Agent"""
    config = CritiqueConfig(
        quality_threshold=quality_threshold,
        max_iterations=4,
        evaluation_criteria=[
            "清晰度：內容是否清楚易懂？",
            "完整性：是否包含所有必要資訊？", 
            "準確性：資訊是否正確無誤？",
            "創意性：內容是否具有創新和吸引力？",
            "說服力：是否能說服讀者採取行動？",
            "產品價值：是否清楚傳達產品價值主張？",
            "差異化：是否突出與競品的差異？",
            "使用者導向：是否站在使用者角度思考？",
            "可信度：是否能建立讀者的信任？",
            "吸引力：是否能吸引讀者繼續閱讀？"
        ],
        custom_instructions="""
        這是針對產品介紹內容的專業評估。
        請特別注意產品的價值主張、差異化優勢和使用者需求。
        評分標準：9-10分（卓越），7-8分（良好），5-6分（需改進），0-4分（不合格）。
        """
    )
    return ReflectionCritiqueAgent(config)

def create_blog_post_critique_agent(quality_threshold: float = 8.0) -> ReflectionCritiqueAgent:
    """創建部落格文章專用評估 Agent"""
    config = CritiqueConfig(
        quality_threshold=quality_threshold,
        max_iterations=4,
        evaluation_criteria=[
            "引人入勝：標題和開頭是否吸引讀者？",
            "結構清晰：段落組織是否合理？",
            "內容價值：是否提供有用資訊？",
            "可讀性：語言是否流暢易懂？",
            "結論強度：結尾是否有力且有說服力？",
            "創意性：內容是否具有創新和吸引力？",
            "連貫性：邏輯結構是否清晰流暢？",
            "可分享性：是否能被分享和傳播？"
        ],
        custom_instructions="""
        這是針對部落格文章的專業評估。
        請特別注意內容的可讀性、價值性和分享潛力。
        評分標準：9-10分（卓越），7-8分（良好），5-6分（需改進），0-4分（不合格）。
        """
    )
    return ReflectionCritiqueAgent(config)

def create_technical_doc_critique_agent(quality_threshold: float = 8.5) -> ReflectionCritiqueAgent:
    """創建技術文檔專用評估 Agent"""
    config = CritiqueConfig(
        quality_threshold=quality_threshold,
        max_iterations=4,
        evaluation_criteria=[
            "技術準確性：程式碼範例和概念是否正確？",
            "完整性：是否涵蓋所有必要的實作細節？",
            "清晰度：技術說明是否易於理解？",
            "結構性：文檔組織是否邏輯清晰？",
            "實用性：是否便於實際操作和應用？",
            "範例品質：是否提供清楚的程式碼或操作範例？",
            "疑難排解：是否包含常見問題和解決方案？"
        ],
        custom_instructions="""
        這是針對技術文檔的專業評估。
        請特別注意技術準確性、實用性和完整性。
        評分標準：9-10分（卓越），7-8分（良好），5-6分（需改進），0-4分（不合格）。
        """
    )
    return ReflectionCritiqueAgent(config)

class AdvancedReflectionWorkflow:
    """進階反思工作流程，協調整個「生成-評估-改進」過程。"""
    
    def __init__(self, max_iterations: int = 3, difficulty: DifficultyLevel = DifficultyLevel.STANDARD):
        self.max_iterations = max_iterations
        self.threshold_manager = DynamicThresholdManager(difficulty)
        self.iteration_history: List[AdvancedIterationRecord] = []

    def run(self, 
            content_generator: Agent,
            content_refiner: Agent,
            initial_prompt: str,
            content_type: ContentType,
            inputs: Dict[str, Any]) -> Tuple[str, List[AdvancedIterationRecord]]:
        """執行進階反思流程。"""
        quality_threshold = self.threshold_manager.get_threshold()
        print(f"\n🔄 開始進階反思流程")
        print(f"   內容類型: {content_type.value}")
        print(f"   品質閾值: {quality_threshold}/10")
        print(f"   最大迭代: {self.max_iterations} 次")
        print("=" * 60)
        
        current_content = ""
        
        for i in range(self.max_iterations):
            iteration = i + 1
            start_time = datetime.now()
            print(f"\n🔄 第 {iteration} 輪迭代")
            print("-" * 40)
            
            # 1. 生成或改進內容
            if iteration == 1:
                task = Task(description=initial_prompt, expected_output=f"一份高品質的 {content_type.value} 草稿", agent=content_generator)
                crew = Crew(agents=[content_generator], tasks=[task], process=Process.sequential, verbose=True)
                current_content = str(crew.kickoff(inputs=inputs))
            else:
                critique_summary = self.iteration_history[-1].critique_result.recommendation
                refinement_prompt = f"請根據以下評估回饋，改進這份內容：\n\n**先前版本:**\n{current_content}\n\n**評估回饋:**\n{critique_summary}\n\n請產出一個顯著提升的版本。"
                task = Task(description=refinement_prompt, expected_output=f"一份改進後的 {content_type.value}", agent=content_refiner)
                crew = Crew(agents=[content_refiner], tasks=[task], process=Process.sequential, verbose=True)
                current_content = str(crew.kickoff())
            
            # 2. 評估當前內容
            critique_agent_logic = create_advanced_critique_agent(
                content_type=content_type, 
                difficulty=self.threshold_manager.level, 
                max_iterations=self.max_iterations
            )
            critique_agent = critique_agent_logic.create_agent(role="Quality Analyst", goal="評估內容品質並提供改進建議")
            critique_task = critique_agent_logic.create_critique_task(content_to_review=current_content, agent=critique_agent)
            critique_crew = Crew(agents=[critique_agent], tasks=[critique_task], process=Process.sequential, verbose=True)
            critique_text = str(critique_crew.kickoff())
            critique_result = critique_agent_logic.parse_critique_result(critique_text)
            
            # 3. 記錄迭代結果
            execution_time = (datetime.now() - start_time).total_seconds()
            record = AdvancedIterationRecord(
                iteration=iteration,
                content_type=content_type,
                critique_result=critique_result,
                refined_content=current_content,
                improvement_score=critique_result.overall_score,
                execution_time=execution_time,
            )
            self.iteration_history.append(record)
            
            print(f"📊 第 {iteration} 輪評估結果: {critique_result.overall_score:.1f}/10 (耗時: {execution_time:.1f}s)")
            
            # 4. 檢查是否達到品質目標
            if critique_result.overall_score >= quality_threshold:
                print(f"\n✅ 品質目標達成！(分數: {critique_result.overall_score:.1f} >= 閾值: {quality_threshold:.1f})")
                break
            elif iteration == self.max_iterations:
                print(f"\n⚠️ 已達最大迭代次數。")
        
        return current_content, self.iteration_history

# === 示範用的 Agents ===
# 創作者 (有想法 但寫不好)
def create_content_writer() -> Agent:
    """創建內容寫作 Agent"""
    return Agent(
        role="Advanced Content Writer",
        goal="創作高品質、吸引人且符合目標受眾需求的內容",
        backstory="""你是一位經驗豐富的內容創作專家，擅長不同類型內容的創作。
        你總是力求在創意與實用性之間取得平衡，創造出既吸引人又有價值的內容。""",
        verbose=True, allow_delegation=False, max_iter=3, memory=True
    )
# 優化者(編修者)
def create_content_refiner() -> Agent:
    """創建內容優化 Agent"""
    return Agent(
        role="Content Refinement Specialist", 
        goal="根據專業評估建議，系統性地改進和優化內容品質",
        backstory="""你是一位專業的內容優化專家，擅長根據具體建議進行精準改進，
        在保持原有核心價值的同時，顯著提升內容的品質、可讀性和影響力。""",
        verbose=True, allow_delegation=False, max_iter=3, memory=True
    )

# === 主要示範執行函數 ===

def run_advanced_refine_demo():
    """執行一個進階的、專注的自我反思示範。"""
    print("🧪 Week 02: 進階反思模式示範（簡化版）")
    print("=" * 60)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 警告：未設置 OPENAI_API_KEY 環境變數。\n")
        return

    print("\n💡 此示範展示了進階反思系統的核心特色：")
    print("   - 獨立的評估 Agent 工廠函數")
    print("   - 針對特定內容類型的專用評估標準")
    print("   - 動態難度調整和品質閾值管理")
    print("   - 結構化的迭代記錄和分析")

    # 1. 初始化工作流程
    workflow = AdvancedReflectionWorkflow(max_iterations=3, difficulty=DifficultyLevel.STANDARD)
    
    # 2. 創建 Agents
    writer = create_content_writer()
    refiner = create_content_refiner()
    
    # 3. 定義初始任務
    initial_prompt = """為一款名為「SmartHome AI Pro」的 AI 智能家居管理系統撰寫產品介紹。

產品特色：
- 整合語音控制、環境監測、能源管理
- 支援 100+ 智能設備連接
- 機器學習個人化自動化
- 隱私優先的本地處理

目標受眾：科技愛好者和注重生活品質的家庭

要求：
- 吸引人的產品描述
- 清晰的價值主張和差異化優勢
- 具體的使用場景和效益
- 專業但易懂的語言風格
- 長度約 300-400 字"""
    
    inputs = {
        "product_name": "SmartHome AI Pro",
        "target_audience": "科技愛好者和注重生活品質的家庭"
    }
    
    # 4. 執行反思流程
    final_content, history = workflow.run(
        content_generator=writer,
        content_refiner=refiner,
        initial_prompt=initial_prompt,
        content_type=ContentType.PRODUCT_INTRO,
        inputs=inputs
    )
    
    # 5. 顯示最終結果
    print(f"\n🎯 最終產品介紹:")
    print("=" * 50)
    print(final_content)
    print("=" * 50)
    
    print(f"\n📊 迭代歷史:")
    if history:
        initial_score = history[0].improvement_score
        final_score = history[-1].improvement_score
        print(f"   - 總迭代次數: {len(history)}")
        print(f"   - 初始分數: {initial_score:.1f}/10")
        print(f"   - 最終分數: {final_score:.1f}/10")
        print(f"   - 分數提升: +{final_score - initial_score:.1f}")
    else:
        print("   - 未完成任何迭代。")
    
    # 6. 展示獨立工廠函數的使用
    print(f"\n🔧 工廠函數示範:")
    print("=" * 50)
    
    # 展示專用工廠函數
    product_critic = create_product_intro_critique_agent(quality_threshold=8.0)
    blog_critic = create_blog_post_critique_agent(quality_threshold=7.5)
    technical_critic = create_technical_doc_critique_agent(quality_threshold=8.5)
    
    print(f"✅ 產品介紹評估 Agent: 閾值 {product_critic.config.quality_threshold}/10，{len(product_critic.config.evaluation_criteria)} 項標準")
    print(f"✅ 部落格文章評估 Agent: 閾值 {blog_critic.config.quality_threshold}/10，{len(blog_critic.config.evaluation_criteria)} 項標準")
    print(f"✅ 技術文檔評估 Agent: 閾值 {technical_critic.config.quality_threshold}/10，{len(technical_critic.config.evaluation_criteria)} 項標準")
    
    # 展示通用工廠函數
    advanced_critic = create_advanced_critique_agent(
        content_type=ContentType.PRODUCT_INTRO,
        difficulty=DifficultyLevel.EXPERT,
        max_iterations=5
    )
    print(f"✅ 進階通用評估 Agent: 閾值 {advanced_critic.config.quality_threshold}/10，{len(advanced_critic.config.evaluation_criteria)} 項標準")
    
    print(f"\n🆚 設計模式對比:")
    print(f"   專用工廠函數: 簡單直接，針對特定用途優化")
    print(f"   通用工廠函數: 靈活可配置，支援動態參數")

# === 主執行區塊 ===

if __name__ == "__main__":
    try:
        run_advanced_refine_demo()
        print(f"\n✅ 示範結束。這個簡化後的腳本展示了一個可客製化的進階反思循環。\n")
        print(f"   檔案位置: work/labs/week02_reflection/advanced_solution.py")
    except KeyboardInterrupt:
        print(f"\n⏹️ 使用者中斷執行。\n")
    except Exception as e:
        print(f"\n❌ 主程式區塊發生未預期錯誤: {e}\n")
        import traceback
        traceback.print_exc()
