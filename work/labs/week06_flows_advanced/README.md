# Week 06: AI 決策驅動的兩階段動態流程

## 🎯 學習目標

1.  **理解兩階段控制模式 (Two-Stage Control Pattern)**：學習如何將一個複雜的動態流程，拆解為一個「決策 Crew」和一個「執行 Crew」，以實現更穩定、更可靠的系統。
2.  **掌握決策代理 (Decision Agent)**：學習如何設計一個作為「決策者」的 `RoutingAgent`。這個 Agent 的核心職責不再是委派，而是**輸出結構化的 JSON**，作為後續流程的指令。
3.  **掌握 JSON 作為 Agent 之間的 API 契約**：學習如何透過 Prompt Engineering，強制 Agent 的輸出格式為可靠的 JSON，並在 Python 腳本中進行解析和驗證。
4.  **實現程式碼驅動的執行 (Code-Driven Execution)**：深刻理解如何利用 Python 腳本作為「協調者 (Orchestrator)」，根據決策 Agent 的輸出，動態地建立並執行相應的專家 `Crew`，從而完美結合 AI 的靈活性與程式碼的穩定性。

## 🛠️ 技術重點

在偵錯過程中，我們發現 `Process.hierarchical` 在當前版本中存在穩定性問題。因此，我們將其重構為一個更強大、更具生產價值的模式。

### 1. 兩階段 Crew 模式：決策與執行的分離

這是本次重構的核心。我們不再依賴 `crewai` 內部的委派機制，而是將流程拆分為兩個獨立的、循序的 `Crew`：

-   **第一階段：決策 Crew**
    -   只包含一個 `RoutingAgent` 和一個 `routing_task`。
    -   其**唯一目標**是分析輸入，並輸出一個包含下一步指令的 JSON 物件，例如：`{"specialist_role": "Technical Support Specialist", "new_task_description": "..."}`。
    -   這個 `Crew` 壽命短，執行快，職責單一。

-   **第二階段：執行 Crew**
    -   在 Python 腳本中，等待並解析「決策 Crew」的 JSON 輸出。
    -   根據解析出的專家角色，**動態地**建立一個只包含該專家 Agent 的 `Crew`。
    -   執行由「決策 Crew」為專家量身打造的新任務。

### 2. `RoutingAgent`: 作為一個 JSON 微服務

`RoutingAgent` 的角色發生了根本性轉變：

-   它不再需要 `allow_delegation=True`。
-   它的 `goal` 和 `Task` 的 `expected_output` 被嚴格限定為**必須輸出一個 JSON 物件**。這使得 LLM 的輸出從不確定的自然語言，變成了可預測、可解析的結構化數據。

```python
# Agent 的目標是輸出 JSON
routing_agent = Agent(
    role="Intelligent Routing Agent",
    goal=dedent("""...
        Your final answer MUST be a JSON object with the keys 'specialist_role' and 'new_task_description'.
        """),
    ...
)

# Task 也期望得到 JSON
routing_task = Task(
    description=dedent("""..."""),
    expected_output=dedent("""\
        A JSON object containing two keys: 'specialist_role' and 'new_task_description'.
        Example: 
        {
          "specialist_role": "Technical Support Specialist",
          "new_task_description": "The user is unable to log in to their account. Please guide them through the password reset process."
        }
        """),
    agent=routing_agent,
)
```

### 3. Python 作為「協調者」

主執行函式 `run_dynamic_flow` 的邏輯現在變得非常清晰，它扮演著「協調者」的角色：

```python
def run_dynamic_flow(request: str, is_premium: bool):
    # 1. 執行決策 Crew，獲取 JSON 指令
    decision_crew = Crew(...)
    decision_result_str = str(decision_crew.kickoff())
    
    # 2. 解析 JSON 指令
    decision = json.loads(cleaned_json_str)
    specialist_role = decision['specialist_role']
    new_task_desc = decision['new_task_description']

    # 3. 根據指令，動態建立並執行「執行 Crew」
    specialist_agent = specialists[specialist_role]
    execution_crew = Crew(
        agents=[specialist_agent],
        tasks=[Task(description=new_task_desc, agent=specialist_agent)],
        ...
    )
    result = execution_crew.kickoff()
    print(f"Final Result: {result}")
```

## 🔄 Week 05 vs. Week 06 對比總結

| 特性 | Week 05 (外部腳本控制) | Week 06 (AI 決策 + 程式碼執行) |
|:---|:---|:---|
| **決策者** | **Python 腳本** (`if/else`) | **決策 Agent** (LLM 輸出的 JSON) + **Python 協調者** |
| **程式碼** | 決策邏輯在 `main` 中，冗長但明確 | 決策邏輯在 **Agent Prompt** 中，執行邏輯在協調函式中，**職責分離** |
| **適應性** | 低 (新增規則需改 `if/else`) | **高** (新增專家只需更新 `Prompt` 和專家列表) |
| **Crew 結構** | 單一、簡單的循序 `Crew` | **兩個簡單的循序 `Crew`** (決策 + 執行) |
| **適用場景** | 規則明確、不容出錯的業務流程 | 規則模糊、需要彈性應對，但又要求執行穩定可靠的複雜場景 |

通過這次從 `hierarchical` 到「兩階段模式」的重構，我們不僅解決了穩定性問題，還找到了一個在真實世界中更具實用性和擴展性的架構。這個模式是 `CrewAI` 應用於生產環境的關鍵。
