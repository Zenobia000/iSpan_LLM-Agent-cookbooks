# Week 07: Tools & Memory (自訂工具開發)

## 學習目標

- 學習如何使用繼承 `BaseTool` (Class-based) 或 `@tool` decorator (Function-based) 來建立自訂工具。
- 比較兩種方法的優缺點與適用場景。
- 應用 `tool_template.py` 中的最佳實踐，包括 Pydantic 輸入驗證和錯誤處理。
- 實作一個能夠讀取本地檔案內容的 `FileReaderTool` (包含兩種版本)。
- 在 Agent 中使用自訂工具來完成特定任務。

## 核心概念：兩種工具定義方式

CrewAI 提供兩種主要方式來定義工具，開發者可以根據複雜度與個人偏好進行選擇。

### 1. Class-based: `BaseTool`
- **適用場景**:
  - 當工具邏輯複雜，需要管理狀態 (State)。
  - 需要更精細的控制，例如自訂 `args_schema` 來處理複雜輸入。
  - 希望將工具封裝成一個獨立、可重用的類別。
- **優點**: 結構清晰、易於擴展與維護。
- **缺點**: 程式碼較多，對於簡單功能略顯繁瑣。

### 2. Function-based: `@tool`
- **適用場景**:
  - 快速開發簡單、無狀態 (Stateless) 的工具。
  - 工具功能單一，只有一個函式即可完成。
- **優點**: 寫法簡潔、快速方便。
- **缺點**: 對於複雜邏輯或多步驟操作，較難管理。

## 實作步驟

1.  **擴充 `file_reader_tool.py`:**
    *   在 `work/labs/week07_tools_custom/` 中，我們將同時實作 Class-based 與 Function-based 兩種工具。
    *   **Class-based `FileReaderTool`**:
        *   參考 `src/templates/tool_template.py` 的結構。
        *   定義一個 `FileReaderInput` 的 Pydantic 模型，接收 `file_path` 作為參數。
        *   建立 `FileReaderTool` 類別，繼承自 `BaseTool`。
        *   在 `_run` 方法中，實作讀取檔案的邏輯。
        *   加入完整的 `try...except` 錯誤處理，以應對 `FileNotFoundError`、`PermissionError` 等常見問題。
    *   **Function-based `read_file_content`**:
        *   定義一個名為 `read_file_content` 的函式。
        *   在函式上方加上 `@tool("工具名稱")` 裝飾器。
        *   函式的 docstring 會被自動用作工具的 `description`。
        *   函式的參數 (`file_path: str`) 會被自動轉換為工具的輸入。
        *   同樣加入完整的錯誤處理邏輯。
2.  **建立 `solution.py`:**
    *   導入 `Agent`, `Task`, `Crew` 以及你剛剛建立的兩種工具 (`FileReaderTool` 和 `read_file_content`)。
    *   建立一個測試用的文字檔案 `sample_data.txt` (已提供)。
    *   **分別建立兩個 Agent 與 Crew**，一個使用 Class-based 工具，另一個使用 Function-based 工具，以便對照。
    *   **Crew 1 (Class-based)**:
        *   建立一個 `FileReadingAgent`，將 `FileReaderTool` 的實例加入其 `tools` 列表。
        *   建立一個 `Task`，指示 Agent 去讀取 `sample_data.txt`。
        *   建立並執行 Crew，觀察結果。
    *   **Crew 2 (Function-based)**:
        *   建立另一個 `FileReadingAgent`，將 `read_file_content` 函式 (即 `@tool` 裝飾的工具) 加入其 `tools` 列表。
        *   使用相同的 `Task`。
        *   建立並執行 Crew，比較其行為與結果是否一致。
