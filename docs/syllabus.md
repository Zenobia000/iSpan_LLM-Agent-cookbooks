# 📚 CrewAI × Agentic Design Patterns 課程大綱

## 🎯 課程概述

**課程名稱**: CrewAI × Agentic Design Patterns 完整教案  
**課程期間**: 16 週 (64 小時)  
**目標對象**: 具備 Python 基礎的 AI/ML 開發者  
**授課模式**: 理論講解 + 實作練習 + 專案導向

### 核心學習目標

1. **掌握 CrewAI 框架**: 從基礎 Agent/Task 到高階 Flow/Training
2. **理解 Agentic 設計模式**: Reflection、Planning、Tool Use、Multi-Agent
3. **實作生產級系統**: 包含監控、部署、CI/CD 完整流程
4. **培養系統思維**: 設計、開發、測試、部署的全週期能力

---

## 📋 16 週詳細課綱

### Module 1: Framework 基礎 (週次 1-2)
**主題**: CrewAI 入門與 Reflection Pattern  
**Agentic Pattern**: 🔄 **Reflection**

#### Week 1: CrewAI 基礎概念
**學習目標**:
- 理解 Agent、Task、Crew 核心概念
- 建立第一個 CrewAI 應用程式
- 導入 Reasoning 功能

**理論內容**:
- CrewAI 生態系統概覽
- Agent 角色設計原則
- Task 執行機制與輸出管理
- Memory 系統基礎

**實作練習**:
```python
# Lab 1-1: 基礎天氣報告 Agent
weather_agent = Agent(
    role="氣象專家",
    goal="提供準確的天氣預報",
    backstory="擁有10年氣象預報經驗",
    reasoning=True  # 啟用推理
)
```

**評量方式**: 
- ✅ 成功建立並執行第一個 Agent
- ✅ 理解 reasoning 輸出結果
- ✅ 完成基礎配置檔案設定

#### Week 2: Reflection Pattern 深度實作
**學習目標**:
- 實作 Self-Critique Loop
- 設計品質評估機制
- 建立迭代改進流程

**理論內容**:
- Self-Refine 研究論文解析
- 自我評估與改進策略
- 品質閾值設計

**實作練習**:
```python
# Lab 1-2: Reflection Pipeline
initial_task = Task(description="撰寫產品介紹", ...)
reflection_task = Task(
    description="評分 0-10 並提出改進建議",
    context=[initial_task],
    guardrail=lambda x: int(x.split('分數:')[1].split('/')[0]) >= 8
)
```

**評量標準**:
- 🌟 **5星**: ≥2輪迭代，自評邏輯明確，品質顯著提升
- ⭐ **3星**: 1輪迭代，基本反思功能
- ⚠️ **1星**: 無迭代機制

---

### Module 2: Processes & Crews (週次 3-4)
**主題**: 團隊協作與 Planning Pattern  
**Agentic Pattern**: 📋 **Planning**

#### Week 3: Sequential & Hierarchical Processes
**學習目標**:
- 比較不同 Process 類型
- 設計工作流程架構
- 實作任務依賴關係

**理論內容**:
- Sequential vs Hierarchical vs Consensual
- Work Breakdown Structure (WBS)
- 任務分解與優先級排序

**實作練習**:
```python
# Lab 2-1: GitHub 趨勢分析團隊
crew = Crew(
    agents=[planner, researcher, writer],
    tasks=[plan_task, research_task, write_task],
    process=Process.Hierarchical,
    manager_llm="gpt-4o"
)
```

#### Week 4: Planning Agent 進階功能
**學習目標**:
- 開發動態規劃功能
- 實作進度追蹤機制
- 建立自動排程邏輯

**實作練習**:
```python
# Lab 2-2: 智能專案管理系統
def dynamic_planner(goal: str) -> List[Task]:
    return manager_agent.plan(goal)  # 自動生成任務序列
```

**評量標準**:
- 🌟 **5星**: 動態調整計劃，產生甘特圖，具備進度追蹤
- ⭐ **3星**: 靜態任務分解，基本工作流
- ⚠️ **1星**: 單一線性任務

---

### Module 3: Flows 事件驅動 (週次 5-6)
**主題**: 進階工作流控制  
**Agentic Pattern**: 📋 **Planning** (動態調度)

#### Week 5: Flow Decorators 基礎
**學習目標**:
- 掌握 @start、@listen、@router 裝飾器
- 設計事件驅動流程
- 實作條件分支邏輯

