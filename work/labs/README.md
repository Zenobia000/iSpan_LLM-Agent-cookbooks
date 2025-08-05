# CrewAI × Agentic Design Patterns 實驗室

> **完整的 16 週實作課程架構**  
> 基於 Self-Refine、Planning、Tool Use、Multi-Agent 四大 Agentic Patterns

## 🎯 **專案概述**

本實驗室提供完整的 CrewAI × Agentic Design Patterns 學習路徑，從基礎概念到進階應用，涵蓋 16 週的系統性學習內容。

### 核心特色
- ✅ **模組化設計**: 每週獨立且相互銜接的學習單元
- ✅ **漸進式學習**: 從基礎到進階的系統性發展
- ✅ **實作導向**: 每週都有具體的程式碼實作和示範
- ✅ **四大 Pattern**: 完整覆蓋 Reflection、Planning、Tool Use、Multi-Agent

## 📂 **16 週完整架構**

### 🔄 **Module 1: Framework 基礎與 Reflection Pattern (Week 1-2)**

#### [`week01_crewai_basics/`](./week01_crewai_basics/) - CrewAI 基礎概念 ✅
- **學習目標**: 理解 Agent、Task、Crew 核心概念，建立第一個 CrewAI 應用
- **核心內容**: 基礎天氣報告 Agent + 簡單反思機制
- **完成狀態**: ✅ 完整實作，包含 solution.py 和詳細 README
- **評量標準**: 成功建立並執行第一個 Agent，理解 reasoning 輸出

#### [`week02_reflection/`](./week02_reflection/) - 進階反思系統 ✅
- **學習目標**: 實作 Self-Critique Loop，設計品質評估機制，建立迭代改進流程
- **核心內容**: 多輪迭代 + 動態閾值 + 智能改進引導
- **完成狀態**: ✅ 進階實作，包含 advanced_solution.py 和架構文檔
- **評量標準**: ≥2輪迭代，自評邏輯明確，品質顯著提升

---

### 📋 **Module 2: Processes & Crews 與 Planning Pattern (Week 3-4)**

#### [`week03_planning/`](./week03_planning/) - Sequential & Hierarchical Processes ✅
- **學習目標**: 比較不同 Process 類型，設計工作流程架構，實作任務依賴關係
- **核心內容**: GitHub 趨勢分析團隊 + Hierarchical 協作流程
- **完成狀態**: ✅ 基礎實作，已解決 delegation 問題
- **評量標準**: 動態調整計劃，產生甘特圖，具備進度追蹤

#### [`week04_planning_advanced/`](./week04_planning_advanced/) - Planning Agent 進階功能 📋
- **學習目標**: 開發動態規劃功能，實作進度追蹤機制，建立自動排程邏輯
- **核心內容**: 智能專案管理系統 + 動態任務生成
- **完成狀態**: 📋 待開發
- **評量標準**: 動態調整計劃，產生甘特圖，具備進度追蹤

---

### 🌊 **Module 3: Flows 事件驅動 (Week 5-6)**

#### [`week05_flows_basics/`](./week05_flows_basics/) - Flow Decorators 基礎 📋
- **學習目標**: 掌握 @start、@listen、@router 裝飾器，設計事件驅動流程
- **核心內容**: AQI 警示系統 + 條件分支邏輯
- **完成狀態**: 📋 待開發

#### [`week06_flows_advanced/`](./week06_flows_advanced/) - 動態流程調整 📋
- **學習目標**: 實作重試與錯誤恢復，設計狀態持久化，建立動態路由機制
- **完成狀態**: 📋 待開發

---

### 🛠️ **Module 4: Tools & Memory 與 Tool Use Pattern (Week 7-8)**

#### [`week07_tools_custom/`](./week07_tools_custom/) - 內建工具與自訂開發 📋
- **學習目標**: 掌握 30+ 內建工具，開發自訂工具，實作異步工具調用
- **核心內容**: 外匯交易分析系統 + 自訂 API 工具
- **完成狀態**: 📋 待開發 (已有基礎工具實作參考)

#### [`week08_tools_robust/`](./week08_tools_robust/) - 錯誤處理與容錯機制 📋
- **學習目標**: 實作 Robust Tool Wrapper，設計 Fallback 策略
- **核心內容**: 容錯工具系統 + 自動 fallback
- **完成狀態**: 📋 待開發

---

### 📚 **Module 5: Knowledge & RAG (Week 9-10)**

#### [`week09_knowledge_rag/`](./week09_knowledge_rag/) - 知識源配置與管理 📋
- **學習目標**: 配置多類型知識源，設計分層知識架構，實作語義搜索
- **核心內容**: 企業知識庫系統 + 多格式文檔處理
- **完成狀態**: 📋 待開發

#### [`week10_rag_reflection/`](./week10_rag_reflection/) - RAG 品質反思機制 📋
- **學習目標**: 實作檢索品質評估，設計自動重檢索邏輯
- **核心內容**: 自適應 RAG 系統 + 品質反思
- **完成狀態**: 📋 待開發

