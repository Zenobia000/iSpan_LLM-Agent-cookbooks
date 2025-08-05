# CrewAI Custom Tools

本目錄包含為 CrewAI 框架開發的自定義工具。

## 可用工具

### 1. TavilySearchTool
**檔案**: `search_tool.py`
**功能**: 使用 Tavily Search API 進行網頁搜尋

#### 功能特色
- 支援一般搜尋和新聞搜尋
- 可選擇基礎或進階搜尋深度
- 包含 LLM 生成的摘要答案
- 支援圖片搜尋
- 可設定時間範圍
- 格式化輸出結果

#### 輸入參數
- `query` (必填): 搜尋查詢字串
- `topic`: 搜尋主題 ('general' 或 'news')
- `search_depth`: 搜尋深度 ('basic' 或 'advanced')
- `max_results`: 最大結果數量 (0-20)
- `include_answer`: 是否包含 LLM 生成答案
- `include_raw_content`: 是否包含原始內容
- `include_images`: 是否搜尋圖片
- `time_range`: 時間範圍限制

#### 環境變數需求
```bash
TAVILY_API_KEY=your_tavily_api_key
```

#### 使用範例
```python
from core.tools import TavilySearchTool

search_tool = TavilySearchTool()
result = search_tool._run(
    query="AI技術趨勢 2025",
    search_depth="advanced",
    max_results=5,
    include_answer=True
)
```

### 2. OpenWeatherMapTool ⭐ (已優化)
**檔案**: `weather_tool.py`
**功能**: 獲取指定城市的即時天氣資訊

#### 🔧 優化改進
- **解決 Agent 重試問題**: 使用嚴格的輸入驗證避免參數混淆
- **單一職責**: 只處理城市名稱查詢，坐標查詢使用專門工具
- **智能輸入清理**: 自動移除國家後綴，標準化城市名稱
- **詳細錯誤信息**: 提供明確的使用指引

#### 功能特色
- 專門處理城市名稱查詢
- Pydantic 嚴格驗證防止格式錯誤
- 完整天氣資訊（溫度、濕度、氣壓、風速、風向）
- 智能錯誤處理和用戶友好的錯誤消息

#### 輸入參數
- `city_name` (必填): 簡單的城市名稱（例如："Tokyo"、"London"）

#### ⚠️ 重要注意事項
```python
# ✅ 正確用法
city_name: "Tokyo"
city_name: "New York" 
city_name: "London"

# ❌ 錯誤用法（會被自動修正或拒絕）
city_name: "Tokyo, Japan"  # 會自動移除 ", Japan"
city_name: "35.6762,139.6503"  # 會被拒絕，請使用 CoordinateWeatherTool
```

#### 環境變數需求
```bash
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
```

#### 使用範例
```python
from core.tools import OpenWeatherMapTool

weather_tool = OpenWeatherMapTool()
result = weather_tool._run(city_name="Tokyo")
```

### 3. CoordinateWeatherTool (新增)
**檔案**: `coordinate_weather_tool.py`
**功能**: 使用精確坐標獲取天氣資訊

#### 功能特色
- 專門處理經緯度坐標查詢
- 嚴格的坐標範圍驗證
- 與城市工具完全分離，避免參數混淆

#### 輸入參數
- `latitude` (必填): 緯度 (-90.0 到 90.0)
- `longitude` (必填): 經度 (-180.0 到 180.0)

#### 使用範例
```python
from core.tools import CoordinateWeatherTool

coord_tool = CoordinateWeatherTool()
result = coord_tool._run(latitude=35.6762, longitude=139.6503)  # 東京
```

## 工具開發指南

### 基於 BaseTool 的工具開發

1. **定義輸入 Schema**
```python
class MyToolInput(BaseModel):
    """Input schema for MyTool."""
    param: str = Field(..., description="Parameter description")
```

2. **繼承 BaseTool**
```python
class MyTool(BaseTool):
    name: str = "MyTool"
    description: str = "Tool description"
    args_schema: Type[BaseModel] = MyToolInput
    
    def _run(self, param: str) -> str:
        # Tool logic here
        return "Result"
```

### 使用 @tool 裝飾器的工具開發

```python
from crewai.tools import tool

@tool("Tool Name")
def my_tool(param: str) -> str:
    """Tool description."""
    # Tool logic here
    return "Result"
```

## 參考資源

- [CrewAI 官方工具文檔](https://docs.crewai.com/en/learn/create-custom-tools)
- [Tavily Search API 文檔](https://docs.tavily.com/)
- [OpenWeatherMap API 文檔](https://openweathermap.org/api)