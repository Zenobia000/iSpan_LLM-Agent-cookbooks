# Week 03: 基礎規劃與階層式流程

## 🎯 學習目標

1.  **理解階層式流程 (Hierarchical Process)**：學習 `CrewAI` 中 `Process.hierarchical` 的運作方式，了解如何設定一個「管理者 Agent」來協調「工作者 Agents」。
2.  **掌握任務分解 (Task Decomposition)**：學習如何設計一個 `PlannerAgent`，使其能夠接收一個高階目標，並將其分解為一系列具體的、可執行的子任務。
3.  **實作基礎的委派 (Delegation)**：觀察管理者 Agent 如何將分解後的任務，準確地委派給具有對應能力的 Worker Agents。
4.  **建立清晰的團隊結構**：學習如何定義不同角色的 Agents (Planner, Researcher, Writer)，並將它們組織在一個 Crew 中協同工作。

## 🛠️ 技術重點

### 1. `Process.hierarchical`

這是 `CrewAI` 中用於實現管理者/工作者模式的核心機制。當 `process` 被設定為 `hierarchical` 時：

-   Crew 中需要有一個（或多個）Agent 能夠扮演 **管理者 (Manager)** 的角色。
-   管理者會接收初始的、高階的任務。
-   它會將這個高階任務分解成子任務，並將這些子任務 **委派 (delegate)** 給 Crew 中的其他 **工作者 (Worker)** Agents。
-   管理者會監督整個流程，並在所有子任務完成後，整合結果並產出最終的答案。

### 2. `PlannerAgent` 的設計

在本週的範例中，`planner` Agent 就是我們的管理者。它的設計重點在於：

-   **`role` 和 `goal`**：明確定義其職責是「規劃」和「分解任務」。
-   **`allow_delegation=True`**：這個參數是 **必須的**，它賦予了 Agent 委派任務給他人的能力。
-   **初始任務 (`planning_task`)**：我們提供給 `planner` 的第一個任務，其 `description` 必須清晰地引導它去思考「如何分解」以及「可以委派給誰」。

### 3. 簡化的任務定義

為了專注於「規劃」這個核心概念，本週的 `solution.py` 做了以下簡化：

-   **只定義初始任務**：在 `Crew` 的 `tasks` 列表中，我們只放入了 `planning_task`。其他的任務（如 `research_task`, `write_task`）雖然有定義，但它們將由 `planner` 在執行過程中 **動態地創建並委派**。
-   **清晰的期望輸出**：`planning_task` 的 `expected_output` 明確要求一個「結構化的任務列表」，這為 `planner` 提供了清晰的行動指南。

## 🔄 與 Week 04 的關係

本週的範例是理解「規劃模式」的 **第一步**。我們專注於最基礎的任務分解與委派流程。

在 `week04_planning_advanced` 中，我們將會在這個基礎上，探討更複雜、更真實的場景，包括：

-   **任務相依性 (Task Dependencies)**：如何讓 Planner 理解「任務 B 必須在任務 A 完成後才能開始」。
-   **風險評估 (Risk Assessment)**：如何讓 Planner 識別潛在的風險並規劃應對策略。
-   **動態重新規劃 (Dynamic Re-planning)**：當意外情況發生時，Planner 如何調整原有的計畫。

通過這兩週的學習，你將能完整地掌握 `CrewAI` 中的 Planning Pattern。

## 📝 實作要求

1.  **理解 `solution.py` 的結構**：
    a.  觀察 `planner`, `researcher`, `writer` 三個 Agent 的角色定義。
    b.  注意 `planner` 的 `allow_delegation` 設置為 `True`。
    c.  分析 `planning_task` 是如何引導 `planner` 進行任務分解的。
    d.  理解為什麼在 `Crew` 的初始化中，只需要傳入 `planning_task`。
2.  **執行程式**：運行 `solution.py`。
3.  **觀察輸出**：在 console 的輸出中，仔細觀察 `planner` 是如何思考、分解任務，並將子任務（如研究、寫作）委派給 `researcher` 和 `writer` 的。
