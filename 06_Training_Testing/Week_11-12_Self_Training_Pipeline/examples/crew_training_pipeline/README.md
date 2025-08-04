# 範例：Crew 訓練流程

本範例旨在簡化並展示 **CrewAI 的訓練功能**，讓您了解如何透過一個小型的數據集來微調您的 Agent。

## 1. 目的

本範例的目標是：
1.  展示如何創建一個符合 `crewai train` 要求的 `jsonl` 格式的訓練數據集。
2.  演示如何使用程式化的 `crew.train()` 方法來啟動訓練流程。
3.  讓您能夠觀察到，即使是小規模的訓練，也能對 Agent 的輸出風格和內容產生可見的影響。

## 2. 如何運行

1.  **安裝必要的函式庫：**
    ```bash
    # crewai 包含了訓練所需的所有依賴
    pip install crewai
    ```

2.  **創建訓練數據文件：**
    -   在 `crew_training_pipeline` 目錄下，創建一個名為 `training_data.jsonl` 的檔案。
    -   將以下內容複製到該檔案中。注意，每一行都是一個獨立的 JSON 物件。
        ```json
        {"input": "Give me a fun fact about the Roman Empire.", "output": "A fun fact about the Roman Empire is that they had a form of central heating called a hypocaust system, where hot air circulated under floors and through walls to warm rooms and baths!"}
        {"input": "What's a cool fact about space?", "output": "A cool fact about space is that there's a giant cloud of alcohol in Sagittarius B2, which is near the center of our galaxy. It contains enough ethyl alcohol to supply 400 trillion trillion pints of beer!"}
        ```

3.  **執行腳本：**
    ```bash
    python main.py
    ```

## 3. 程式碼邏輯詳解

-   **`main.py`**:
    1.  **Agent 定義**：
        -   我們創建一個 `FunFactFinder` 代理，其目標是提供有趣的事實。
    2.  **訓練前的測試**：
        -   我們首先定義一個任務，並在**訓練前**運行一次 `crew.kickoff()`。
        -   我們將其結果打印出來。這是我們的「基準線 (baseline)」，用來對比訓練後的效果。
    3.  **啟動訓練**：
        -   我們調用 `crew.train()` 方法。
        -   `dataset_path` 參數指向我們創建的 `training_data.jsonl` 文件。
        -   CrewAI 會處理後續的微調流程（這可能需要一些時間，並會消耗 API token）。
    4.  **訓練後的測試**：
        -   訓練完成後，我們用**完全相同**的任務再次運行 `crew.kickoff()`。
        -   我們將新的結果打印出來。
    5.  **比較結果**：
        -   透過比較訓練前和訓練後的輸出，您應該能觀察到 Agent 的回答風格變得更接近我們在 `training_data.jsonl` 中提供的範例格式（例如，以 "A fun fact about..." 或 "A cool fact about..." 開頭）。

## 4. 預期輸出

腳本的輸出將分為三個主要部分：
1.  一個標示為「Before Training」的區塊，顯示 Agent 未經訓練時的原始回答。
2.  CrewAI 訓練流程的日誌，顯示其正在微調模型。
3.  一個標示為「After Training」的區塊，顯示 Agent 在經過微調後的回答。

比較這兩個回答，以評估訓練對 Agent 行為的影響。



