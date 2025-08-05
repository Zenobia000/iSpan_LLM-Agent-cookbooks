# Week 09: Knowledge & RAG

## 學習目標

- 了解 CrewAI 中 `KnowledgeBase` 的概念與用途。
- 學習如何從本地檔案建立一個知識庫。
- 實作一個使用 RAG (Retrieval-Augmented Generation) 技術的 Agent，使其能夠根據知識庫的內容來回答問題。

## 實作步驟

1.  **準備知識庫來源檔案:** 建立一個或多個文字檔案，作為 RAG 的知識來源。例如，`crewai_features.txt`。
2.  **建立 `solution.py`:**
    *   導入 `Agent`, `Task`, `Crew`, `KnowledgeBase`。
    *   使用 `KnowledgeBase(source_files=['./crewai_features.txt'])` 來建立一個知識庫實例。
    *   建立一個 `RAGAgent`，並將 `knowledge_base` 作為參數傳入。
    *   建立一個 `Task`，其 `description` 提出一個只有在知識庫檔案中才能找到答案的問題。
    *   建立並執行 Crew，觀察 Agent 是否成功地從知識庫中檢索資訊來回答問題。
