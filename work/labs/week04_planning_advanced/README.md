# Week 04: 進階規劃與動態執行

## 🎯 學習目標

1.  **理解資料驅動的規劃 (Data-Driven Planning)**：學習如何強制 LLM 輸出結構化的計畫 (JSON)，並使用 Pydantic 模型進行驗證和解析，而不是依賴不穩定的自然語言輸出。
2.  **掌握任務相依性 (Task Dependencies)**：學習如何定義任務之間的依賴關係，形成一個 **有向無環圖 (DAG - Directed Acyclic Graph)**，並依此順序執行任務。
3.  **實作風險評估 (Risk Assessment)**：學習如何設計一個專門的 `RiskAnalystAgent` 來識別計畫中的潛在風險，並提出緩解策略。
4.  **建立自訂執行循環 (Custom Execution Loop)**：拋棄單純的 `crew.kickoff()`，學習如何編寫一個「工作流協調器」，該協調器能讀取結構化計畫，並根據 DAG 依序、可控地執行每個任務。
5.  **了解動態重新規劃 (Dynamic Re-planning)**：在自訂執行循環中，學習如何埋設「鉤子 (Hook)」，以便在任務失敗或出現意外時，能夠觸發重新規劃的機制。

## 🛠️ 技術重點

### 1. Pydantic 模型：計畫的「骨架」

這是本次重構的基石。我們不再讓 Agent 自由發揮，而是給它一個嚴格的「模板」。

-   **`SubTask`**: 定義了單一任務的所有屬性，最關鍵的是 `id` 和 `dependencies: List[int]`。`dependencies` 欄位讓我們的計畫從一個線性列表，變成了一個「圖」。
-   **`Risk`**: 一個結構化的風險物件。
-   **`ProjectPlan`**: 整個計畫的根物件，包含了任務列表和風險列表。

通過要求 Agent 輸出符合這些 Pydantic 模型 schema 的 JSON，我們確保了計畫的 **可預測性和機器可讀性**。

### 2. 兩階段的 Crew 執行

-   **第一階段：規劃 (Planning)**
    -   我們運行一個小型的、專門的 `planning_crew`。
    -   其唯一目標就是讓 `PlannerAgent` 和 `RiskAnalystAgent` 協作，產生一份符合 `ProjectPlan` schema 的 JSON 字串。
    -   拿到這個 JSON 後，第一階段的 Crew 就解散了。我們接下來的工作將由 Python 程式碼主導。

-   **第二階段：執行 (Execution)**
    -   這一步在 `main` 函數的 `while` 迴圈中實現。
    -   我們不再一次性地運行一個大的 Crew，而是 **為每一個子任務，動態地創建一個小型的、一次性的 `single_task_crew`**。
    -   這種模式給了我們極大的靈活性和控制力。

### 3. DAG 執行器 (The DAG Runner)

`main` 函數中的 `while` 迴圈是我們實現的簡單版 DAG 執行器。其邏輯如下：

1.  **循環開始**：只要已完成的任務數量小於總任務數，就繼續循環。
2.  **尋找可執行的任務**：在每一輪循環中，遍歷所有任務，找出所有「相依性已滿足」（即其 `dependencies` 列表中的所有任務 ID 都已經在 `completed_task_ids` 集合中）且狀態為 `pending` 的任務。
3.  **執行任務**：
    -   為每個可執行的任務，動態組建一個只包含指定 Agent 的 `single_task_crew`。
    -   將其相依任務的輸出結果 (`task_outputs`) 作為 `context` 傳遞給當前任務。
    -   `kickoff()` 這個小型 Crew。
4.  **更新狀態**：任務成功後，將其 ID 加入 `completed_task_ids`，並將其結果存入 `task_outputs` 字典。
5.  **重複**：回到步驟 1，直到所有任務完成。

### 4. 動態重新規劃的鉤子 (Hook for Re-planning)

在我們的 DAG 執行器中，如果一個 `single_task_crew.kickoff()` 失敗了（例如，返回的結果包含 "error" 或 "failed"），這就是我們觸發重新規劃的 **最佳時機**。

```python
if "error" in result.lower():
    print("🚨 TRIGGERING RE-PLANNING LOGIC (DEMO) 🚨")
    # 在真實的 SOTA 系統中，你現在會：
    # 1. 收集失敗的上下文（哪個任務失敗了，為什麼失敗）。
    # 2. 再次調用 PlannerAgent，並將失敗的上下文作為新的輸入。
    # 3. 讓 PlannerAgent 產生一個全新的、修正過的計畫。
    # 4. 重新開始執行新計畫。
```

## 🚀 執行與驗證

當你運行 `solution.py` 時，你將在 console 中清晰地看到整個流程：

1.  **Phase 1**: 首先，`planning_crew` 會啟動，並輸出它正在生成計畫。成功後，你會看到計畫已被驗證的訊息。
2.  **Phase 2**: 接著，協調器會開始執行。你會看到任務 **按照其相依順序** 被逐一執行 (`🏃‍♂️ Executing Task X...`)。
3.  **Phase 3**: 所有任務成功完成後，程式會打印出最終結果。

這個範例展示了一個遠比簡單 `Crew` 更強大、更接近真實生產環境的 Agentic 工作流。它將 **「規劃」** 和 **「執行」** 徹底分離，並通過 **結構化資料** 和 **自訂協調器** 將它們完美地結合在一起。
