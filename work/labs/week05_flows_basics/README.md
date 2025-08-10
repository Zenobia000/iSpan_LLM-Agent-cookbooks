# Week 05: 外部腳本控制的確定性流程 (重構版)

## 🎯 學習目標

1.  **理解外部控制模式 (External Control Pattern)**：學習如何將 `CrewAI` 作為一個「函式庫」或「黑盒子」，由一個 **外部的 Python 腳本** 來進行流程控制。
2.  **掌握確定性路由 (Deterministic Routing)**：學習如何將 `if/elif/else` 等決策邏輯，放置在主執行腳本中，從而在建立和啟動 `Crew` **之前**，就已經確定了要執行的任務。
3.  **實現 Crew 的模組化**：學習將 `Crew` 的職責單一化，使其只專注於執行一個被明確指定的、單一的任務，而不是在 `Crew` 內部進行複雜的流程判斷。
4.  **區分「決策」與「執行」**：深刻理解在此模式下，**Python 腳本負責「決策」**（決定要執行哪個任務），而 **`Crew` 只負責「執行」**（高效地完成該任務），兩者職責清晰分離。

## ✨ 重構重點

這個版本將 `week05` 的原始 `solution.py` 進行了模組化重構，旨在提高程式碼的可讀性、可維護性和可擴展性。這是在真實專案中組織程式碼的更佳實踐。

### 新的文件結構

```
week05_flows_basics_refactored/
├── main.py               # 主執行入口，負責啟動流程
├── flow_controller.py    # 核心流程控制器，包含 if/else 決策邏輯
├── agent_definition.py   # 集中定義所有的 Agent
└── task_factory.py       # 任務工廠，根據需求動態建立 Task
```

### 重構帶來的好處

-   **職責分離 (Separation of Concerns)**：
    -   `main.py`: 只關心啟動哪個流程。
    -   `flow_controller.py`: 只關心業務邏輯和決策。
    -   `agent_definition.py`: 只關心 Agent 的角色、目標和背景故事。
    -   `task_factory.py`: 只關心如何根據輸入參數建立具體的任務。
-   **可讀性更高**：每個文件的目的都非常明確，容易理解。
-   **更容易擴展**：
    -   如果需要新增 Agent，只需修改 `agent_definition.py`。
    -   如果需要新增任務類型，只需在 `task_factory.py` 中增加新的函式。
    -   如果決策邏輯變複雜，只需專注於修改 `flow_controller.py`。
-   **可測試性更強**：可以針對 `task_factory` 或 `flow_controller` 編寫獨立的單元測試，而無需啟動完整的 `CrewAI` 流程。

## 🛠️ 技術重點

### 1. 流程在 `flow_controller.py` 中定義

流程控制邏輯被封裝在 `run_logistics_flow` 函式中。

```python
# In flow_controller.py

def run_logistics_flow(stock_level: int):
    # ...
    if is_sunny and is_low_stock:
        task_to_execute = create_order_task(state)
    else:
        task_to_execute = create_standby_task(state)
    # ...
    logistics_crew = Crew(
        agents=[logistics_agent],
        tasks=[task_to_execute],
    )
    result = logistics_crew.kickoff()
```

### 2. 主執行文件 `main.py`

`main.py` 的職責被簡化為導入和執行流程。

```python
# In main.py

from flow_controller import run_logistics_flow

if __name__ == "__main__":
    run_logistics_flow(stock_level=30)
    run_logistics_flow(stock_level=100)
```

## 🔄 與 Week 06 的關係

這次重構為 `week06` 的動態流程打下了堅實的基礎。通過將決策邏輯 (`flow_controller`) 和執行細節 (`task_factory`) 分離，在下一階段，我們可以更輕易地將 `flow_controller.py` 中的 `if/else` 邏輯替換為一個「決策 Agent」，而無需大幅改動專案的其他部分。