**實作練習**:
```python
# Lab 3-1: AQI 警示系統
@flow
class AQIAlertFlow:
    @start()
    def fetch_aqi_data(self):
        return {"aqi": get_current_aqi()}
    
    @router(fetch_aqi_data)
    def route_by_aqi_level(self, state):
        if state["aqi"] > 150:
            return alert_critical
        return monitor_normal
```

#### Week 6: 動態流程調整
**學習目標**:
- 實作重試與錯誤恢復
- 設計狀態持久化
- 建立動態路由機制

**評量標準**:
- 🌟 **5星**: 複雜條件路由，狀態持久化，自動重試
- ⭐ **3星**: 基本事件驅動，簡單分支
- ⚠️ **1星**: 線性流程，無條件分支

---

### Module 4: Tools & Memory (週次 7-8)
**主題**: 工具整合與外部系統連接  
**Agentic Pattern**: 🛠️ **Tool Use**

#### Week 7: 內建工具與自訂開發
**學習目標**:
- 掌握 30+ 內建工具
- 開發自訂工具
- 實作異步工具調用

**實作練習**:
```python
# Lab 4-1: 外匯交易分析系統
@tool("外匯API查詢")
async def forex_tool(currency_pair: str) -> str:
    async with aiohttp.ClientSession() as session:
        # API 調用邏輯
        return f"{currency_pair}: {rate}"

forex_agent = Agent(
    tools=[forex_tool, CodeInterpreterTool()]
)
```

#### Week 8: 錯誤處理與容錯機制
**學習目標**:
- 實作 Robust Tool Wrapper
- 設計 Fallback 策略
- 建立工具監控機制

**實作練習**:
```python
# Lab 4-2: 容錯工具系統
class RobustToolWrapper:
    def __init__(self, tool, max_retries=3, fallback=None):
        self.tool = tool
        self.max_retries = max_retries
        self.fallback = fallback
    
    async def execute_with_fallback(self, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await self.tool(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return await self.fallback(*args, **kwargs)
```

**評量標準**:
- 🌟 **5星**: ≥2外部工具，完善錯誤處理，自動fallback
- ⭐ **3星**: 1個外部工具，基本錯誤處理
- ⚠️ **1星**: 僅使用內建工具

---

### Module 5: Knowledge & RAG (週次 9-10)
**主題**: 知識庫整合與檢索  
**Agentic Pattern**: 🔄 **Reflection** + 🛠️ **Tool Use**

#### Week 9: 知識源配置與管理
**學習目標**:
- 配置多類型知識源
- 設計分層知識架構
- 實作語義搜索

**實作練習**:
```python
# Lab 5-1: 企業知識庫系統
knowledge_sources = [
    PDFKnowledgeSource("company_policies.pdf"),
    CSVKnowledgeSource("product_data.csv"),
    WebKnowledgeSource("https://docs.company.com")
]

crew = Crew(
    agents=[consultant_agent],
    knowledge_sources=knowledge_sources
)
```

#### Week 10: RAG 品質反思機制
**學習目標**:
- 實作檢索品質評估
- 設計自動重檢索邏輯
- 建立知識庫更新機制

**實作練習**:
```python
# Lab 5-2: 自適應 RAG 系統
def rag_with_reflection(query: str) -> str:
    results = knowledge_base.search(query)
    quality_score = evaluate_retrieval_quality(results)
    
    if quality_score < 0.9:
        # 觸發反思並重新檢索
        refined_query = refine_search_query(query, results)
        results = knowledge_base.search(refined_query)
    
    return generate_response(results)
```

**評量標準**:
- 🌟 **5星**: 檢索品質自評，自動重檢索，多知識源整合
- ⭐ **3星**: 基本 RAG 功能，單一知識源
- ⚠️ **1星**: 靜態知識查詢

---

### Module 6: Training & Testing (週次 11-12)
**主題**: 模型訓練與系統測試  
**Agentic Pattern**: 🔄 **Reflection** (自我評量微調)

#### Week 11: CrewAI 訓練機制
**學習目標**:
- 收集訓練數據
- 執行模型微調
- 驗證訓練效果

**實作練習**:
```python
# Lab 6-1: Self-Refine Training Pipeline
# 1. 收集對話歷史
crew.train(n_iterations=5, filename="training_data.jsonl")

# 2. 驗證改進效果
before_metrics = evaluate_crew_performance(crew, test_cases)
after_metrics = evaluate_crew_performance(trained_crew, test_cases)
```

#### Week 12: 測試與品質保證
**學習目標**:
- 建立測試框架
- 實作效能基準測試
- 設計 A/B Testing

**評量標準**:
- 🌟 **5星**: 完整測試套件，性能基準，模型改進≥20%
- ⭐ **3星**: 基本測試，有訓練流程
- ⚠️ **1星**: 無系統測試

