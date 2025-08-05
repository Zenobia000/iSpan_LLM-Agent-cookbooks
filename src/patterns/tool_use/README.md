# Agentic Pattern: Tool Use

## 核心目標

建立穩健、可靠的工具使用機制，是打造高效能 Agent 的關鍵。本章節專注於研究 CrewAI 中工具使用的最佳實踐，特別是**錯誤處理**與**容錯機制**。

## CrewAI 工具錯誤處理機制研究

CrewAI 內建了一套基礎的錯誤處理機制，但我們可以透過一些模式來增強其穩健性。

### 1. 預設行為

- 當一個工具在執行過程中拋出異常 (Exception) 時，CrewAI 會捕捉這個異常。
- 這個異常的訊息會被回傳給 Agent，作為其思考下一步的上下文。
- Agent 會根據錯誤訊息，決定是**重試**、**更換工具**，還是**向使用者報告失敗**。

### 2. 增強錯誤處理的模式

#### a. 在工具內部進行處理 (Tool-Level Error Handling)

這是最推薦的方式。與其讓異常直接拋出給 Agent，不如在工具的 `_run` 方法內部使用 `try...except` 區塊進行處理。

**優點:**
- **更清晰的錯誤訊息:** 你可以回傳一個對 Agent 更友善、更具指導性的錯誤訊息，而不是一個原始的 Python traceback。
- **備援邏輯 (Fallback):** 在 `except` 區塊中，你可以實作備援方案。例如，如果主要的 API 失敗了，可以嘗試呼叫一個備用的 API。
- **狀態碼處理:** 對於 API 工具，可以根據不同的 HTTP 狀態碼 (401, 404, 429, 500) 回傳不同的、具體的錯誤原因。

**範例 (參考 `src/core/tools/weather_tool.py`):**

```python
class OpenWeatherMapTool(BaseTool):
    def _run(self, city_name: str) -> str:
        try:
            # ... API call logic ...
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            # ... process data ...
            return result
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                return "❌ Error: Invalid API key."
            elif response.status_code == 404:
                return f"❌ Error: City '{city_name}' not found."
            return f"❌ Error: HTTP error occurred: {http_err}"
        except Exception as e:
            return f"❌ Error: An unexpected error occurred: {e}"
```

#### b. 使用 Pydantic 進行輸入驗證 (Input Validation)

在工具的 `args_schema` 中使用 Pydantic 模型，可以在工具執行**之前**就捕捉到無效的輸入，避免了因為格式錯誤而導致的執行失敗。

**優點:**
- **早期失敗 (Fail Fast):** 在問題發生的最早階段就提出錯誤。
- **清晰的指引:** Pydantic 會生成非常清晰的錯誤訊息，告訴 Agent 哪個參數錯了，以及為什麼錯。

**範例 (參考 `src/core/tools/coordinate_weather_tool.py`):**

```python
class CoordinateWeatherInput(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class CoordinateWeatherTool(BaseTool):
    name: str = "CoordinateWeatherTool"
    args_schema: Type[BaseModel] = CoordinateWeatherInput
    # ...
```

### 3. CrewAI 的重試機制

CrewAI 本身沒有一個內建的、像 `max_retries=3` 這樣的參數來自動重試失敗的工具。重試的邏輯是**由 Agent 的 LLM 來驅動的**。

- 如果工具回傳了一個可操作的錯誤訊息 (例如 "API timeout, please try again"), Agent 的 LLM 就有可能決定再次呼叫同一個工具。
- 為了促進這種行為，我們應該在工具的錯誤訊息中**明確地給出重試建議**。

## 結論與最佳實踐

1.  **優先在工具內部處理錯誤:** 使用 `try...except` 捕捉預期內的異常，並回傳對 Agent 友善的訊息。
2.  **使用 Pydantic 嚴格驗證輸入:** 確保傳給工具的參數在格式和類型上都是正確的。
3.  **提供清晰的錯誤指引:** 錯誤訊息應該要能幫助 Agent 做出下一步的決策（例如，是修正參數、更換工具還是放棄）。
4.  **考慮備援方案:** 在工具的錯誤處理邏輯中，可以加入備援數據源或備用 API，以提高工具的可靠性。
