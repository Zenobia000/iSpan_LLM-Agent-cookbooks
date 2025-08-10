# Week 12: 測試與品質保證 - 單元測試框架

## 🎯 學習目標

1.  **理解 Agent/Crew 測試的核心理念**：學習如何為基於 LLM 的應用編寫有意義的測試，重點在於測試其**結構的確定性**，而非**輸出的不確定性**。
2.  **實作單元測試**：使用 Python 內建的 `unittest` 框架，為 Agent 的定義和核心邏輯類別編寫單元測試。
3.  **學習 Mocking**：了解如何使用 `unittest.mock.patch` 來「模擬」檔案寫入等外部依賴，確保測試的獨立和穩定。

## 🧪 測試框架說明

本實驗室為 `week11_training_pipeline` 中的核心組件建立了一套單元測試。測試的重點是驗證我們自己編寫的程式碼的**結構和邏輯**是否正確。

### 測試對象

-   `agent_definitions.py`: 驗證 `ContentCreatorAgent` 和 `CritiqueAgent` 的 `role`、`goal` 等配置是否正確。
-   `training_data_collector.py`: 驗證 `TrainingDataCollector` 類別的初始化、數據收集和檔案儲存邏輯是否符合預期。

### 測試檔案

-   `test_training_pipeline.py`: 包含所有單元測試案例。

### 核心測試案例

1.  **`TestWeek11AgentDefinitions`**: 
    -   `test_content_creator_agent_creation`: 確保「內容創作者 Agent」的配置正確。
    -   `test_critique_agent_creation`: 確保「評論家 Agent」的配置正確。

2.  **`TestTrainingDataCollector`**:
    -   `test_initialization`: 驗證資料收集器初始化是否正確。
    -   `test_collect`: 驗證 `collect` 方法是否能正確地將數據點加入內部列表。
    -   `test_save`: 使用 `mock_open` 驗證 `save` 方法是否以正確的格式呼叫了檔案寫入功能，而無需在測試過程中實際產生檔案。

### 關鍵技術：模擬 (Mocking)

為了避免在測試 `TrainingDataCollector` 時實際寫入檔案（這會讓單元測試依賴於檔案系統），我們使用了 `unittest.mock.patch` 來模擬 `open` 函式。

```python
# In TestTrainingDataCollector.test_save

m = mock_open()
with patch("builtins.open", m):
    self.collector.save()

m.assert_called_once_with("test_output.jsonl", 'w', encoding='utf-8')
handle = m()
handle.write.assert_has_calls(...)
```

這段程式碼攔截了 `self.collector.save()` 中對 `open()` 的呼叫，並用一個「假的」模擬檔案取代了它。這讓我們可以檢查 `save` 方法是否試圖用正確的檔名和模式去「打開」檔案，以及是否試圖將正確的內容「寫入」檔案，整個過程都在記憶體中完成，非常快速且可靠。

## ⚙️ 如何執行測試

在終端機中，導航到 `work/labs/week12_testing_qa` 目錄，然後執行以下命令：

```bash
python test_training_pipeline.py
```

如果所有測試都通過，你將會看到類似以下的輸出：

```
....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```
