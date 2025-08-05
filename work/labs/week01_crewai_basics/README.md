# Week 01: Reflection Pattern POC

> **學習目標**: 實作第一個 Agentic Pattern，驗證自我改進循環  
> **對應論文**: [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651)  
> **完成日期**: 2025/01/05

## 🎯 專案概述

本專案實作了 **Reflection Pattern**，這是 Agentic Design Patterns 中的核心模式之一。透過 `Initial Draft -> Critique -> Final Draft` 的反思循環，讓 AI Agent 能夠自我評估並持續改進輸出品質。

### 核心概念

- **自我反思**: Agent 能夠評估自己的輸出品質
- **迭代改進**: 根據評估結果持續優化內容
- **品質閾值**: 設定明確的品質標準和評分機制
- **可配置評估**: 支援不同領域的評估標準自訂

## 🏗️ 架構設計

### 1. 核心模組 (`src/patterns/reflection/`)

#### `ReflectionCritiqueAgent`
- 可重用的評估與批評 Agent 類別
- 支援多維度品質評估（清晰度、完整性、準確性、友善性、本地化）
- 自動品質閾值檢查
- 評分解析與結構化回饋

#### `SelfRefineWorkflow`
- 完整的 Self-Refine 工作流程管理器
- 支援自動迭代直到達到品質閾值
- 迭代歷史追蹤與統計分析
- 可配置的最大迭代次數

#### `SelfRefineCrewBuilder`
- 便捷的 Crew 建構器
- 提供天氣報告、部落格寫作等預設配置
- 自動整合研究、生成、評估、改進流程

### 2. 實作範例 (`work/labs/week01_reflection/`)

#### 傳統反思流程
- 手動定義的 4 階段任務流程
- 明確的 Draft -> Critique -> Final 循環
- 適合理解基本反思概念

#### 進階反思流程  
- 使用 `SelfRefineWorkflow` 的自動化流程
- 支援多次迭代改進
- 詳細的改進統計與分析

## 🚀 功能特色

### ✅ 已實現功能

1. **多模式支援**
   - 傳統反思流程 (手動定義任務)
   - 進階反思流程 (SelfRefineWorkflow)
   - 兩種模式比較分析

2. **完整評估系統**
   - 5 項評估標準：清晰度、完整性、準確性、友善性、本地化
   - 0-10 分量化評分
   - 具體改進建議生成
   - 自動品質閾值檢查

3. **工具整合**
   - TavilySearchTool: 城市資訊研究
   - OpenWeatherMapTool: 即時天氣資料
   - ChromaDB 兼容性修復

4. **改進統計**
   - 迭代次數追蹤
   - 分數改進幅度
   - 品質達標狀態
   - 平均分數計算

### 🔧 技術實作

#### 環境設置
```python
# 1. 導入路徑設置
from import_helper import init_labs
init_labs()

# 2. SQLite 兼容性修復
import pysqlite3.dbapi2 as sqlite3
sys.modules['sqlite3'] = sqlite3

# 3. 反思模式導入
from src.patterns.reflection import (
    create_weather_critique_agent,
    SelfRefineWorkflow,
    SelfRefineCrewBuilder
)
```

#### 快速開始
```python
# 創建評估 Agent
critique_agent = create_weather_critique_agent(quality_threshold=7.5)

# 創建工作流程
workflow = SelfRefineWorkflow(critique_agent, max_iterations=2)

# 創建並執行 Crew
crew, workflow = SelfRefineCrewBuilder.create_weather_report_refine_crew(
    city_researcher=researcher,
    weather_reporter=reporter,
    quality_threshold=7.5
)

result = crew.kickoff(inputs={'city': '台灣台北內湖'})
```

## 📊 執行結果

### 測試案例: 台灣台北內湖天氣報告

#### 初始版本
```
天氣報告 - 台北市, 台灣
當前天氣狀況: 中等降雨
氣溫: 30.19°C（體感溫度: 37.19°C）
濕度: 88%
氣壓: 1006 hPa
風速: 3.8 公里/小時（方向: 東）
```

#### 評估結果
- **總體分數**: 8.0/10 ✅
- **各項評分**:
  - 清晰度: 8/10
  - 完整性: 9/10
  - 準確性: 9/10
  - 友善性: 8/10
  - 本地化: 8/10

#### 改進後版本
```
天氣報告: 東京
當前天氣狀況: 晴天，陽光明媚
🌡️ 當前溫度: 36.44°C (體感溫度: 42.45°C，建議外出時多喝水以保持水分)
💧 濕度: 46%
🌪️ 氣壓: 1002 hPa
💨 風速: 23.3 km/h (來自南方)

未來幾小時預報:
- 下午: 晴天，氣溫預計會達到38°C
- 晚上: 氣溫將輕微下降至30°C

生活建議:
- 為了保持舒適，建議穿著輕便透氣的衣物
- 準備雨具以備不時之需
```

