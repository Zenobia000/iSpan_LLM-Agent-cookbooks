# 範例：自我批判循環 (Self-Critique Loop)

本範例展示了 CrewAI 中的 **反思模式 (Reflection Pattern)**。

## 1. 目的

本範例旨在展示如何建立一個多代理系統。其中一個代理 (`Weather Reporter`) 生成內容，而第二個代理 (`Summary Reviewer`) 則對該內容進行批判，並提供回饋，以供最終的修訂版本參考。

這種「生成-批判-精煉」的循環，是創建更穩健、更可靠 AI 系統的核心概念。

## 2. 如何運行

1.  **設定您的環境：**
    -   確保您已安裝 `crewai` 和 `crewai-tools`：
        ```bash
        pip install crewai crewai-tools
        ```
    -   在 `main.py` 檔案或您的系統中，將 `OPENAI_API_KEY` 設置為環境變數。

2.  **執行腳本：**
    ```bash
    python main.py
    ```

## 3. 程式碼邏輯詳解

-   **`main.py`**:
    1.  **Agent 定義**：定義了兩個代理：
        -   `weather_reporter`：其目標是創建初始的天氣摘要。
        -   `summary_reviewer`：其目標是審查摘要、提供評分並提出具體的改進建議。這是我們的「反思」代理。
    2.  **Task 定義**：三個任務協調了整個工作流程：
        -   `report_task`：指派給 `weather_reporter` 以生成初稿。
        -   `review_task`：指派給 `summary_reviewer`。至關重要的是，它將 `report_task` 的輸出作為其 `context`。這使其能夠「看到」並評估初稿。
        -   `revision_task`：指派回 `weather_reporter`。它將前兩個任務的輸出都作為其 `context`，使其能夠根據具體回饋來修訂其工作。
    3.  **Crew 執行**：將代理和任務組裝成一個 `Crew`，並採用 `Process.sequential` 順序流程，以確保任務按正確順序執行。最後，將印出經過精煉的最終輸出。

## 4. 預期輸出

當您運行此腳本時，您將看到每個代理思考過程的詳細、逐步日誌 (`verbose=2`)。最終的輸出將是精煉後的天氣摘要，該摘要已整合了審查者代理的建議。
