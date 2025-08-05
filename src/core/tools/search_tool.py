# tavily_search.py

# 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")

# 其他標準庫導入
import requests
import os
from typing import Optional, List, Dict, Any, Union, Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# CrewAI 導入 - 必須在 SQLite 修復之後
from crewai.tools import BaseTool

load_dotenv()


class TavilySearchInput(BaseModel):
    """Input schema for TavilySearchTool."""
    query: str = Field(..., description="The search query string.")
    topic: str = Field(default="general", description="Search topic: 'general' or 'news'.")
    search_depth: str = Field(default="basic", description="Search depth: 'basic' or 'advanced'.")
    max_results: Optional[int] = Field(default=5, description="Maximum number of results to return (0-20).")
    include_answer: Optional[bool] = Field(default=True, description="Whether to include LLM-generated answer.")
    include_raw_content: Optional[bool] = Field(default=False, description="Whether to include raw content.")
    include_images: bool = Field(default=False, description="Whether to search for images.")
    time_range: Optional[str] = Field(default=None, description="Time range for results (day, week, month, year).")

def tavily_search(
    api_url: str,
    api_key: str,
    query: str,
    auto_parameters: bool = False,
    topic: str = "general",
    search_depth: str = "basic",
    chunks_per_source: Optional[int] = None,
    max_results: Optional[int] = None,
    time_range: Optional[str] = None,
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_answer: Optional[Union[bool, str]] = None,
    include_raw_content: Optional[Union[bool, str]] = None,
    include_images: bool = False,
    include_image_descriptions: bool = False,
    include_favicon: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    發送 Tavily Search API 請求並回傳解析後的結果。

    Args:
        api_url (str): Tavily Search API 端點網址。
        api_key (str): API 金鑰。
        query (str): 查詢字串（必填）。
        auto_parameters (bool): 是否自動設定參數（預設為 False）。
        topic (str): 搜尋主題，'general' 或 'news'（預設 'general'）。
        search_depth (str): 搜尋深度，'basic' 或 'advanced'（預設 'basic'）。
        chunks_per_source (Optional[int]): 單一來源最多回傳幾個片段（1~3，僅 advanced 有效）。
        max_results (Optional[int]): 最多回傳幾筆結果（0~20）。
        time_range (Optional[str]): 結果時間範圍（如 'day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'）。
        days (Optional[int]): 回溯天數（僅 topic 為 news 有效）。
        start_date (Optional[str]): 查詢起始日期（YYYY-MM-DD）。
        end_date (Optional[str]): 查詢結束日期（YYYY-MM-DD）。
        include_answer (Optional[Union[bool, str]]): 是否包含 LLM 生成答案（True/'basic'/'advanced'）。
        include_raw_content (Optional[Union[bool, str]]): 是否包含原始內容（True/'markdown'/'text'）。
        include_images (bool): 是否搜尋圖片。
        include_image_descriptions (bool): 圖片是否附說明。
        include_favicon (bool): 是否回傳 favicon。
        include_domains (Optional[List[str]]): 限定搜尋的網域。
        exclude_domains (Optional[List[str]]): 排除搜尋的網域。
        country (Optional[str]): 優先顯示特定國家內容（僅 general 有效）。

    Returns:
        Dict[str, Any]: Tavily API 回傳的 JSON 結果，包含 query, answer, images, results, auto_parameters, response_time 等欄位。

    Raises:
        requests.HTTPError: 若 API 請求失敗時拋出。
    """
    payload = {
        "query": query,
        "auto_parameters": auto_parameters,
        "topic": topic,
        "search_depth": search_depth,
        "include_images": include_images,
        "include_image_descriptions": include_image_descriptions,
        "include_favicon": include_favicon,
    }
    # 可選參數動態加入
    if chunks_per_source is not None:
        payload["chunks_per_source"] = chunks_per_source
    if max_results is not None:
        payload["max_results"] = max_results
    if time_range is not None:
        payload["time_range"] = time_range
    if days is not None:
        payload["days"] = days
    if start_date is not None:
        payload["start_date"] = start_date
    if end_date is not None:
        payload["end_date"] = end_date
    if include_answer is not None:
        payload["include_answer"] = include_answer
    if include_raw_content is not None:
        payload["include_raw_content"] = include_raw_content
    if include_domains is not None:
        payload["include_domains"] = include_domains
    if exclude_domains is not None:
        payload["exclude_domains"] = exclude_domains
    if country is not None:
        payload["country"] = country

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def format_tavily_result(result: dict) -> str:
    """
    將 Tavily 搜尋結果格式化成結構化文本，包含：
      1. 摘要回答（answer）
      2. 全域相關圖片（result['images']）
      3. 各筆搜尋結果及其內嵌圖片（item['images']）
    """

    try:
        parts: List[str] = []

        # 1. 摘要回答
        answer = result.get("answer")
        if answer:
            parts.append("=== 摘要回答 ===")
            parts.append(str(answer).strip())
            parts.append("")

        # 2. 全域相關圖片
        global_images = result.get("images", [])
        if global_images and isinstance(global_images, list):
            parts.append("=== 全域相關圖片 ===")
            for i, img in enumerate(global_images, 1):
                if isinstance(img, dict):
                    parts.append(f"[圖片 {i}]")
                    parts.append(f"  標題：{img.get('title', 'N/A')}")
                    parts.append(f"  描述：{img.get('description', 'N/A')}")
                    parts.append(f"  URL：{img.get('url', 'N/A')}")
                else:
                    parts.append(f"[圖片 {i}] {str(img)}")
            parts.append("")

        # 3. 各筆搜尋結果
        parts.append("=== 搜尋結果 ===")
        results = result.get("results", [])
        if isinstance(results, list):
            for idx, item in enumerate(results, 1):
                parts.append(f"-- 來源 {idx} --")
                if isinstance(item, dict):
                    parts.append(f"標題：{item.get('title', 'N/A')}")
                    parts.append(f"網址：{item.get('url', 'N/A')}")
                    content = item.get("content")
                    if content:
                        parts.append("內容摘要：")
                        parts.append(str(content).strip())
                    raw = item.get("raw_content")
                    if raw:
                        parts.append("詳細全文：")
                        parts.append(str(raw).strip())
                else:
                    parts.append(f"結果：{str(item)}")
                parts.append("")
        else:
            parts.append(f"搜尋結果格式異常：{str(results)}")

        return "\n".join(parts)
        
    except Exception as e:
        return f"格式化結果時發生錯誤：{str(e)}\n原始結果：{str(result)}"


class TavilySearchTool(BaseTool):
    """CrewAI tool for performing web searches using Tavily Search API."""
    
    name: str = "TavilySearchTool"
    description: str = (
        "Performs web searches using Tavily Search API. "
        "Can search for general information or news, with options for basic or advanced search depth. "
        "Returns formatted results including summary answers, images, and detailed search results."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(
        self,
        query: str,
        topic: str = "general",
        search_depth: str = "basic",
        max_results: Optional[int] = 5,
        include_answer: Optional[bool] = True,
        include_raw_content: Optional[bool] = False,
        include_images: bool = False,
        time_range: Optional[str] = None,
        include_image_descriptions: bool = False,
    ) -> str:
        """
        Execute the Tavily search and return formatted results.
        
        Args:
            query: The search query string
            topic: Search topic ('general' or 'news')
            search_depth: Search depth ('basic' or 'advanced')
            max_results: Maximum number of results to return
            include_answer: Whether to include LLM-generated answer
            include_raw_content: Whether to include raw content
            include_images: Whether to search for images
            time_range: Time range for results
            
        Returns:
            Formatted search results as a string
        """
        try:
            # Get API credentials
            api_url = "https://api.tavily.com/search"
            api_key = os.getenv("TAVILY_API_KEY")
            
            if not api_key:
                return "Error: TAVILY_API_KEY not found in environment variables."
            
            # Perform the search
            print(f"🔍 開始搜尋: {query}")
            result = tavily_search(
                api_url=api_url,
                api_key=api_key,
                query=query,
                topic=topic,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images,
                include_image_descriptions=include_image_descriptions,
                time_range=time_range,
            )
            
            print(f"📄 搜尋結果類型: {type(result)}")
            if isinstance(result, dict):
                print("✅ 結果格式正確，開始格式化...")
                return format_tavily_result(result)
            else:
                print(f"❌ 結果格式錯誤: {result}")
                return f"Error: Invalid search result format: {result}"
            
        except requests.exceptions.HTTPError as http_err:
            return f"Error: HTTP error occurred: {http_err}"
        except Exception as e:
            return f"An error occurred during search: {e}"


# 範例使用（CrewAI Tool）
if __name__ == "__main__":
    # 檢查 API Key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("⚠️  請設置 TAVILY_API_KEY 環境變數才能進行搜尋測試")
        print("範例：export TAVILY_API_KEY=your_api_key")
        print("\n✅ CrewAI Tool 類別建立成功！")
        print("TavilySearchTool 已準備就緒，只需要設置 API Key 即可使用。")
    else:
        # 使用 CrewAI Tool
        search_tool = TavilySearchTool()
        
        print(f"🔑 使用 API Key: {api_key[:10]}...")
        
        # 執行搜尋
        result = search_tool._run(
            query="2025 BTC 大事件",
            search_depth="advanced",
            max_results=5,
            include_answer=True,
            include_raw_content=True,
            include_images=True,
            include_image_descriptions=True
        )
        
        print("=== CrewAI Tool 搜尋結果 ===")
        print(result)
