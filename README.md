# 🤖 CrewAI × Agentic Design Patterns 教案專案

> **完整的 16 週 CrewAI 教學課程，深度整合四大 Agentic 設計模式**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![CrewAI Version](https://img.shields.io/badge/crewai-0.80.0%2B-green.svg)](https://crewai.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://github.com/ispan/crewai-agentic-course/workflows/CI/CD/badge.svg)](https://github.com/ispan/crewai-agentic-course/actions)

## 🎯 專案目標

本專案旨在提供一套完整的 CrewAI 教學解決方案，整合四大 Agentic 設計模式：
- **🔄 Reflection**: 自我反思與品質改進
- **📋 Planning**: 任務分解與動態規劃  
- **🛠️ Tool Use**: 工具調用與外部整合
- **👥 Multi-Agent**: 多代理協作系統

## 📚 課程架構

### 核心模組對映

| 週次 | 主題 | Agentic Pattern | 重點技能 |
|------|------|-----------------|----------|
| 01-02 | **Framework 基礎** | Reflection | Agent/Task、Self-Critique Loop |
| 03-04 | **Processes & Crews** | Planning | Sequential/Hierarchical、WBS 分解 |
| 05-06 | **Flows 事件驅動** | Planning | Flow Decorators、動態排程 |
| 01-02 | **Framework 基礎** | Reflection | Agent/Task、Self-Critique Loop |
| 03-04 | **Processes & Crews** | Planning | Sequential/Hierarchical、WBS 分解 |
| 05-06 | **Flows 事件驅動** | Planning | Flow Decorators、動態排程 |
| 07-08 | **Tools & Memory** | Tool Use | 30+ Tools、異步執行、錯誤處理 |
| 09-10 | **Knowledge & RAG** | Reflection + Tool Use | 知識庫整合、檢索品質反思 |
| 11-12 | **Training & Testing** | Reflection | Self-Refine Pipeline、模型微調 |
| 13 | **Observability** | Tool Use | AgentOps、Prometheus/Grafana |
| 14 | **Deployment** | Planning | CI/CD、容器化部署 |
| 15-16 | **Capstone Project** | Multi-Agent | 團隊專案、角色分工、協作機制 |

## 🚀 快速開始

### 環境需求

- **Python**: 3.10+
- **Node.js**: 16+ (可選，用於前端開發)
- **Docker**: 20.10+ (用於容器化部署)
- **Git**: 2.30+

### 安裝步驟

#### 方法一：使用 uv (推薦)

```bash
# 1. 克隆專案
git clone https://github.com/ispan/crewai-agentic-course.git
cd crewai-agentic-course

# 2. 安裝 uv (如果尚未安裝)
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用 pip: pip install uv

# 3. 創建虛擬環境並安裝依賴
uv sync

# 4. 啟用虛擬環境
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate.bat  # Windows

# 5. 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，設定您的 API 金鑰
```

#### 方法二：使用 pip

```bash
# 1. 克隆專案
git clone https://github.com/ispan/crewai-agentic-course.git
cd crewai-agentic-course

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -e .

# 4. 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，設定您的 API 金鑰
```

### 🔑 必要的 API 金鑰設定

在 `.env` 檔案中設定以下 API 金鑰：

```bash
# AI Service Providers (至少需要一個)
OPENAI_API_KEY=sk-your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Search APIs (建議設定)
SERPER_API_KEY=your_serper_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# 觀測性工具 (可選)
AGENTOPS_API_KEY=your_agentops_api_key_here
```

### 🐳 Docker 快速啟動

```bash
# 啟動完整開發環境
docker-compose -f infra/docker-compose.yml up -d

# 服務端點
# - CrewAI 應用: http://localhost:8000
# - ChromaDB: http://localhost:8001
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
```

## 📁 專案結構

```text
crewai-agentic-course/
├── 📚 docs/                     # 教學文件
│   ├── patterns/                # Agentic 模式說明
│   ├── guides/                  # 開發指南
│   └── rubrics.md               # 評量標準
│
├── 💻 src/                      # 核心程式碼
│   ├── core/                    # CrewAI 基礎封裝
│   │   ├── agents/              # Agent 定義
│   │   ├── tasks/               # Task 管理
│   │   ├── tools/               # 工具開發
│   │   ├── crews/               # 團隊協作
│   │   ├── memory/              # 記憶系統
│   │   └── knowledge/           # 知識庫
│   ├── patterns/                # 四大 Agentic 模式
│   │   ├── reflection/          # 自我反思
│   │   ├── planning/            # 任務規劃
│   │   ├── tool_use/            # 工具使用
│   │   └── multi_agent/         # 多代理協作
│   ├── pipelines/               # 高階工作流
│   │   ├── self_refine/         # 自我精進流程
│   │   ├── rag_reflect/         # RAG 反思循環
│   │   └── aqi_alert_flow/      # 事件驅動範例
│   ├── data/                    # 示範資料
│   └── templates/               # 程式範本
│
├── 🎓 work/                     # 學生實作區
│   ├── labs/                    # 週次實驗
│   │   ├── week01_reflection/   # 反思模式實作
│   │   ├── week02_reflection/   # 進階反思
│   │   ├── week03_planning/     # 規劃模式
│   │   └── ...                  # week04-16
│   └── projects/                # 期末專案
│
├── 🏗️ infra/                    # 基礎設施
│   ├── docker-compose.yml       # 開發環境
│   ├── k8s/                     # Kubernetes 部署
│   ├── ci/                      # CI/CD 配置
│   └── observability/           # 監控告警
│
├── 🧪 tests/                    # 測試程式
└── 📓 notebooks/                # 教學 Jupyter
```

## 🎮 實際操作範例

### 基礎 Agent 建立 (Week 01)

```python
from crewai import Agent, Task, Crew
from src.core.agents.agent_base import BaseAgent

# 建立 Reflection Pattern 的 Agent
weather_reporter = BaseAgent(
    role="天氣報告員",
    goal="提供準確且易懂的天氣預報",
    backstory="你是一位經驗豐富的氣象專家",
    reasoning=True,  # 啟用推理功能
    memory=True      # 啟用記憶功能
)

# 建立包含 Reflection 的任務
weather_task = Task(
    description="為台北提供明日天氣預報",
    expected_output="包含溫度、降雨機率和建議的詳細報告",
    agent=weather_reporter
)

reflection_task = Task(
    description="評估天氣報告品質 (0-10分) 並提出改進建議",
    expected_output="評分和具體改進方向",
    agent=weather_reporter,
    context=[weather_task]  # 依賴前一個任務的輸出
)
```

### Tool Use Pattern 實作 (Week 07)

```python
from crewai.tools import tool
from src.patterns.tool_use.robust_tool_wrapper import RobustToolWrapper

@tool("外匯匯率查詢")
def forex_rate_tool(currency_pair: str) -> str:
    """查詢即時外匯匯率，支援自動重試和錯誤處理"""
    try:
        # 實際 API 調用邏輯
        rate = get_forex_rate(currency_pair)
        return f"{currency_pair} 匯率: {rate}"
    except Exception as e:
        # 使用 Robust Wrapper 處理錯誤
        return f"查詢失敗，使用備用數據源: {fallback_rate}"

# 在 Agent 中使用
forex_agent = Agent(
    role="外匯分析師",
    tools=[RobustToolWrapper(forex_rate_tool)],  # 包裝工具以提供錯誤處理
    allow_delegation=True
)
```

### Multi-Agent 協作 (Week 15-16)

```python
from crewai import Crew
from src.patterns.multi_agent.delegation_manager import DelegationManager

# 建立多角色團隊
planner = Agent(role="專案規劃師", goal="制定詳細計劃")
executor = Agent(role="執行專家", goal="高效執行任務")
reviewer = Agent(role="品質審查員", goal="確保輸出品質")

# 設定協作機制
crew = Crew(
    agents=[planner, executor, reviewer],
    process=Process.Hierarchical,  # 階層式協作
    manager_llm="gpt-4o",
    delegation_manager=DelegationManager()
)
```

## 📈 監控與觀測

### 使用 AgentOps 監控

```python
import agentops
from src.core.crews.crew_factory import CrewFactory

# 啟用 AgentOps 追蹤
agentops.init()

# 建立並執行 Crew
crew = CrewFactory.create_weather_crew()
result = crew.kickoff()

# 自動記錄執行指標
agentops.end_session("SUCCESS")
```

### Grafana 儀表板

訪問 `http://localhost:3000` 查看即時監控儀表板：
- Agent 執行統計
- Token 使用量分析
- API 回應時間
- 錯誤率追蹤
- 系統資源使用

## 🧪 測試與驗證

```bash
# 執行所有測試
pytest tests/ -v

# 執行特定模式測試
pytest tests/patterns/test_reflection.py -v

# 產生覆蓋率報告
pytest --cov=src --cov-report=html

# 執行效能測試
pytest tests/performance/ -v --benchmark-only
```

## 📖 學習路徑

### 初學者 (Week 1-4)
1. 📖 閱讀 `docs/guides/setup_guide.md`
2. 🏃 完成 `work/labs/week01_reflection/`
3. 🔍 研究 `src/patterns/reflection/`
4. 💡 實作第一個 Self-Critique Agent

### 進階學習 (Week 5-12)
1. 🛠️ 掌握 Tool Use Pattern
2. 🧠 整合 Knowledge & RAG
3. 🔄 建立 Self-Refine Pipeline
4. 📊 設定監控與觀測

### 專家級 (Week 13-16)
1. 🚀 容器化部署
2. 👥 Multi-Agent 系統設計
3. 🎯 Capstone 專案實作
4. 📈 效能最佳化

## 🤝 貢獻指南

我們歡迎各種形式的貢獻！

### 開發流程

```bash
# 1. Fork 專案並建立分支
git checkout -b feature/your-feature-name

# 2. 安裝開發依賴
uv sync --extra dev

# 3. 設定 pre-commit hooks
pre-commit install

# 4. 進行開發並提交
git add .
git commit -m "feat: add your feature"

# 5. 推送並建立 Pull Request
git push origin feature/your-feature-name
```

### 程式碼規範

- ✅ 使用 **Black** 格式化程式碼
- ✅ 通過 **Flake8** 檢查
- ✅ 完整的 **MyPy** 型別註解
- ✅ **pytest** 測試覆蓋率 ≥ 90%

## 📞 支援與社群

- 📧 **Email**: team@ispan.com.tw
- 💬 **討論區**: [GitHub Discussions](https://github.com/ispan/crewai-agentic-course/discussions)
- 🐛 **Bug 回報**: [GitHub Issues](https://github.com/ispan/crewai-agentic-course/issues)
- 📚 **文件**: [完整文件](https://docs.ispan.com.tw/crewai-agentic-course)

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權條款。

## 🙏 致謝

特別感謝以下專案和社群的貢獻：
- [CrewAI](https://crewai.com) - 多代理 AI 框架
- [LangChain](https://langchain.com) - AI 應用開發框架
- [ChromaDB](https://www.trychroma.com) - 向量資料庫
- [AgentOps](https://agentops.ai) - AI Agent 觀測平台

---

<div align="center">

**🌟 如果這個專案對您有幫助，請給我們一個 Star！**

[![GitHub stars](https://img.shields.io/github/stars/ispan/crewai-agentic-course.svg?style=social&label=Star)](https://github.com/ispan/crewai-agentic-course)

</div>
