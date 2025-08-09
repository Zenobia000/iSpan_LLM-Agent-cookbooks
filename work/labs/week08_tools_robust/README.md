# Week 08: 打造生產級別的穩健工具 (Robust Tools)

## 🎯 學習目標

1.  **理解工具的脆弱性 (Tool Fragility)**：認識到在真實世界中，任何外部 API 呼叫都可能因為網路問題、速率限制或暫時性服務中斷而失敗。
2.  **掌握工具包裝器模式 (Tool Wrapper Pattern)**：學習如何建立一個通用的 `RobustToolWrapper`，在不修改原始工具的情況下，為其增加重試 (Retry) 和備援 (Fallback) 機制。
3.  **深入 `crewai` 工具的內部機制**：透過偵錯，深刻理解 `crewai` 中 `BaseTool` 的繼承、Pydantic 驗證和參數傳遞的複雜性。
4.  **實現程式化重試 (Programmatic Retry)**：學習如何編寫確定性的重試邏輯（例如，指數退避），以高效地處理暫時性錯誤。
5.  **掌握備援策略 (Fallback Strategy)**：學習如何設計和實作備援函式，確保在主要工具徹底失敗時，系統仍能提供有價值的回應，而不是完全崩潰。

## 🛠️ 技術重點

### 1. 最終的 `RobustToolWrapper` 設計

經過多次偵錯，我們最終得到了一個既符合 `crewai` 規範，又能應對其內部複雜性的穩健設計。

```python
class RobustToolWrapper(BaseTool):
    tool: BaseTool
    max_retries: int = 3
    fallback_func: Optional[Callable[..., Any]] = None

    def __init__(self, tool: BaseTool, **kwargs: Any):
        # 關鍵點 1: 在 super().__init__ 中傳遞所有必要欄位
        # 這確保了 Pydantic 驗證能夠通過，並且 Agent 能看到正確的工具元數據
        super().__init__(
            name=tool.name, 
            description=tool.description, 
            args_schema=tool.args_schema,
            tool=tool,
            **kwargs
        )

    def _run(self, **kwargs: Any) -> Any:
        # 關鍵點 2: 手動處理參數傳遞
        # crewai 可能會傳遞巢狀的參數，我們在此手動解析
        actual_args = kwargs.get('tool_input', kwargs)
        
        for attempt in range(self.max_retries):
            try:
                # 關鍵點 3: 直接呼叫被包裝工具的 _run 方法
                return self.tool._run(**actual_args)
            except Exception as e:
                # ... 重試與備援邏輯 ...
                if self.fallback_func:
                    return self.fallback_func(**actual_args)
                else:
                    raise e
```

#### 為什麼這個設計是有效的？

-   **符合 Pydantic 驗證**：在 `__init__` 中將所有必需的欄位（包括 `tool` 本身和 `kwargs`）傳遞給 `super()`，徹底解決了我們遇到的 `ValidationError`。
-   **正確的元數據繼承**：`Agent` 在選擇工具時，會看到 `Unstable Search` 的 `name` 和 `description`，而不是 `RobustToolWrapper` 的通用描述，這使得它的決策更準確。
-   **穩健的參數處理**：`_run` 方法不再信任 `crewai` 的自動參數解包，而是自己從 `kwargs` 中提取出真正的參數，確保了 `TypeError` 不再發生。

### 2. CrewAI 內建重試 vs. 程式化重試

這是一個核心概念，也是本週學習的重點。

| 特性 | CrewAI 內建重試 (LLM 驅動) | 我們的 `RobustToolWrapper` (程式碼驅動) |
|:---|:---|:---|
| **處理層級** | **Agent 的 LLM 推理層** | **工具執行的程式碼層** |
| **運作方式** | 將工具錯誤的堆疊追蹤返回給 `Agent`，由 LLM **思考** 下一步該怎麼辦。 | 在 `try/except` 區塊中**捕獲**異常，由程式碼**立即**執行重試或備援邏輯。 |
| **處理對象** | 各種錯誤（參數錯誤、邏輯錯誤、API 錯誤）。 | 專門處理**暫時性、可預期的錯誤**（如網路抖動、API 超時）。 |
| **速度與成本** | **慢且昂貴**。每一次「重試」都需要一次完整的 LLM call 來進行思考。 | **快且廉價**。重試是在程式內部完成的，不涉及 LLM。 |
| **可靠性** | **不確定**。LLM 可能會陷入無意義的重試循環，或做出非預期的決定。 | **100% 確定**。重試次數、等待時間和備援策略都由程式碼精準控制。 |
| **適用場景** | 作為處理未知錯誤、修正參數的最終防線。 | **生產環境中，呼叫任何外部 API 的標準配備。** |

**結論**：在一個生產級的 Agentic 系統中，兩者應該結合使用。`RobustToolWrapper` 作為第一道防線，處理掉 90% 的暫時性網路問題。只有當工具真的發生了無法透過重試解決的根本性錯誤時，包裝器才會將最終的錯誤拋出，交給 Agent 的 LLM 大腦去進行更高層次的、更昂貴的決策。

## 🔄 學習路徑總結

從 `week07` 的自定義工具，到 `week08` 的穩健工具包裝器，我們完成了一個關鍵的工程進階。我們不再僅僅是工具的「使用者」，而是成為了工具的「架構師」，能夠根據生產環境的需求，打造出穩定、可靠、可預測的 Agentic 組件。這個能力是區分業餘愛好者與專業 AI 工程師的關鍵。
