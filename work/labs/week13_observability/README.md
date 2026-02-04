# Week 13: CrewAI Observability with Opik

> **目標**: 實作基於 Opik 框架的 CrewAI 應用程式監控與觀測能力

## 📋 概述

本週我們將學習如何使用 **Opik** 框架為 CrewAI 應用程式添加全面的觀測能力。Opik 是一個現代化的 LLM 應用觀測平台，提供端到端的跟蹤、效能監控、成本分析和即時除錯功能。

### 🆚 為什麼選擇 Opik 而非 AgentOps？

| 特性 | Opik | AgentOps |
|-----|------|----------|
| **開源程度** | 完全開源 | 部分開源 |
| **部署方式** | 本地 + 雲端 | 主要雲端 |
| **自定義能力** | 高度可定製 | 相對受限 |
| **數據隱私** | 完全控制 | 依賴第三方 |
| **集成複雜度** | 中等 | 簡單 |
| **社群生態** | 快速成長 | 較成熟 |

## 🏗️ 專案結構

```
week13_observability/
├── README.md               # 本文件
├── solution.py            # 主要實作 - 使用 Opik 的 CrewAI 應用
├── custom_handler.py      # 自定義工具處理器 (集成 Opik)
├── opik_config.py         # Opik 配置和工具函數
└── .env.example          # 環境變數設定範例
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 使用 uv 安裝所有依賴（推薦）
uv sync

# 或單獨安裝 Opik
uv add opik
# 或使用 pip
pip install opik

# 配置 Opik（首次使用）
opik configure
```

### 2. 設定環境變數

創建 `.env` 文件：

```bash
# OpenAI API 設定 (必須)
OPENAI_API_KEY=your_openai_api_key

# Tavily 搜尋工具設定 (必須)
TAVILY_API_KEY=your_tavily_api_key

# Opik 配置 (可選 - 用於雲端部署)
OPIK_API_KEY=your_opik_api_key
OPIK_WORKSPACE=crewai-observability
OPIK_PROJECT_NAME=week13-observability

# 本地部署選項 (設為 true 使用本地 Opik)
OPIK_LOCAL=false
```

### 3. 啟動 Opik (本地部署選項)

如果選擇本地部署 Opik：

```bash
# 使用 Docker Compose 啟動 Opik（推薦）
git clone https://github.com/comet-ml/opik
cd opik/deployment/docker-compose
docker-compose up -d

# 或使用單一容器
docker run -d \
  -p 5173:5173 \
  -p 3003:3003 \
  --name opik-local \
  ghcr.io/comet-ml/opik:latest

# 訪問 Opik UI: http://localhost:5173
```

### 4. 運行範例

```bash
cd work/labs/week13_observability

# 使用 uv（推薦）
uv run python solution.py

# 或傳統方式
python solution.py
```

## 🔧 核心組件解析

### 1. Opik 配置模組 (`opik_config.py`)

提供了完整的 Opik 集成工具：

```python
from opik_config import track_crew_workflow, track_agent_execution, log_agent_metrics

# 追蹤 Crew 工作流程
@track_crew_workflow("my_crew")
def run_crew():
    return crew.kickoff()

# 追蹤 Agent 執行
@track_agent_execution("researcher", "AI research task")
def research_task():
    # Agent 邏輯
    pass

# 記錄自定義指標
log_agent_metrics("agent_name", {
    "execution_time": 1.23,
    "tokens_used": 150,
    "cost": 0.002
})
```

### 2. 自定義工具處理器 (`custom_handler.py`)

集成了 Opik 追蹤功能的工具處理器：

- **自動追蹤**: 所有工具使用都會自動記錄到 Opik
- **錯誤處理**: 提供友善的錯誤訊息和詳細的錯誤追蹤
- **效能監控**: 記錄工具執行時間和使用統計

### 3. 主要應用程式 (`solution.py`)

展示了如何在實際的 CrewAI 應用中集成 Opik：

- **多 Agent 協作**: 研究員、作家、編輯的協作流程
- **工具使用追蹤**: 自動追蹤 TavilySearchTool 的使用情況
- **端到端監控**: 從任務開始到完成的完整追蹤

## 📊 Opik 功能特性

### 1. 自動追蹤功能

```python
# 使用 Opik 裝飾器自動追蹤函數
import opik

@opik.track(name="content_writer")
def write_content(topic):
    # 函數邏輯會自動被追蹤
    return generated_content

# 或使用我們的包裝器
from opik_config import track_agent_execution

@track_agent_execution("content_writer")
def write_content(topic):
    return generated_content
```

