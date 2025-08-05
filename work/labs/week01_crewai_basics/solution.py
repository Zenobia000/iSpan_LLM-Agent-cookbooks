# === 導入設置 === 
# 1. 首先設置導入路徑
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from import_helper import init_labs
init_labs()

# 2. 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
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
from typing import Dict, Any, Tuple

# 4. 第三方庫導入
from crewai import Agent, Task, Crew, Process

# 5. 專案模組導入
from src.core.tools.search_tool import TavilySearchTool
from src.core.tools.weather_tool import OpenWeatherMapTool

# === 環境檢查與工具初始化 ===

# 檢查必要的 API 金鑰是否存在
required_env_vars = ["OPENAI_API_KEY", "OPENWEATHERMAP_API_KEY", "TAVILY_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable '{var}' not found. Please add it to your .env file.")

# 實例化工具
search_tool = TavilySearchTool()
weather_tool = OpenWeatherMapTool()

print("✅ 環境檢查完成，所有工具已初始化")

# === Agent 定義 ===

def create_city_researcher() -> Agent:
    """創建城市研究員 Agent"""
    return Agent(
        role="City Researcher",
        goal="深入研究指定城市，找出其精確座標、當地語言和文化特色",
        backstory="""你是一位經驗豐富的地理學家和文化研究專家。你擅長：
        - 使用數位工具快速定位城市資訊
        - 識別當地的主要語言和文化背景
        - 提供準確的地理座標資訊
        
        你總是確保提供的資訊準確可靠，為後續的天氣報告奠定良好基礎。""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        max_iter=5,
        memory=True
    )

def create_weather_reporter() -> Agent:
    """創建天氣播報員 Agent"""
    return Agent(
        role="Weather Reporter",
        goal="基於地理座標獲取即時天氣資料，並生成用戶友善的本地化天氣報告",
        backstory="""你是一位專業的氣象播報員，具備以下專長：
        - 解讀複雜的氣象數據
        - 將技術性天氣資訊轉化為易懂的報告
        - 適應不同文化和語言的播報風格
        - 提供實用的生活建議
        
        你的目標是讓每個人都能輕鬆理解天氣狀況，並做出合適的生活安排。""",
        verbose=True,
        allow_delegation=False,
        tools=[weather_tool],
        max_iter=5,
        memory=True
    )

def create_quality_analyst() -> Agent:
    """創建品質分析 Agent (傳統方式)"""
    return Agent(
        role="Weather Report Quality Analyst",
        goal="評估天氣報告的品質並提供建設性改進建議",
        backstory="""你是一位專業的內容品質分析師，專精於天氣報告評估。
        
        你的評估標準包括：
        1. 清晰度：內容是否清楚易懂
        2. 完整性：是否包含所有必要資訊 
        3. 準確性：資訊是否正確無誤
        4. 友善性：語調是否友善親和
        5. 本地化：是否符合當地文化習慣
        
        你總是提供具體、可行的改進建議，幫助提升報告品質。
        請為每個評估標準打分 (0-10)，並提供總體評分。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True
    )

# === 基礎 Reflection Pattern 實作 ===

