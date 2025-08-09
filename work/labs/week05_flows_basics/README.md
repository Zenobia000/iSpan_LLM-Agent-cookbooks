# Week 05: 外部腳本控制的確定性流程

## 🎯 學習目標

1.  **理解外部控制模式 (External Control Pattern)**：學習如何將 `CrewAI` 作為一個「函式庫」或「黑盒子」，由一個 **外部的 Python 腳本** 來進行流程控制。
2.  **掌握確定性路由 (Deterministic Routing)**：學習如何將 `if/elif/else` 等決策邏輯，放置在主執行腳本中，從而在建立和啟動 `Crew` **之前**，就已經確定了要執行的任務。
3.  **實現 Crew 的模組化**：學習將 `Crew` 的職責單一化，使其只專注於執行一個被明確指定的、單一的任務，而不是在 `Crew` 內部進行複雜的流程判斷。
4.  **區分「決策」與「執行」**：深刻理解在此模式下，**Python 腳本負責「決策」**（決定要執行哪個任務），而 **`Crew` 只負責「執行」**（高效地完成該任務），兩者職責清晰分離。

## 🛠️ 技術重點

### 1. 流程在 `main` 中定義

與 `week06` 將要介紹的「Agent 內部驅動」形成鮮明對比，本週的流程控制邏輯完全存在於 `if __name__ == "__main__"` 區塊（或由其呼叫的函式 `run_logistics_flow`）中。

```python
# The decision is made here, in pure Python, before any Crew is created.
if is_sunny and is_low_stock:
    task_to_execute = create_order_task(state)
else:
    task_to_execute = create_standby_task(state)

# The Crew is simple and linear, only executing the single task decided by the script.
logistics_crew = Crew(
    agents=[logistics_agent],
    tasks=[task_to_execute],
)
result = logistics_crew.kickoff()
```

它的特點是：

-   **先決策，後執行**：腳本首先獲取狀態，完成所有的 `if/else` 判斷，選擇一個具體的 `Task`，然後才將這個唯一的任務交給 `Crew` 去執行。
-   **Crew 的極簡化**：`Crew` 的結構非常簡單，通常只包含一個 Agent 和一個 Task。它的存在就是為了高效地完成一個原子性的操作。
-   **高度可預測和可測試**：由於決策邏輯是純 Python 程式碼，因此整個流程的走向是 100% 確定性的，並且非常容易進行單元測試。

### 2. Agent 作為「工具人」

在這個範例中，`logistics_agent` 的角色被進一步簡化。它甚至不知道還有其他可能的任務存在。它只是接收一個明確的指令（由 `Task` 的 `description` 定義），並執行它。這種模式非常適合將 AI 的能力封裝成一個個獨立的「微服務」。

## 🔄 與 Week 06 的關係

本週的範例是構建 Agentic 工作流的 **最穩健、最傳統** 的方式。它將 AI 的不確定性限制在單一 `Task` 的執行範圍內，而整個應用程式的流程控制仍然由開發者用可預測的程式碼來掌握。這對於將 AI 功能整合到現有的、對穩定性要求極高的企業級應用中，是一個非常實用的模式。

在 `week06` 中，我們將看到這個模式的 **終極演進**。我們將會把 `run_logistics_flow` 中的 `if/else` 決策邏輯，從 Python 程式碼中 **轉移** 到一個專門的 **「決策 Agent」** 中。屆時，您將學習到：

1.  **AI 負責決策**：一個 `RoutingAgent` 將負責分析需求，並輸出一個包含下一步指令的 **JSON**。
2.  **程式碼負責執行**：外部的 Python 腳本將解析這個 JSON，然後 **動態地** 建立一個只包含專家 Agent 的「執行 Crew」。

通過對比這兩週的範例，你將能深刻體會到，如何從一個**完全由程式碼控制**的確定性流程，演進到一個**由 AI 進行決策、再由程式碼進行可靠執行的**混合式動態流程。這是 `CrewAI` 在生產環境中最實用、最穩健的架構之一。