---

### Module 7: Observability & Operations (週次 13)
**主題**: 監控與維運  
**Agentic Pattern**: 🛠️ **Tool Use**

#### Week 13: 監控與觀測
**學習目標**:
- 整合 AgentOps 監控
- 配置 Prometheus/Grafana
- 建立告警機制

**實作練習**:
```python
# Lab 7-1: 完整監控系統
import agentops

@agentops.track_agent
class MonitoredAgent(Agent):
    def execute_task(self, task):
        with agentops.track_action("task_execution"):
            return super().execute_task(task)

# Grafana 儀表板配置
dashboard = create_crewai_dashboard([
    "agent_execution_rate",
    "token_usage_by_model", 
    "error_rate_by_type",
    "response_time_percentiles"
])
```

**評量標準**:
- 🌟 **5星**: 完整監控儀表板，自動告警，成本分析
- ⭐ **3星**: 基本監控指標
- ⚠️ **1星**: 無監控機制

---

### Module 8: Deployment Strategy (週次 14)
**主題**: 部署與 CI/CD  
**Agentic Pattern**: 📋 **Planning**

#### Week 14: 容器化與自動部署
**學習目標**:
- Docker 容器化
- Kubernetes 部署
- CI/CD Pipeline 設計

**實作練習**:
```yaml
# Lab 8-1: GitHub Actions CI/CD
name: CrewAI Deployment
on:
  push:
    branches: [main]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
    steps:
      - name: Deploy to ${{ matrix.environment }}
        run: kubectl apply -f k8s/${{ matrix.environment }}/
```

**評量標準**:
- 🌟 **5星**: 多環境部署，自動化 CI/CD，監控整合
- ⭐ **3星**: 基本容器化，手動部署
- ⚠️ **1星**: 本地運行

---

### Module 9: Capstone Project (週次 15-16)
**主題**: 綜合專案實作  
**Agentic Pattern**: 👥 **Multi-Agent**

#### Week 15: 團隊專案設計
**學習目標**:
- 設計多代理協作系統
- 實作角色分工機制
- 建立溝通協議

#### Week 16: 專案展示與評估
**學習目標**:
- 完成專案部署
- 進行成果展示
- 同儕評估與反饋

**專案範例**:
1. **智能客服系統**: Planner + Researcher + Responder + QA
2. **內容創作平台**: Editor + Writer + Reviewer + Publisher  
3. **數據分析助手**: Collector + Analyst + Visualizer + Reporter

**評量標準**:
- 🌟 **5星**: ≥3 Agent 協作，清晰分工，完整部署，優秀展示
- ⭐ **3星**: 基本多 Agent 系統，功能完整
- ⚠️ **1星**: 單 Agent 或功能不完整

---

## 📊 總體評量機制

### 平時成績 (70%)
- **Lab 作業**: 40% (每週實作練習)
- **模式實作**: 20% (四大 Pattern 掌握度)
- **程式品質**: 10% (代碼規範、測試覆蓋率)

### 期末專案 (30%)
- **技術深度**: 15% (架構設計、模式應用)
- **創新性**: 10% (獨創想法、問題解決)
- **展示效果**: 5% (簡報、演示、文件)

### 額外加分項目
- 🏆 **開源貢獻**: 提交 PR 到課程專案
- 🎯 **技術分享**: 在社群發表技術文章
- 💡 **創新應用**: 開發獨特的 Agentic Pattern 實作

---

## 📚 延伸學習資源

### 必讀論文
- **Reflection**: [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651)
- **Planning**: [HuggingGPT: Solving AI Tasks with ChatGPT](https://arxiv.org/abs/2303.17580)
- **Tool Use**: [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- **Multi-Agent**: [ChatDev: Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924)

### 實用工具
- **CrewAI 官方文件**: https://docs.crewai.com
- **AgentOps 平台**: https://agentops.ai
- **Weights & Biases**: https://wandb.ai
- **Prometheus 監控**: https://prometheus.io

### 社群資源
- **GitHub Discussions**: 課程討論區
- **Discord 頻道**: 即時技術交流
- **定期 Office Hours**: 每週二 19:00-20:00

---

## 🎖️ 課程完成證書

完成所有模組並通過評量的學員將獲得：
- 📜 **結業證書**: CrewAI × Agentic Design Patterns 專業認證
- 🏅 **技能徽章**: Reflection、Planning、Tool Use、Multi-Agent 四大徽章
- 💼 **作品集指導**: 協助建立專業的 GitHub Portfolio
- 🤝 **就業推薦**: 與合作企業的實習/就業機會

---

*最後更新: 2025年1月* 