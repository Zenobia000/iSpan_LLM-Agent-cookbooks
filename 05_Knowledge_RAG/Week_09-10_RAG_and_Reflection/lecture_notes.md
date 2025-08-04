# 模組 5：知識庫與 RAG

***

### **講座：第 9-10 週**

**授課者：** Dr. Cortex

**主題：** 賦予 Agent 領域知識：檢索增強生成 (RAG) 與反思性驗證

***

#### **1. 第一原理：從通用知識到領域專長**

通用的大型語言模型（LLMs）擁有廣泛的世界知識，但它們缺乏特定領域的、私有的、或即時的深度知識。一個僅依賴其預訓練數據的 Agent，無法成為真正的領域專家。

這裡的**第一原理**是**知識賦予 (Knowledge Endowment)**。要讓一個 Agent 在特定任務上表現出色，我們必須為其提供一個可供查詢的、權威的**知識庫 (Knowledge Base)**。Agent 的能力不再僅僅是其內在模型的直接產物，而是其模型與外部知識庫互動的結果。

---

#### **2. 基礎知識：CrewAI 的知識系統**

CrewAI 透過其**知識 (Knowledge)** 系統，將檢索增強生成 (RAG) 的能力無縫整合到 Agent 的工作流程中。

##### **2.1 `KnowledgeBase`**

`KnowledgeBase` 是 RAG 的核心。它接收一個或多個知識來源，在內部對其進行處理（分塊、嵌入），並提供一個語義搜索接口。

-   **知識來源 (Knowledge Sources)**：CrewAI 支援多種數據格式作為知識來源，包括：
    -   本地檔案：`.txt`, `.md`, `.pdf`, `.csv`, `.docx` 等。
    -   網站內容：透過 URL 直接爬取。
    -   字串內容：直接將文字內容作為知識。
-   **嵌入器 (Embedder)**：`KnowledgeBase` 使用嵌入模型（如 OpenAI, Cohere 等）將文本塊轉換為向量，以便進行語義相似度搜索。您可以配置使用哪個嵌入提供商。

##### **2.2 將知識賦予 Agent**

您可以透過兩種方式將知識庫與 Agent 關聯起來：

1.  **在 `Crew` 層級**：
    ```python
    crew = Crew(
        knowledge_base=my_knowledge_base,
        ...
    )
    ```
    在此配置下，`my_knowledge_base` 將被 crew 中的所有 Agent 共享。這適用於通用的公司政策、行業標準等。

2.  **在 `Agent` 層級**：
    ```python
    expert_agent = Agent(
        knowledge_base=specialized_knowledge_base,
        ...
    )
    ```
    在此配置下，只有 `expert_agent` 能夠查詢 `specialized_knowledge_base`。這適用於特定角色的專業知識，如技術文檔、法律條文等。

##### **2.3 RAG 工具的自動化**

當您為 Agent 配置了 `knowledge_base` 後，CrewAI 會**自動**為該 Agent 配備一個名為 `Knowledge Base Search` 的工具。Agent 在其推理過程中，如果意識到需要從提供的特定知識庫中尋找答案，它就會自主地調用這個工具。

---

#### **3. 知識體系（BoK）：RAG 結合反思 (RAG with Reflection)**

**定義：** 這是一個進階模式，它將 RAG 的檢索能力與我們在第一週學到的反思模式相結合。它不僅僅是檢索並使用資訊，更是對檢索到的資訊的**品質和相關性**進行批判性評估。

一個基本的 RAG 流程是：**查詢 → 檢索 → 生成**。
而一個反思性的 RAG 流程是：**查詢 → 檢索 → (反思：這些資訊足夠好嗎？) → (可選：重新查詢/精煉查詢) → 生成**。

##### **實現方式：使用 `guardrail` 進行輸出驗證**

CrewAI 的 `Task` 物件提供了一個強大的 `guardrail` 參數。`guardrail` 是一個 lambda 函數，它會在任務完成後、返回結果之前，對 Agent 的輸出進行驗證。如果驗證失敗，任務可以被配置為重新執行。

**範例場景：**

一個 Agent 的任務是根據公司的內部政策文件（已載入 `KnowledgeBase`）回答一個關於休假政策的問題。

1.  **RAG 執行**：Agent 使用 `Knowledge Base Search` 工具，從文件中檢索到相關段落，並生成一個初步答案。
2.  **Guardrail 驗證**：我們在 `Task` 中設置一個 `guardrail`，用來檢查 Agent 的輸出是否包含了關鍵字，例如「年假」或「帶薪休假」。
    ```python
    task = Task(
        description="...",
        expected_output="...",
        agent=policy_expert,
        guardrail=lambda out: "年假" in out
    )
    ```
3.  **反思與重試**：
    -   如果 Agent 的初步答案由於檢索結果不佳而未能包含關鍵字（例如，它只找到了關於病假的段落），`guardrail` 將返回 `False`。
    -   CrewAI 會指示 Agent 重新執行該任務。在第二次嘗試中，Agent 會意識到其第一次的檢索是不足的，這會促使它可能會以不同的關鍵字或方式，再次調用 `Knowledge Base Search` 工具，從而實現了對其自身檢索行為的「反思」。

---

#### **4. 實驗室指引：實驗 5**

請參閱 `lab/lab_5.md`。您將：
1.  從本地文件（例如，一個您自己創建的 `.md` 檔案）創建一個 `KnowledgeBase`。
2.  構建一個 Agent，並將此知識庫賦予它。
3.  設計一個任務，要求 Agent 回答只有在該文件中才能找到答案的問題。
4.  (挑戰) 為該任務實現一個 `guardrail`，以驗證 Agent 的答案是否基於了文件中的特定資訊，從而實現反思性的 RAG。

本實驗將讓您掌握如何將外部、私有的知識安全、高效地整合到您的 AI 系統中，這是構建企業級 AI 應用的核心能力。

講座結束。



