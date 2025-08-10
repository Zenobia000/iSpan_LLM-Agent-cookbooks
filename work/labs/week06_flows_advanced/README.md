# Week 06: AI 決策驅動的兩階段動態流程 (重構版)

## 🎯 學習目標

1.  **理解兩階段控制模式 (Two-Stage Control Pattern)**：學習如何將一個複雜的動態流程，拆解為一個「決策 Crew」和一個「執行 Crew」，以實現更穩定、更可靠的系統。
2.  **掌握決策代理 (Decision Agent)**：學習如何設計一個作為「決策者」的 `RoutingAgent`。這個 Agent 的核心職責不再是委派，而是**輸出結構化的 JSON**，作為後續流程的指令。
3.  **掌握 JSON 作為 Agent 之間的 API 契約**：學習如何透過 Prompt Engineering，強制 Agent 的輸出格式為可靠的 JSON，並在 Python 腳本中進行解析和驗證。
4.  **實現程式碼驅動的執行 (Code-Driven Execution)**：深刻理解如何利用 Python 腳本作為「協調者 (Orchestrator)」，根據決策 Agent 的輸出，動態地建立並執行相應的專家 `Crew`，從而完美結合 AI 的靈活性與程式碼的穩定性。

## ✨ 重構重點

這個版本將 `week06` 的原始 `solution.py` 進行了徹底的模組化重構，將「決策」和「執行」兩個階段的邏輯分離到各自的工廠函式中，使整體架構更加清晰和可維護。

### 新的文件結構

```
week06_flows_advanced_refactored/
├── main.py                     # 主執行入口，負責啟動流程
├── flow_controller.py          # 核心流程協調器，串聯決策與執行
├── agent_definitions.py        # 集中定義所有的 Agent (Router, Specialists)
├── decision_crew_factory.py    # 工廠：專門建立「決策 Crew」
└── execution_crew_factory.py   # 工廠：專門建立「執行 Crew」
```

### 重構帶來的好處

-   **高度模組化**：每個文件都有一個非常具體的職責，例如 `decision_crew_factory.py` 只關心如何建立決策 Crew，而 `execution_crew_factory.py` 只關心如何根據決策結果建立執行 Crew。
-   **清晰的流程**：`flow_controller.py` 現在像一個高階的指揮官，清晰地展示了「先決策，後執行」的兩階段流程，而不用關心每個階段的內部細節。
-   **極佳的可擴展性**：
    -   要增加一個新的專家角色（例如「銷售專員」）？只需在 `agent_definitions.py` 中新增 Agent，然後更新 `decision_crew_factory.py` 的 `prompt` 讓 `RoutingAgent` 知道有這個新選項即可。
    -   要修改決策邏輯？只需專注於 `decision_crew_factory.py`。
-   **可測試性更強**：可以獨立測試 `decision_crew_factory` 是否能生成正確的 `Crew`，以及 `execution_crew_factory` 是否能處理各種角色，而無需每次都運行完整的端到端流程。

## 🛠️ 技術重點

### 1. 流程協調器 (`flow_controller.py`)

`flow_controller.py` 是整個流程的大腦，它清晰地定義了兩步走的策略：

```python
# In flow_controller.py

def run_dynamic_flow(request: str, is_premium: bool):
    # 1. 建立並執行決策 Crew
    decision_crew = create_decision_crew(request, is_premium)
    decision_result_output = decision_crew.kickoff()

    # 2. 解析決策，並建立執行 Crew
    decision = json.loads(cleaned_json_str)
    execution_crew = create_execution_crew(
        decision["specialist_role"],
        decision["new_task_description"]
    )
    final_result = execution_crew.kickoff()
```

### 2. 工廠模式 (`*_factory.py`)

我們使用工廠模式來封裝 `Crew` 的建立邏輯。這使得 `flow_controller` 不再需要知道 `Crew`、`Task` 和 `Agent` 的具體配置細節，從而實現了更高層次的抽象。

```python
# In decision_crew_factory.py
def create_decision_crew(request: str, is_premium: bool) -> Crew:
    # ... 配置 task 和 agent
    return Crew(...)

# In execution_crew_factory.py
def create_execution_crew(specialist_role: str, task_description: str) -> Crew:
    # ... 根據角色查找 agent，配置 task
    return Crew(...)
```

這個重構後的架構不僅功能上與原版等效，而且在軟體工程的最佳實踐（如單一職責原則、高內聚低耦合）方面有了顯著的提升，為未來更複雜的流程擴展打下了堅實的基礎。
