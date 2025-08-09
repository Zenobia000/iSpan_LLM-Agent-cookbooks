# CrewAI 專案開發任務清單 (WBS)

> **最後更新**: 2025年8月8日
> **狀態**: Phase 1-3 核心功能完成，Phase 4 進行中。

本文件使用工作分解結構 (Work Breakdown Structure) 來規劃 `crewai-agentic-course` 專案的開發時程。開發將優先專注於 `src/` 核心功能的 MVP，並同步推進 `work/` 各週的實作驗證。

---

## 📊 **當前專案狀態總覽**

| Phase | 內容 | 狀態 | 完成度 |
|-------|------|------|-------|
| **Phase 1** | 專案基礎與 Reflection Pattern (W1-2) | ✅ 完成 | 100% |
| **Phase 2** | 流程控制與 Planning Pattern (W3-4) | ✅ 完成 | 100% |
| **Phase 3** | 事件驅動與外部整合 (W5-8) | ✅ 完成 | 100% |
| **Phase 4** | RAG 與知識庫整合 (W9-10) | ✅ 完成 | 100% |
| **Phase 5** | 模型訓練與測試 (W11-12) | ⏳ 待開發 | 0% |
| **Phase 6** | 監控與部署 (W13-14) | ⏳ 待開發 | 0% |
| **Phase 7** | 綜合專案與架構重構 (W15-16) | ⏳ 待開發 | 5% |

### 🎯 **近期完成的重要里程碑**
- ✅ **SOTA 級進階規劃 (Week 04)**: 實現了基於 DAG 的結構化計畫與動態執行循環。
- ✅ **流程控制模式重構 (Week 05-06)**: 徹底區分了「程式碼驅動」與「語言驅動」兩種流程控制典範。
- ✅ **核心工具鏈重構**: 將 `search` 和 `scrape` 功能整合到單一、高效的 `TavilySearchTool` 中。
- ✅ **進階 RAG 模式探索 (Week 09-10)**: 成功實作了包含「自我反思」、「查詢擴展」與「HyDE」三種 SOTA RAG 策略，並整合 `ragas` 進行量化評估。
- ✅ **目錄結構完整**: 已建立全部 16 週的 `work/labs` 目錄結構。

### 🚀 **當前工作重點 (Next Steps)**
- 🚀 **啟動 Phase 5 (訓練與測試)**: 開始 `week11_training_pipeline` 的規劃與開發。
- 🚀 **完善 Week 15 (多代理協作)**: 實作一個涵蓋多種 Agentic Pattern 的綜合協作範例。
- ⏳ **啟動 Phase 6 (監控與部署)**: 規劃 `week13_observability` 的整合方案。

---

## ✅ Phase 1: 專案基礎與核心框架 (對應 Syllabus Week 1-2) - **已完成**

### 1.1. Epic: 環境設定與工具鏈 - **✅ 完成**
- [x] **Task 1.1.1:** 完成 Poetry 環境初始化與依賴安裝。
- [x] **Task 1.1.2:** 設定 `pre-commit` hooks (black, flake8, mypy)。
- [x] **Task 1.1.3:** 建立並填寫 `.env` 檔案以管理 API 金鑰。

### 1.2. Epic: `src/core` 核心抽象層 MVP - **✅ 完成**
- [x] **Task 1.2.1:** 建立 `src/core` 各模組基礎結構。
- [x] **Task 1.2.2:** 完成核心工具 `TavilySearchTool` 的整合與重構。

### 1.3. Epic: Reflection Pattern MVP (對應 `work/labs/week01_crewai_basics`) - **✅ 完成**
- [x] **Task 1.3.1:** 實作基礎天氣預報 Crew。
- [x] **Task 1.3.2:** 新增 `Critique_Agent` 來評估報告品質。
- [x] **Task 1.3.3:** 將 `Critique_Agent` 整合進 Crew，形成反思流程。
- [x] **Task 1.3.4:** 撰寫 `work/labs/week01_crewai_basics/README.md`。

### 1.4. Epic: 進階反思模式與工廠設計 (對應 `work/labs/week02_reflection`) - **✅ 完成**
- [x] **Task 1.4.1:** 實作進階反思工作流程。
- [x] **Task 1.4.2:** 建立標準 Self-Refine 示範。
- [x] **Task 1.4.3:** 實作工廠函數設計模式。
- [x] **Task 1.4.4:** 完善文檔與對比分析。

---

## ✅ Phase 2: 流程控制與規劃能力 (對應 Syllabus Week 3-4) - **已完成**

### 2.1. Epic: `src/patterns/planning` 規劃模式元件 - **✅ 完成**
- [x] **Task 2.1.1:** 在 `src/patterns/planning/` 中定義 `PlannerAgent` 的角色與目標。

### 2.2. Epic: Crew 協作流程 (對應 `work/labs/week03_planning`) - **✅ 完成**
- [x] **Task 2.2.1:** 設計一個需要多步驟協作的場景。
- [x] **Task 2.2.2:** 建立一個包含 `PlannerAgent` 的 Crew，並設定 `process=Process.Hierarchical`。
- [x] **Task 2.2.3:** 驗證 `PlannerAgent` (作為 manager) 能夠成功地將任務委派給其他 Agents。
- [x] **Task 2.2.4:** 撰寫 `work/labs/week03_planning/README.md`。

