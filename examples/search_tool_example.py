#!/usr/bin/env python3
"""
CrewAI TavilySearchTool 使用範例

此範例展示如何在 CrewAI 中使用 TavilySearchTool 進行網頁搜尋。
"""

import os
import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crewai import Agent, Task, Crew
from core.tools.search_tool import TavilySearchTool

# 確保設置了 TAVILY_API_KEY
if not os.getenv("TAVILY_API_KEY"):
    print("請設置 TAVILY_API_KEY 環境變數")
    sys.exit(1)

def main():
    # 創建搜尋工具實例
    search_tool = TavilySearchTool()
    
    # 創建研究員 Agent
    researcher = Agent(
        role='Web Researcher',
        goal='搜尋並分析網路上的最新資訊',
        backstory="""你是一位專業的網路研究員，擅長使用搜尋工具來找到準確且相關的資訊。
        你能夠分析搜尋結果並提供有價值的見解。""",
        tools=[search_tool],
        verbose=True
    )
    
    # 創建搜尋任務
    search_task = Task(
        description="""
        請搜尋 "2025年AI技術趨勢" 的相關資訊，並提供以下內容：
        1. 主要的技術趨勢概覽
        2. 重要的發展方向
        3. 對產業的影響分析
        
        請使用進階搜尋模式，並包含答案摘要。
        """,
        expected_output="結構化的AI技術趨勢分析報告，包含搜尋摘要和詳細分析",
        agent=researcher
    )
    
    # 創建 Crew 並執行
    crew = Crew(
        agents=[researcher],
        tasks=[search_task],
        verbose=True
    )
    
    # 執行任務
    result = crew.kickoff()
    
    print("\n" + "="*50)
    print("搜尋任務完成！")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()