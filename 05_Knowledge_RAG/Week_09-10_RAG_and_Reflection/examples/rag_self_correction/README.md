# 範例：RAG 自我修正 (RAG with Self-Correction)

本範例旨在展示如何利用 **檢索增強生成 (RAG)** 為 Agent 提供專業知識，並結合 `guardrail` 來實現對檢索結果的反思與修正。

## 1. 目的

在許多情況下，僅僅讓 Agent 從知識庫中檢索一次資訊可能是不夠的。檢索到的內容可能不完整或不夠相關。本範例的目標是創建一個能夠：
1.  從本地文件創建一個 `KnowledgeBase`。
2.  讓 Agent 使用這個知識庫來回答問題。
3.  使用 `Task` 的 `guardrail` 參數來驗證 Agent 的回答。如果回答不符合標準（暗示著檢索的內容不佳），則迫使 Agent 重新執行任務，從而進行自我修正。

## 2. 如何運行

1.  **安裝必要的函式庫：**
    ```bash
    # crewai-tools for the FileReadTool
    pip install crewai crewai-tools
    ```

2.  **創建知識庫文件：**
    -   在 `rag_self_correction` 目錄下，創建一個名為 `company_policy.md` 的檔案。
    -   將以下內容複製到該檔案中：
        ```markdown
        # 公司休假政策

        ## 年假
        所有全職員工每年享有 15 天的帶薪年假。

        ## 病假
        員工每年可請 5 天帶薪病假。
        ```

3.  **執行腳本：**
    ```bash
    python main.py
    ```

## 3. 程式碼邏輯詳解

-   **`main.py`**:
    1.  **知識庫創建**：
        -   我們使用 `KnowledgeBase` 類別，並傳入知識庫來源檔案 `company_policy.md` 的路徑來將其初始化。
        -   `FileReadTool` 被用來讀取這個文件。
    2.  **專家 Agent**：
        -   我們創建一個 `PolicyExpert` 代理。
        -   最關鍵的一步是，在創建 Agent 時，我們將 `knowledge_base` 的實例傳遞給它。這會自動為該 Agent 配備一個 `Knowledge Base Search` 工具。
    3.  **帶有 Guardrail 的任務**：
        -   任務要求 Agent 回答關於「事假 (personal leave)」的問題。請注意，我們的知識庫文件中並**沒有**直接提及「事假」。
        -   `guardrail` 參數被設置為一個 lambda 函數 `lambda out: "年假" in out`。這個護欄要求 Agent 的最終回答中必須包含「年假」這個詞。
    4.  **自我修正循環**：
        -   **第一次嘗試**：當 Agent 第一次執行任務時，它會在知識庫中搜索「事假」。由於找不到直接匹配，它可能會給出一個模糊的答案，例如「公司政策沒有提及事假」。
        -   **Guardrail 觸發**：這個初步答案不包含「年假」，因此 `guardrail` 驗證失敗。
        -   **第二次嘗試**：CrewAI 指示 Agent 重新執行任務。這次，Agent 會在其推理中意識到第一次的嘗試失敗了，並且它需要找到包含「年假」的資訊。這會促使它以不同的方式（可能搜索「休假」或「假期」）來查詢知識庫，從而找到相關的「年假」政策，並給出一個滿足 `guardrail` 條件的、更有幫助的答案。

## 4. 預期輸出

您將在詳細日誌中看到 Agent 執行了兩次任務。第一次的輸出會比較簡短且不完整。在 `guardrail` 觸發後，第二次的輸出將會是一個更完整、更符合預期的答案，其中會提及可以將年假作為事假使用。這清晰地展示了 RAG 的自我修正過程。