### 2.3. Epic: `work/labs/week04_planning_advanced` - **✅ 完成**
- [x] **Task 2.3.1:** 讓 `PlannerAgent` 能夠理解任務之間的相依性 (DAG)。
- [x] **Task 2.3.2:** 賦予系統動態重新規劃的能力 (透過自訂執行循環)。
- [x] **Task 2.3.3:** 讓 `PlannerAgent` 能夠進行風險評估。
- [x] **Task 2.3.4:** 在 `work/labs/week04_planning_advanced/` 中，實作 SOTA 級的規劃與執行範例。
- [x] **Task 2.3.5:** 撰寫 `work/labs/week04_planning_advanced/README.md`。

---

## ✅ Phase 3: 事件驅動與外部整合 (對應 Syllabus Week 5-8) - **已完成**

### 3.1. Epic: Flows 事件驅動 (對應 `work/labs/week05_flows_basics` & `week06_flows_advanced`) - **✅ 完成**
- [x] **Task 3.1.1:** 移除自訂的 `@flow` decorator，回歸 CrewAI 原生功能。
- [x] **Task 3.1.2:** 在 `work/labs/week05_flows_basics/` 中，實作「外部腳本控制」的確定性流程。
- [x] **Task 3.1.3:** 在 `work/labs/week06_flows_advanced/` 中，實作「Agent 內部驅動」的動態流程。

### 3.2. Epic: 自訂工具與 RAG (對應 `work/labs/week07_tools_custom`) - **✅ 完成**
- [x] **Task 3.2.1:** 開發一個自訂工具（檔案讀取工具 `FileReaderTool`）。
- [x] **Task 3.2.2:** 在 `work/labs/week07_tools_custom/` 中進行實作。

### 3.3. Epic: 容錯工具系統 (對應 `work/labs/week08_tools_robust`) - **✅ 完成**
- [x] **Task 3.3.1:** 實作 `RobustToolWrapper` 類別，支援重試機制與 fallback 策略。
- [x] **Task 3.3.2:** 在 `work/labs/week08_tools_robust/` 中建立容錯工具使用示範。
- [x] **Task 3.3.3:** 撰寫工具容錯最佳實踐文檔。

---

## ✅ Phase 4: RAG 與知識庫整合 (對應 Syllabus Week 9-10) - **已完成**

### 4.1. Epic: 基礎 RAG (對應 `work/labs/week09_knowledge_rag`) - **✅ 完成**
- [x] **Task 4.1.1:** 實作使用 `Knowledge` 的 RAG Crew。
- [x] **Task 4.1.2:** 在 `work/labs/week09_knowledge_rag/` 中實作。

### 4.2. Epic: RAG 品質反思與進階模式 (對應 `work/labs/week10_rag_reflection`) - **✅ 完成**
- [x] **Task 4.2.1:** 實作「自我反思」RAG 循環 (`solution.py`)，包含檢索、評估與查詢優化。
- [x] **Task 4.2.2:** 實作「多階段查詢擴展」RAG 流程 (`solution_advanced.py`)。
- [x] **Task 4.2.3:** 整合 `ragas` 函式庫，對 RAG 流程進行量化評估。
- [x] **Task 4.2.4:** 實作「假設性文件生成 (HyDE)」RAG 流程 (`solution_hyde.py`)。
- [x] **Task 4.2.5:** 撰寫三種進階 RAG 模式的比較與總結 `README.md`。

---

## ⏳ Phase 5: 模型訓練與測試 (對應 Syllabus Week 11-12) - **待開發**

### 5.1. Epic: CrewAI 訓練管道 (對應 `work/labs/week11_training_pipeline`) - **⏳ 待開發**
- [ ] **Task 5.1.1:** 實作訓練數據收集與格式化流程。
- [ ] **Task 5.1.2:** 建立 CrewAI 訓練執行與驗證機制。

### 5.2. Epic: 測試與品質保證 (對應 `work/labs/week12_testing_qa`) - **⏳ 待開發**
- [ ] **Task 5.2.1:** 實作 Agent 與 Crew 的單元測試框架。
- [ ] **Task 5.2.2:** 建立效能基準測試與 A/B Testing 機制。

---

## ⏳ Phase 6: 監控與部署 (對應 Syllabus Week 13-14) - **待開發**

### 6.1. Epic: 監控與觀測 (對應 `work/labs/week13_observability`) - **⏳ 待開發**
- [ ] **Task 6.1.1:** 整合 AgentOps 監控與 Prometheus/Grafana 儀表板。
- [ ] **Task 6.1.2:** 建立告警機制與成本分析功能。

### 6.2. Epic: 容器化與 CI/CD (對應 `work/labs/week14_deployment`) - **⏳ 待開發**
- [ ] **Task 6.2.1:** 實作 Docker 容器化與 Kubernetes 部署配置。
- [ ] **Task 6.2.2:** 建立 GitHub Actions CI/CD Pipeline。

---

## ⏳ Phase 7: 綜合專案與架構重構 (對應 Syllabus Week 15-16) - **待開發**

### 7.1. Epic: Multi-Agent 綜合專案 (對應 `work/labs/week15_multi_agent`) - **🔄 規劃中**
- [x] **Task 7.1.1:** 撰寫 `work/labs/week15_multi_agent/README.md`。
- [ ] **Task 7.1.2:** **(待辦)** 實作一個涵蓋多種 Agentic Pattern 的多代理協作示範 `solution.py`。
- [ ] **Task 7.1.3:** **(待辦)** 建立 `work/labs/week16_capstone_project/` 專案範本與評量標準。

### 7.2. Epic: `src/core` 抽象層重構 - **⏳ 待開發**
- [ ] **Task 7.2.1:** 在 `src/core/agents/` 中，建立可重用的 Agent 原型。
- [ ] **Task 7.2.2:** 在 `src/core/crews/` 中，實作 `CrewFactory`。
