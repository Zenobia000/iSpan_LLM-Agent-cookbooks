#!/usr/bin/env python3
"""
Week 02: 標準 Self-Refine 模式示範（簡化版）

一個簡化的標準自我反思工作流程示範。
此版本專注於單一、清晰的使用案例，使開發者更容易將其應用於自己的場景。

應用場景：迭代改進技術 API 文檔。
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
from typing import Dict, Any

# 4. 第三方庫導入
from crewai import Agent

# 5. 專案模組導入 - 使用標準的 Self-Refine 組件
from src.patterns.reflection import ReflectionCritiqueAgent, CritiqueConfig
from src.patterns.reflection.self_refine import SelfRefineWorkflow

# === 示範的核心組件 ===

def create_technical_writer() -> Agent:
    """創建技術文檔寫作 Agent"""
    return Agent(
        role="Technical Documentation Writer",
        goal="撰寫清晰、準確、易懂的技術文檔",
        backstory="""你是一位經驗豐富的技術文檔寫作專家，對軟體開發有深刻理解。
        你擅長將複雜的技術概念轉化為對開發者、使用者和管理者都友善的文檔。
        你注重結構、可讀性和實用價值。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True
    )

def create_code_reviewer() -> Agent:
    """創建用於品質保證的程式碼審查 Agent"""
    return Agent(
        role="Senior Code Reviewer",
        goal="審查和改進文檔中的程式碼範例和技術細節",
        backstory="""你是一位資深的程式碼審查員和技術顧問。你擅長在程式碼中識別錯誤、
        不良實踐和安全隱患。你提供清晰、可行的回饋，以確保程式碼範例正確、
        可執行並遵循最佳實踐。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True
    )

def create_technical_critique_agent(quality_threshold: float = 8.5) -> ReflectionCritiqueAgent:
    """創建專門用於技術文檔的評估 Agent"""
    config = CritiqueConfig(
        quality_threshold=quality_threshold,
        max_iterations=4,
        evaluation_criteria=[
            "技術準確性：程式碼範例和概念是否正確？",
            "完整性：是否涵蓋所有必要的實作細節？",
            "清晰度：技術說明是否易於理解？",
            "結構性：文檔組織是否邏輯清晰？",
            "實用性：是否便於實際操作和應用？",
            "錯誤處理：是否包含錯誤處理和邊界情況？",
        ],
        custom_instructions="""
        這是對技術文檔的專業評估。請特別注意：
        1. 程式碼範例的正確性和可執行性。
        2. 技術概念的準確性和時效性。
        3. 文檔的邏輯結構和導航性。
        
        請根據專業技術文檔的標準嚴格評分。
        """
    )
    return ReflectionCritiqueAgent(config)

# === 主要示範流程 ===

def run_simplified_refine_demo():
    """
    為 API 文檔執行一個簡化的自我反思示範。
    """
    print("🧪 Week 02: 簡化版 Self-Refine 模式示範")
    print("=" * 60)
    
    # 檢查必要的環境變數
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 警告：未設置 OPENAI_API_KEY 環境變數。 mogę")
        return

    print("\n💡 此示範展示了一個專注的「生成 -> 評估 -> 改進」循環。")
    print("   它使用標準的 SelfRefineWorkflow 來完成一個清晰的任務。")
    
    # 1. 創建 Agents
    generator_agent = create_technical_writer()
    refiner_agent = create_code_reviewer()
    critique_agent = create_technical_critique_agent(quality_threshold=8.0)

    # 2. 實例化工作流程
    workflow = SelfRefineWorkflow(
        critique_agent=critique_agent,
        max_iterations=3,
        verbose=True
    )

    # 3. 定義任務
    api_functions_list = """- 用戶註冊 (POST /api/users)
- 用戶登入 (POST /api/auth/login)
- 獲取用戶資料 (GET /api/users/{id})
- 更新用戶資料 (PUT /api/users/{id})
- 刪除用戶 (DELETE /api/users/{id})"""

    initial_task_description = """為「用戶管理系統」撰寫一份 RESTful API 文檔。

API 應包含以下功能：
{api_functions}

文檔必須包含：
- 每個 API 端點的清晰描述。
- 完整的請求/回應範例 (JSON)。
- 錯誤處理的說明。
- 認證機制的詳細資訊。
- 使用範例程式碼。

目標受眾是前端和後端開發者。"""
    
    inputs = {
        "api_name": "用戶管理系統 API",
        "version": "v1.0",
        "base_url": "https://api.example.com/v1",
        "api_functions": api_functions_list
    }

    # 4. 執行迭代改進流程
    print("\n🚀 開始生成和改進 API 文檔...")
    print("- " * 25)
    
    try:
        final_content, iterations = workflow.run_iterative_refine(
            generator_agent=generator_agent,
            refiner_agent=refiner_agent,
            initial_task_description=initial_task_description,
            expected_output="一份完整且專業的 API 技術文檔。",
            inputs=inputs,
            topic="API documentation"
        )
        
        # 5. 顯示結果
        print("\n✅ 改進流程完成！")
        print("=" * 50)
        print(f"📊 結果:")
        print(f"   - 迭代次數: {len(iterations)}")
        if iterations:
            initial_score = iterations[0].improvement_score
            final_score = iterations[-1].improvement_score
            print(f"   - 初始分數: {initial_score:.1f}/10")
            print(f"   - 最終分數: {final_score:.1f}/10")
            print(f"   - 分數提升: +{final_score - initial_score:.1f}")
        
        print(f"\n📄 最終文檔 (前 500 字元):")
        print("-" * 50)
        print(str(final_content)[:500] + "...")
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ 示範過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

# === 主執行區塊 ===

if __name__ == "__main__":
    try:
        run_simplified_refine_demo()
        print("\n✅ 示範結束。這個簡化後的腳本為您自己的專案提供了一個清晰的模板。")
        print(f"   檔案位置: work/labs/week02_reflection/standard_refine_demo.py")
    except KeyboardInterrupt:
        print("\n⏹️ 使用者中斷執行。")
    except Exception as e:
        print(f"\n❌ 主程式區塊發生未預期錯誤: {e}")