### 2. 手動追蹤功能

```python
# 使用 context manager 手動控制追蹤
from opik_config import OpikTrace

with OpikTrace("custom_operation", tags=["custom", "operation"]) as trace:
    trace.log_message("開始自定義操作")
    result = perform_operation()
    trace.log_message(f"操作完成，結果: {result}")
```

### 3. 指標記錄功能

```python
# 記錄成本指標
log_cost_metrics("gpt4_call", cost=0.02, tokens_used=500)

# 記錄 Agent 效能指標
log_agent_metrics("researcher", {
    "search_queries": 5,
    "documents_processed": 20,
    "execution_time": 45.2
})
```

## 🔍 監控儀表板

Opik 提供了豐富的視覺化儀表板：

1. **追蹤視圖**: 查看完整的執行流程樹狀圖
2. **效能分析**: 分析執行時間、成功率、錯誤率
3. **成本監控**: 追蹤 API 調用成本和 token 使用量
4. **比較分析**: 比較不同執行的效能差異

訪問 Opik UI：
- 雲端版本：[app.opik.comet.com](https://app.opik.comet.com)
- 本地版本：http://localhost:5173

## 🛠️ 進階設定

### 1. 自定義標籤和元數據

```python
# 在追蹤中添加自定義標籤
opik.track_metadata({
    "experiment_id": "exp_001",
    "model_version": "gpt-4-turbo",
    "user_id": "user_123"
})
```

### 2. 條件式追蹤

```python
# 只在特定條件下進行追蹤
if os.getenv("ENABLE_TRACKING", "true").lower() == "true":
    client = opik.Opik()
```

### 3. 批量操作追蹤

```python
# 追蹤批量處理操作
with OpikTrace("batch_processing") as trace:
    for i, item in enumerate(batch_items):
        with OpikTrace(f"item_processing_{i}") as item_trace:
            process_item(item)
```

## 🔧 故障排除

### 常見問題與解決方案

1. **首次設定問題**
   ```bash
   # 配置 Opik（會提示設定 API 金鑰）
   opik configure

   # 或使用環境變數
   export OPIK_API_KEY="your_api_key"
   ```

2. **連接問題**
   ```bash
   # 檢查 Opik 服務是否運行（本地部署）
   curl http://localhost:5173/api/health

   # 檢查雲端連接
   curl https://www.comet.com/api/
   ```

3. **認證問題**
   ```python
   # 檢查 API 金鑰設定
   import os
   print(f"API Key: {os.getenv('OPIK_API_KEY', 'Not Set')}")

   # 獲取 API 金鑰：https://www.comet.com/api/my/settings/
   ```

4. **追蹤不顯示**
   - 確認 Opik 已正確配置：`opik configure`
   - 檢查網路連接和防火牆設定
   - 查看控制台錯誤訊息
   - 確認專案名稱設定正確

## 🎯 學習目標檢核

完成本週學習後，你應該能夠：

- [ ] 理解 Opik 的核心概念和優勢
- [ ] 設定和配置 Opik 環境
- [ ] 在 CrewAI 應用中集成 Opik 追蹤
- [ ] 使用 Opik 儀表板分析應用效能
- [ ] 實作自定義的監控和警告機制
- [ ] 比較不同監控框架的優缺點

## 📚 參考資源

- [Opik 官方文檔](https://www.comet.com/docs/opik/)
- [Opik GitHub 倉庫](https://github.com/comet-ml/opik)
- [Opik 快速開始](https://www.comet.com/docs/opik/tracing/quickstart/)
- [Opik Python SDK](https://www.comet.com/docs/opik/python-sdk/)
- [CrewAI 官方文檔](https://docs.crewai.com/)
- [LLM 應用監控最佳實踐](https://www.comet.com/docs/opik/concepts/why_opik/)
- [Opik 評估指南](https://www.comet.com/docs/opik/evaluation/overview/)

## 🚀 下一步

完成本週學習後，建議：

1. 探索 Opik 的進階功能（A/B 測試、實驗追蹤）
2. 學習 Week 14 的部署與 CI/CD 流程
3. 研究如何將 Opik 集成到生產環境中
4. 探索其他觀測工具（如 LangSmith、Weights & Biases）的整合方案

---

**💡 提示**: Opik 的強大之處在於其開源特性和高度可定製性。支援 50+ AI 框架整合，每天可處理 4000 萬+ 追蹤記錄。在生產環境中，你可以根據具體需求調整追蹤策略和指標收集方式，也可以選擇自主部署以保護數據隱私。