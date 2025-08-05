#!/usr/bin/env python3
"""
改進後的天氣工具示例

展示新設計如何解決 Agent 重試問題的示例。
"""

import os
import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crewai import Agent, Task, Crew
from core.tools import OpenWeatherMapTool, CoordinateWeatherTool

def test_individual_tools():
    """測試個別工具功能"""
    print("🧪 測試個別工具功能")
    print("=" * 50)
    
    # 測試城市天氣工具
    print("\n1. 測試城市天氣工具")
    city_tool = OpenWeatherMapTool()
    
    # 正確輸入
    print("✅ 正確輸入: Tokyo")
    result = city_tool._run(city_name="Tokyo")
    print(result[:200] + "..." if len(result) > 200 else result)
    
    # 測試坐標天氣工具
    print("\n2. 測試坐標天氣工具")
    coord_tool = CoordinateWeatherTool()
    
    # 正確輸入
    print("✅ 正確輸入: 東京坐標 (35.6762, 139.6503)")
    result = coord_tool._run(latitude=35.6762, longitude=139.6503)
    print(result[:200] + "..." if len(result) > 200 else result)

def test_with_crew():
    """測試與 CrewAI 整合"""
    print("\n🤖 測試與 CrewAI 整合")
    print("=" * 50)
    
    # 確保設置了 API KEY
    if not os.getenv("OPENWEATHERMAP_API_KEY"):
        print("⚠️ 請設置 OPENWEATHERMAP_API_KEY 環境變數")
        return
    
    # 創建專門的天氣分析師
    weather_analyst = Agent(
        role='Weather Analyst',
        goal='提供準確的天氣資訊分析',
        backstory="""你是一位專業的氣象分析師，擅長解讀天氣數據並提供有用的見解。
        你知道如何正確使用天氣工具：
        - 對於城市查詢，使用 OpenWeatherMapTool 並提供簡單的城市名稱
        - 對於精確坐標，使用 CoordinateWeatherTool
        """,
        tools=[OpenWeatherMapTool()],
        verbose=True
    )
    
    # 創建簡單明確的任務
    weather_task = Task(
        description="""
        請查詢東京的當前天氣狀況。
        
        重要提示：
        - 使用工具時，city_name 參數請只使用 "Tokyo"（不要加國家名）
        - 提供完整的天氣分析報告
        """,
        expected_output="包含溫度、濕度、風速等詳細資訊的天氣報告",
        agent=weather_analyst
    )
    
    # 創建 Crew 並執行
    crew = Crew(
        agents=[weather_analyst],
        tasks=[weather_task],
        verbose=True,
        # 限制重試次數避免無限循環
        max_rpm=3
    )
    
    try:
        result = crew.kickoff()
        print("\n" + "="*50)
        print("🎯 任務完成！")
        print("="*50)
        print(result)
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")

def show_best_practices():
    """展示最佳實踐"""
    print("\n📋 工具使用最佳實踐")
    print("=" * 50)
    
    practices = [
        ("✅ 正確", "OpenWeatherMapTool", "city_name: 'Tokyo'"),
        ("✅ 正確", "OpenWeatherMapTool", "city_name: 'New York'"),
        ("✅ 正確", "CoordinateWeatherTool", "latitude: 35.6762, longitude: 139.6503"),
        ("❌ 錯誤", "OpenWeatherMapTool", "city_name: 'Tokyo, Japan'"),
        ("❌ 錯誤", "OpenWeatherMapTool", "city_name: '35.6762,139.6503'"),
        ("❌ 錯誤", "CoordinateWeatherTool", "latitude: 'Tokyo'"),
    ]
    
    for status, tool, usage in practices:
        print(f"{status} {tool:<25} -> {usage}")

def main():
    """主函數"""
    print("🌤️ 改進後的天氣工具測試")
    print("="*60)
    
    # 顯示最佳實踐
    show_best_practices()
    
    # 測試個別工具
    test_individual_tools()
    
    # 測試 CrewAI 整合
    test_with_crew()

if __name__ == "__main__":
    main()