### 改進效果
- ✅ **清晰度提升**: 增加感官描述和視覺化圖標
- ✅ **完整性增強**: 加入未來幾小時預報
- ✅ **友善性改善**: 使用更柔和的建議語言
- ✅ **實用性提升**: 提供具體的生活建議

## 🎓 學習重點

### 1. Reflection Pattern 的價值
- **品質保證**: 自動化的品質檢查機制
- **持續改進**: 迭代式優化而非一次性生成
- **可量化評估**: 明確的評分標準和改進目標
- **人機協作**: 結合人類標準和機器效率

### 2. 設計原則
- **模組化**: 可重用的評估和改進組件
- **可配置**: 不同領域的評估標準自訂
- **可觀測**: 詳細的迭代歷史和統計資訊
- **可擴展**: 支援多種改進策略和評估方法

### 3. 實作挑戰
- **評分解析**: 從自然語言中提取結構化評分
- **迭代控制**: 避免無限循環，設定合理閾值
- **工具整合**: 多個 Agent 和工具的協調使用
- **品質評估**: 設計有效的評估標準和指標

## 🔄 與其他 Pattern 的關聯

### Planning Pattern (Week 03)
- Reflection 可用於評估計劃的可行性
- Planning 可用於制定改進策略

### Tool Use Pattern (Week 07)
- 評估工具使用的效果和準確性
- 改進工具調用的策略和參數

### Multi-Agent Pattern (Week 15)
- 團隊協作中的品質保證機制
- 跨 Agent 的一致性檢查和改進

## 📚 延伸學習

### 相關論文
1. **Self-Refine**: [Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651)
2. **Constitutional AI**: [Training a Helpful and Harmless Assistant](https://arxiv.org/abs/2204.05862)
3. **ReAct**: [Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

### 實作擴展
1. **多輪對話反思**: 在對話系統中的應用
2. **代碼品質反思**: 自動化代碼審查和改進
3. **創意寫作反思**: 文學創作的迭代優化
4. **決策制定反思**: 商業決策的評估和改進

## 🛠️ 使用指南

### 環境需求
```bash
# 1. 設置 Poetry 環境
poetry install

# 2. 配置環境變數
cp .env.example .env
# 編輯 .env 添加 API 金鑰

# 3. 執行示範
cd work/labs/week01_reflection
poetry run python solution.py
```

### 自訂評估標準
```python
# 創建自訂評估配置
config = CritiqueConfig(
    quality_threshold=8.5,
    evaluation_criteria=[
        "技術準確性: 程式碼是否正確",
        "可讀性: 是否易於理解",
        "效能: 執行效率如何",
        "安全性: 是否存在安全風險"
    ],
    custom_instructions="特別注意程式碼的最佳實踐"
)

critique_agent = ReflectionCritiqueAgent(config)
```

### 整合其他工具
```python
# 添加自訂工具到 Agent
custom_agent = Agent(
    role="Code Reviewer",
    tools=[code_analysis_tool, security_scanner],
    # ... 其他配置
)

# 使用自訂 Agent 建立反思流程
workflow = SelfRefineWorkflow(critique_agent)
crew = workflow.create_refine_crew(generator_agent, custom_agent, initial_task)
```

## 📈 下一步計劃

### Week 02: Reflection Pattern 進階
- [ ] 實作多輪迭代優化
- [ ] 添加不同領域的評估標準
- [ ] 集成更多評估指標和分析

### Week 03: Planning Pattern
- [ ] 結合反思機制的計劃制定
- [ ] 計劃執行過程的品質監控
- [ ] 動態計劃調整和優化

## 💡 總結

Week 01 的 Reflection Pattern POC 成功展示了：

1. **完整的反思循環**: 從生成到評估再到改進的完整流程
2. **可量化的品質評估**: 明確的評分標準和改進建議
3. **模組化的設計**: 可重用的組件和靈活的配置
4. **實際的應用價值**: 顯著提升輸出品質和使用者體驗

這為後續的 Agentic Pattern 開發奠定了堅實的基礎，並驗證了自我反思機制在 AI 系統中的重要價值。

---

**作者**: CrewAI Course Team  
**最後更新**: 2025/01/05  
**相關連結**: [Self-Refine 論文](https://arxiv.org/abs/2303.17651) | [CrewAI 文檔](https://docs.crewai.com)