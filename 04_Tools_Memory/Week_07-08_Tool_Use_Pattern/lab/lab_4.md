# 實驗 4：創建具備回退機制的進階工具

## 第一部分：使用外部 API 創建自訂工具

1.  **選擇一個公開 API**：
    -   尋找一個您感興趣且無需金鑰的公開 API。一些好的選擇包括：
        -   **Public APIs Repo**: [https://github.com/public-apis/public-apis](https://github.com/public-apis/public-apis)
        -   **JSONPlaceholder**: 用於測試的假數據 API。
        -   一個天氣 API、新聞 API 或電影資料庫 API。
2.  **創建您的工具**：
    -   參考 `custom_tool_exchange_rate` 範例。
    -   創建一個新的 Python 檔案。
    -   定義一個 `BaseTool` 子類別。
    -   為您的工具編寫一個清晰的 `name` 和 `description`。
    -   使用 Pydantic 的 `BaseModel` 定義 `args_schema`，以驗證您的工具所需的任何輸入。
    -   在 `_run` 方法中，使用 `requests` 函式庫來呼叫您選擇的 API，並處理其回應。
3.  **創建一個 Agent 來使用它**：
    -   設計一個其角色和目標需要用到您新工具的 Agent。
    -   創建一個任務來測試該 Agent 是否能成功調用您的工具。

## 第二部分：數據分析與 CodeInterpreterTool

1.  **獲取結構化數據**：
    -   修改您在第一部分創建的工具，使其返回一個結構化的數據字串（例如，CSV 格式或 JSON 格式的字串）。例如，如果您的工具獲取天氣數據，它可以返回 `"日期,最高溫,最低溫\n2024-01-01,10,5"`。
2.  **創建一個分析師 Agent**：
    -   從 `crewai_tools` 導入 `CodeInterpreterTool`。
    -   創建一個新的 Agent，例如 `Data Analyst Agent`。
    -   將 `CodeInterpreterTool` 加入其 `tools` 列表。
3.  **創建一個兩步驟的 Crew**：
    -   **任務 1**：讓您的第一個 Agent 使用其自訂工具來獲取數據。
    -   **任務 2**：將任務 1 的輸出作為上下文，交給 `Data Analyst Agent`。要求它對數據進行計算（例如，計算平均溫度、找出最大值）或將其轉換為另一種格式。
    -   觀察 `Data Analyst Agent` 如何使用 `CodeInterpreterTool` 來執行 Python 程式碼以完成分析。

## 第三部分：(挑戰) 實現工具的回退機制 (Fallback)

這是一個進階但非常重要的概念。

1.  **模擬主工具失敗**：
    -   在您的自訂 API 工具的 `_run` 方法中，人為地引入一個可能發生的錯誤。例如，您可以讓它在被調用時，有 50% 的機率拋出一個 `requests.exceptions.RequestException`。
2.  **創建一個備用工具**：
    -   從 `crewai_tools` 導入 `WebsiteSearchTool` 或 `SerperDevTool`。
    -   將這個搜索工具也加入到您的第一個 Agent 的 `tools` 列表中。
3.  **修改您的 Agent 或 Task**：
    -   **方案 A (在 Agent 中處理)**：修改 Agent 的 `backstory` 或 `goal`，明確指示它：「如果主要的 API 工具失敗，你應該嘗試使用網絡搜索工具作為備用方案來尋找答案。」
    -   **方案 B (在 Task 中處理)**：這比較困難，但可以透過 `Task` 的回調函數 `callback` 來實現。當任務失敗時，回調函數可以觸發一個新的、使用備用工具的任務。
4.  **測試您的回退機制**：
    -   多次運行您的 Crew。觀察當主工具「失敗」時，Agent 是否能夠智能地切換到備用工具來完成任務。分析其思考過程，看看它是如何做出這個決定的。

完成這個挑戰，代表您已掌握如何建構不僅功能強大，而且穩健、有彈性的 AI Agent。



