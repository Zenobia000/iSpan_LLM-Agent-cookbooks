# Week 03: 基礎規劃與階層式流程

## 🎯 學習目標

1.  **理解階層式流程 (Hierarchical Process)**：學習 `CrewAI` 中 `Process.hierarchical` 的兩種實現方式。
2.  **掌握任務分解 (Task Decomposition)**：學習如何設計規劃 Agent 進行任務分解和協調。
3.  **實作委派機制 (Delegation)**：觀察管理者如何將任務委派給專業 Worker Agents。
4.  **建立清晰的團隊結構**：學習如何組織不同角色的 Agents 進行協同工作。

## 📁 文件說明

本週提供了兩種不同的實現方式：

### 1. `solution.py` - 自動管理器模式
- 使用 `Process.hierarchical`
- CrewAI 自動創建 "Crew Manager" 來協調任務
- 只需定義 worker agents (researcher, writer)
- 系統自動處理任務委派和協調

### 2. `solution_sequential.py` - 顯式規劃器模式
- 使用 `Process.sequential`
- 手動定義 Planner Agent
- 顯式的任務規劃和依賴關係
- 更細粒度的控制和自定義

## 🛠️ 技術重點

### 1. Hierarchical Process 的兩種模式

#### A. 自動管理器模式 (solution.py)
```python
crew = Crew(
    agents=[researcher, writer],  # 只包含 worker agents
    tasks=[research_task, writing_task],
    process=Process.hierarchical,  # CrewAI 自動創建管理器
    manager_llm="gpt-4o-mini",     # 管理器使用的 LLM
    verbose=True,
)
```

**特點：**
- CrewAI 自動創建 "Crew Manager"
- 無需手動定義管理器 Agent
- 系統自動處理任務委派
- 適合快速原型開發

#### B. 顯式規劃器模式 (solution_sequential.py)
```python
crew = Crew(
    agents=[planner, researcher, writer],  # 包含所有 agents
    tasks=[plan_task, research_task, writing_task],
    process=Process.sequential,  # 順序執行
    verbose=True,
)
```

**特點：**
- 手動定義 Planner Agent
- `allow_delegation=True` 啟用委派能力
- 顯式的任務依賴關係設定
- 更細粒度的控制

### 2. Agent 設計模式

#### Manager/Planner Agent
```python
def planner_agent(self) -> Agent:
    return Agent(
        role="Project Planner",
        goal="Break down complex goals into actionable plans",
        backstory="An experienced project manager...",
        allow_delegation=True,  # 關鍵：啟用委派功能
        verbose=True,
    )
```

#### Worker Agents
```python
def researcher_agent(self) -> Agent:
    return Agent(
        role="Research Analyst",
        goal="Gather comprehensive information",
        tools=[self.search_tool],  # 專業工具
        verbose=True,
    )
```

### 3. 任務依賴關係管理

#### 自動管理器模式
```python
# 設定任務依賴
writing_task.context = [research_task]  # 寫作依賴研究結果
```

#### 顯式規劃器模式
```python
# 設定複雜的依賴關係
research_task.context = [plan_task]              # 研究依賴規劃
writing_task.context = [plan_task, research_task] # 寫作依賴規劃和研究
```

## 🚀 執行方式

### 執行自動管理器版本
```bash
cd work/labs/week03_planning
uv run python solution.py
```

### 執行顯式規劃器版本
```bash
cd work/labs/week03_planning
uv run python solution_sequential.py
```

## 📊 比較分析

| 特性 | 自動管理器模式 | 顯式規劃器模式 |
|------|----------------|----------------|
| **設置複雜度** | 簡單 | 中等 |
| **控制粒度** | 粗粒度 | 細粒度 |
| **自定義能力** | 有限 | 高度自定義 |
| **適用場景** | 快速原型、標準流程 | 複雜工作流程、特定需求 |
| **學習曲線** | 平緩 | 陡峭 |

## 🔍 關鍵觀察

### 從執行日誌中可以看到：

1. **自動管理器模式**：
   - 系統自動創建 "Crew Manager"
   - 管理器自動委派任務給 "Research Analyst" 和 "Technical Writer"
   - 無縫的任務協調和執行

2. **任務委派過程**：
   ```
   Agent: Crew Manager
   Tool: delegate_work_to_coworker
   Args: {'task': 'Conduct comprehensive research...', 'coworker': 'Research Analyst'}
   ```

3. **Agent 協作**：
   - Research Analyst 使用 TavilySearchTool 進行資訊收集
   - Technical Writer 基於研究結果創建博客文章
   - Crew Manager 協調整個流程
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
