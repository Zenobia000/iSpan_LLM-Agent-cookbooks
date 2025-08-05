# Week 07: Tools & Memory (自訂工具開發)

## 學習目標

- 學習如何使用 `@tool` decorator 或繼承 `BaseTool` 來建立自訂工具。
- 應用 `tool_template.py` 中的最佳實踐，包括 Pydantic 輸入驗證和錯誤處理。
- 實作一個能夠讀取本地檔案內容的 `FileReaderTool`。
- 在 Agent 中使用自訂工具來完成特定任務。

## 實作步驟

1.  **建立 `file_reader_tool.py`:** 在 `work/labs/week07_tools_custom/` 資料夾中建立一個新檔案，用於存放我們的自訂工具。
2.  **實作 `FileReaderTool`:**
    *   參考 `src/templates/tool_template.py` 的結構。
    *   定義一個 `FileReaderInput` 的 Pydantic 模型，接收 `file_path` 作為參數。
    *   建立 `FileReaderTool` 類別，繼承自 `BaseTool`。
    *   在 `_run` 方法中，實作讀取檔案的邏輯。
    *   加入完整的 `try...except` 錯誤處理，以應對 `FileNotFoundError`、`PermissionError` 等常見問題。
3.  **建立 `solution.py`:**
    *   導入 `Agent`, `Task`, `Crew` 以及你剛剛建立的 `FileReaderTool`。
    *   建立一個測試用的文字檔案，例如 `sample_data.txt`。
    *   建立一個 `FileReadingAgent`，其 `goal` 是讀取並總結檔案內容，並將 `FileReaderTool` 加入其 `tools` 列表。
    *   建立一個 `Task`，其 `description` 指示 Agent 去讀取 `sample_data.txt`。
    *   建立並執行 Crew，觀察 Agent 是否成功使用你的自訂工具來完成任務。
