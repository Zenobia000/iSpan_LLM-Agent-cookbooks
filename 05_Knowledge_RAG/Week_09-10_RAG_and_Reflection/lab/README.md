# 實驗：第 9-10 週：RAG 與反思

## 目標

本實驗將讓您親手為 Agent 賦予特定領域的知識，並透過 **RAG (檢索增強生成)** 來應用這些知識。您還將學習如何使用 `guardrail` 來實現對 RAG 結果的反思性驗證，從而建立更可靠的 AI 系統。

## 指引

1.  導航至 `examples/rag_self_correction` 目錄。
2.  檢閱 `README.md` 和 `main.py` 檔案，以理解其基礎實現。
3.  遵循 `lab_5.md` 中的指引完成練習。

## 需重點關注的概念

-   **`KnowledgeBase` 的創建**：如何從一個簡單的本地文件創建一個可供 Agent 查詢的知識庫。
-   **自動化的 RAG 工具**：理解當您為 Agent 配置 `knowledge_base` 時，CrewAI 如何在幕後自動為其提供 `Knowledge Base Search` 工具。
-   **`guardrail` 作為反思機制**：`guardrail` 如何不僅僅是一個輸出格式的檢查器，而是可以被用來強制 Agent 重新評估其檢索策略，從而找到更相關的資訊。
-   **隱式 vs. 顯式查詢**：觀察 Agent 如何處理一個知識庫中沒有直接答案的查詢（「事假」），並透過 `guardrail` 的引導，找到相關性最高的答案（「年假」）。