---

### 🧪 **Module 6: Training & Testing (Week 11-12)**

#### [`week11_training_pipeline/`](./week11_training_pipeline/) - CrewAI 訓練機制 📋
- **學習目標**: 收集訓練數據，執行模型微調，驗證訓練效果
- **核心內容**: Self-Refine Training Pipeline + 效果驗證
- **完成狀態**: 📋 待開發

#### [`week12_testing_qa/`](./week12_testing_qa/) - 測試與品質保證 📋
- **學習目標**: 建立測試框架，實作效能基準測試，設計 A/B Testing
- **核心內容**: 完整測試套件 + 性能基準
- **完成狀態**: 📋 待開發

---

### 🚀 **Module 7-9: 進階主題 (Week 13-16)**

#### [`week13_observability/`](./week13_observability/) - 監控與觀測 📋
- **學習目標**: 整合 AgentOps 監控，配置 Prometheus/Grafana，建立告警機制
- **完成狀態**: 📋 待開發

#### [`week14_deployment/`](./week14_deployment/) - 容器化與自動部署 📋
- **學習目標**: Docker 容器化，Kubernetes 部署，CI/CD Pipeline 設計
- **完成狀態**: 📋 待開發

#### [`week15_multi_agent/`](./week15_multi_agent/) - 團隊專案設計 📋
- **學習目標**: 設計多代理協作系統，實作角色分工機制，建立溝通協議
- **核心內容**: 智能客服系統、內容創作平台、數據分析助手
- **完成狀態**: 📋 待開發

#### [`week16_capstone_project/`](./week16_capstone_project/) - 專案展示與評估 📋
- **學習目標**: 完成專案部署，進行成果展示，同儕評估與反饋
- **完成狀態**: 📋 待開發

## 🔧 **技術架構特色**

### 統一導入機制
- **`import_helper.py`**: 解決所有週次的模組導入問題
- **自動路徑設置**: 一行代碼即可引用所有 `src` 模組
- **環境變數管理**: 自動載入 `.env` 配置

### 模組化設計
- **可重用組件**: `src/patterns/` 中的四大 Pattern 實作
- **靈活配置**: 支援不同難度等級和評估標準
- **擴展性**: 易於添加新的 Pattern 和功能

### 品質保證
- **SQLite 兼容性**: 自動修復 ChromaDB 版本問題
- **錯誤處理**: 完善的異常處理和降級機制
- **日誌追蹤**: 詳細的執行日誌和統計分析

## 📊 **學習進度與評量**

### 已完成模組 ✅
- **Week 01**: CrewAI 基礎概念 + 基礎反思機制
- **Week 02**: 進階反思系統 + 多輪迭代優化
- **Week 03**: Planning Pattern + Hierarchical 協作 (部分)

### 正在開發 🚧
- **Week 03**: 完善 Planning Pattern 功能
- **Week 04**: Planning Agent 進階功能

### 待開發模組 📋
- **Week 05-16**: 剩餘 12 週的完整實作

### 評量體系
- **5星 🌟**: 超越期望，具備創新和深度
- **3星 ⭐**: 符合基本要求，功能完整
- **1星 ⚠️**: 需要改進，功能不完整

## 🚀 **快速開始**

### 環境設置
```bash
# 1. 克隆專案並設置環境
cd work/labs
poetry install

# 2. 配置 API 金鑰
cp ../../.env.example ../../.env
# 編輯 .env 添加必要的 API 金鑰

# 3. 測試導入機制
poetry run python import_helper.py
```

### 運行示範
```bash
# Week 01: 基礎反思機制
cd week01_crewai_basics
poetry run python solution.py

# Week 02: 進階反思系統
cd week02_reflection  
poetry run python advanced_solution.py

# Week 03: Planning Pattern
cd week03_planning
poetry run python solution.py
```

## 🔄 **Pattern 關係圖**

```
Reflection ←→ Planning ←→ Tool Use ←→ Multi-Agent
    ↕            ↕          ↕           ↕
 Week 1-2    Week 3-4   Week 7-8   Week 15-16
 基礎+進階    協作流程    工具整合    團隊專案
```

## 📈 **下一步規劃**

### 短期目標 (1-2 週)
1. **完善 Week 03-04**: Planning Pattern 的完整實作
2. **開始 Week 05-06**: Flows 事件驅動機制
3. **建立測試框架**: 確保各週次品質

### 中期目標 (1 個月)
1. **完成 Tool Use Pattern**: Week 07-08 的工具整合
2. **實作 Knowledge & RAG**: Week 09-10 的知識庫系統
3. **建立 CI/CD 流程**: 自動化測試和部署

### 長期目標 (2-3 個月)
1. **完成所有 16 週**: 建立完整的學習體系
2. **Community 版本**: 開源發布供社群使用
3. **進階課程**: 基於實際應用的專業課程

---

**維護者**: CrewAI Course Team  
**最後更新**: 2025/01/05  
**版本**: v0.2.0 (完整架構版)