def create_basic_weather_crew(city_researcher: Agent, 
                             weather_reporter: Agent,
                             quality_analyst: Agent) -> Crew:
    """
    創建基礎的天氣報告 Crew (傳統手動方式)
    
    這是最基本的 Draft -> Critique -> Final 三步驟流程
    """
    
    # 步驟 1: 城市研究任務
    research_city_task = Task(
        description="深入分析城市：{city}，找出其精確的緯度、經度和當地主要語言",
        expected_output="包含城市名稱、座標（lat,lon 格式）和當地語言的報告。例如：'城市: 台北, 座標: 25.0330,121.5654, 語言: 繁體中文'",
        agent=city_researcher
    )
    
    # 步驟 2: 初始天氣報告任務 (草稿)
    draft_weather_report_task = Task(
        description="""使用城市研究的結果，獲取該城市的當前天氣狀況。
        用識別出的當地語言撰寫一份友善的天氣報告。
        
        報告應包含：
        - 當前溫度和體感溫度
        - 天氣狀況描述
        - 濕度和氣壓資訊
        - 風速和風向
        - 簡單的生活建議
        
        這是初稿版本，重點是獲取和呈現基本資訊。""",
        expected_output="使用當地語言的基礎天氣報告，包含所有關鍵天氣資訊",
        agent=weather_reporter,
        context=[research_city_task]
    )
    
    # 步驟 3: 品質評估任務
    critique_task = Task(
        description="""評估天氣報告的品質，並提供改進建議。
        
        請從以下 5 個維度進行評估 (每項 0-10 分)：
        1. 清晰度：內容是否清楚易懂
        2. 完整性：是否包含所有必要天氣資訊
        3. 準確性：資訊格式和數據是否合理
        4. 友善性：語調是否親和易讀
        5. 本地化：是否正確使用當地語言
        
        請提供：
        - 每項評分和總分
        - 具體的改進建議
        - 是否需要重寫的建議""",
        expected_output="包含 5 項評分、總分和具體改進建議的品質評估報告",
        agent=quality_analyst,
        context=[draft_weather_report_task]
    )
    
    # 步驟 4: 最終改進任務
    final_weather_report_task = Task(
        description="""根據品質分析師的評估結果，改進並重寫天氣報告。
        
        改進重點：
        1. 仔細閱讀評估報告中的具體建議
        2. 針對分數較低的項目進行改進
        3. 保持報告的核心價值和準確性
        4. 讓內容更清晰、完整和友善
        5. 確保符合當地文化和語言習慣
        
        產出一個改進後的最終版本。""",
        expected_output="經過改進的最終天氣報告，解決了品質評估中指出的問題",
        agent=weather_reporter,
        context=[critique_task]
    )
    
    return Crew(
        agents=[city_researcher, weather_reporter, quality_analyst],
        tasks=[research_city_task, draft_weather_report_task, critique_task, final_weather_report_task],
        process=Process.sequential,
        verbose=True,
        memory=True
    )

def run_basic_weather_report_demo(city: str) -> Dict[str, Any]:
    """
    執行基礎天氣報告示範 (Week 01 傳統方式)
    
    這是最基本的實作：Research -> Draft -> Critique -> Final
    沒有復雜的迭代機制，沒有動態閾值，就是簡單的四步驟流程
    
    Args:
        city: 要查詢的城市
        
    Returns:
        執行結果
    """
    print(f"\n🌤️ Week 01: 基礎天氣報告示範")
    print(f"目標城市: {city}")
    print(f"流程: Research → Draft → Critique → Final (4 步驟)")
    print("=" * 60)
    
    # 創建基礎 Agents (沒有複雜配置)
    city_researcher = create_city_researcher()
    weather_reporter = create_weather_reporter()
    quality_analyst = create_quality_analyst()
    
    # 創建基礎 Crew
    crew = create_basic_weather_crew(city_researcher, weather_reporter, quality_analyst)
    
    print("📋 執行基礎反思流程...")
    result = crew.kickoff(inputs={'city': city})
    
    return {
        "result": str(result),
        "mode": "basic",
        "steps": 4,
        "agents": 3,
        "crew": crew
    }

# === 主執行區塊 ===

if __name__ == "__main__":
    print("🧪 Week 01: CrewAI 基礎概念與簡單反思")
    print("基礎四步驟: Research → Draft → Critique → Final")
    print("=" * 60)
    
    # 測試城市清單
    test_cities = [
        "台灣台北內湖",
        "日本東京新宿", 
        "美國紐約曼哈頓"
    ]
    
    # 選擇測試城市
    city_to_research = test_cities[0]  # 可以修改索引來測試不同城市
    
    print(f"\n📍 測試城市: {city_to_research}")
    print(f"\n🔧 Week 01 特色:")
    print(f"   - 基礎的 4 步驟流程")
    print(f"   - 3 個專門的 Agent")
    print(f"   - 簡單的 5 維度評估")
    print(f"   - 一次性改進 (不迭代)")
    print(f"   - 手動任務定義")
    
    # 執行基礎示範
    result_info = run_basic_weather_report_demo(city=city_to_research)
    
    print(f"\n🎯 最終結果:")
    print("=" * 50)
    print(result_info['result'])
    
    print(f"\n📊 Week 01 統計:")
    print(f"   模式: {result_info['mode']}")
    print(f"   步驟數: {result_info['steps']}")
    print(f"   Agent 數: {result_info['agents']}")
    print(f"   複雜度: 基礎級")
    print(f"   迭代次數: 1 (固定)")
    
    print(f"\n💡 Week 01 vs Week 02 對比:")
    print(f"   Week 01: 基礎反思 (4步驟, 5維度評估, 1次改進)")
    print(f"   Week 02: 進階反思 (多輪迭代, 10+維度, 動態閾值)")
    print(f"   適合學習: CrewAI 基礎概念和簡單工作流程")
    
    print(f"\n✅ Week 01 基礎反思示範完成！")
    print(f"🔄 下一步: 進入 Week 02 體驗進階多輪迭代反思系統")
