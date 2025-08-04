"""
CrewAI 網路搜索工具

提供整合多個搜索引擎的網路搜索功能
支援 Google、Bing、DuckDuckGo 等搜索引擎
"""

from typing import List, Dict, Any, Optional, Union
import asyncio
import aiohttp
import requests
from dataclasses import dataclass
from enum import Enum
import json
import time
from urllib.parse import quote_plus, urljoin
import re
from bs4 import BeautifulSoup

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .tool_registry import ToolRegistry, ToolCategory, ToolMetadata, register_tool


class SearchEngine(Enum):
    """搜索引擎類型"""
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"
    TAVILY = "tavily"


@dataclass
class SearchResult:
    """搜索結果項目"""
    title: str
    url: str
    snippet: str
    source: str = ""
    rank: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SearchResponse(BaseModel):
    """搜索回應模型"""
    query: str = Field(..., description="搜索查詢")
    results: List[SearchResult] = Field(default_factory=list, description="搜索結果")
    total_results: int = Field(default=0, description="總結果數")
    search_time: float = Field(default=0.0, description="搜索時間(秒)")
    engine_used: str = Field(default="", description="使用的搜索引擎")
    error: Optional[str] = Field(default=None, description="錯誤訊息")


class SearchEngineAPI:
    """搜索引擎 API 基類"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = None
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """執行搜索"""
        raise NotImplementedError
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


class SerperAPI(SearchEngineAPI):
    """Serper.dev API 實作"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://google.serper.dev/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """使用 Serper API 搜索"""
        if not self.api_key:
            raise ValueError("Serper API key is required")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": min(num_results, 100)
        }
        
        try:
            async with self.session.post(
                self.base_url, 
                headers=headers, 
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_serper_results(data)
                else:
                    raise Exception(f"Serper API error: {response.status}")
        
        except Exception as e:
            raise Exception(f"Serper search failed: {str(e)}")
    
    def _parse_serper_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """解析 Serper API 回應"""
        results = []
        
        for i, item in enumerate(data.get("organic", [])):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="serper",
                rank=i + 1,
                metadata={
                    "position": item.get("position"),
                    "date": item.get("date")
                }
            )
            results.append(result)
        
        return results


class TavilyAPI(SearchEngineAPI):
    """Tavily API 實作"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.tavily.com/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """使用 Tavily API 搜索"""
        if not self.api_key:
            raise ValueError("Tavily API key is required")
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": min(num_results, 20)
        }
        
        try:
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_tavily_results(data)
                else:
                    raise Exception(f"Tavily API error: {response.status}")
        
        except Exception as e:
            raise Exception(f"Tavily search failed: {str(e)}")
    
    def _parse_tavily_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """解析 Tavily API 回應"""
        results = []
        
        for i, item in enumerate(data.get("results", [])):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source="tavily",
                rank=i + 1,
                metadata={
                    "score": item.get("score"),
                    "published_date": item.get("published_date")
                }
            )
            results.append(result)
        
        return results


class DuckDuckGoAPI(SearchEngineAPI):
    """DuckDuckGo 搜索 (免費，無需 API key)"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://duckduckgo.com"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """使用 DuckDuckGo 搜索"""
        try:
            # 第一步：獲取 vqd token
            vqd = await self._get_vqd_token(query)
            
            # 第二步：執行搜索
            search_url = f"{self.base_url}/l/"
            params = {
                "kl": "wt-wt",
                "s": "0",
                "df": "",
                "vqd": vqd,
                "q": query,
                "bing_market": "wt-WT"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_duckduckgo_results(html)
                else:
                    raise Exception(f"DuckDuckGo search error: {response.status}")
        
        except Exception as e:
            raise Exception(f"DuckDuckGo search failed: {str(e)}")
    
    async def _get_vqd_token(self, query: str) -> str:
        """獲取 DuckDuckGo VQD token"""
        url = f"{self.base_url}/"
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with self.session.get(url, params=params, headers=headers) as response:
            html = await response.text()
            
            # 從 HTML 中提取 vqd token
            vqd_match = re.search(r'vqd=(\d+-\d+-\d+)', html)
            if vqd_match:
                return vqd_match.group(1)
            else:
                raise Exception("Failed to get VQD token from DuckDuckGo")
    
    def _parse_duckduckgo_results(self, html: str) -> List[SearchResult]:
        """解析 DuckDuckGo HTML 結果"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # DuckDuckGo 結果解析邏輯 (簡化版)
        result_containers = soup.find_all('div', class_='result')
        
        for i, container in enumerate(result_containers[:10]):
            title_elem = container.find('a', class_='result__a')
            snippet_elem = container.find('a', class_='result__snippet')
            
            if title_elem:
                result = SearchResult(
                    title=title_elem.text.strip(),
                    url=title_elem.get('href', ''),
                    snippet=snippet_elem.text.strip() if snippet_elem else '',
                    source="duckduckgo",
                    rank=i + 1
                )
                results.append(result)
        
        return results


@register_tool(
    category=ToolCategory.DATA_RETRIEVAL,
    aliases=["search", "google", "web_search"],
    description="多引擎網路搜索工具",
    author="CrewAI Team"
)
class WebSearchTool(BaseTool):
    """
    多引擎網路搜索工具
    
    支援多個搜索引擎：
    - Serper (Google Search API)
    - Tavily (AI-powered search)
    - DuckDuckGo (免費搜索)
    """
    
    name: str = "web_search"
    description: str = "在網際網路上搜索資訊，支援多個搜索引擎"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 初始化搜索引擎
        self.search_engines = {}
        
        # 載入 API keys
        self._load_api_keys()
        
        # 設定預設搜索引擎
        self.default_engine = SearchEngine.DUCKDUCKGO
        
        # 搜索配置
        self.max_results_per_engine = 10
        self.timeout_seconds = 30
        self.retry_attempts = 3
    
    def _load_api_keys(self):
        """載入 API keys"""
        import os
        
        # Serper API
        serper_key = os.getenv("SERPER_API_KEY")
        if serper_key:
            self.search_engines[SearchEngine.SERPER] = SerperAPI(serper_key)
            self.default_engine = SearchEngine.SERPER
        
        # Tavily API
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            self.search_engines[SearchEngine.TAVILY] = TavilyAPI(tavily_key)
            if self.default_engine == SearchEngine.DUCKDUCKGO:
                self.default_engine = SearchEngine.TAVILY
        
        # DuckDuckGo (免費，總是可用)
        self.search_engines[SearchEngine.DUCKDUCKGO] = DuckDuckGoAPI()
    
    def _run(self, query: str, engine: Optional[str] = None, 
            num_results: int = 10) -> str:
        """同步執行搜索"""
        return asyncio.run(self._run_async(query, engine, num_results))
    
    async def _run_async(self, query: str, engine: Optional[str] = None, 
                        num_results: int = 10) -> str:
        """異步執行搜索"""
        start_time = time.time()
        
        # 選擇搜索引擎
        selected_engine = self._select_engine(engine)
        
        try:
            # 執行搜索
            async with self.search_engines[selected_engine] as search_api:
                results = await self._search_with_retry(
                    search_api, query, num_results
                )
            
            search_time = time.time() - start_time
            
            # 構建回應
            response = SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                engine_used=selected_engine.value
            )
            
            return self._format_results(response)
            
        except Exception as e:
            # 錯誤處理：嘗試備用搜索引擎
            return await self._handle_search_failure(query, num_results, str(e))
    
    def _select_engine(self, engine: Optional[str]) -> SearchEngine:
        """選擇搜索引擎"""
        if engine:
            try:
                requested_engine = SearchEngine(engine.lower())
                if requested_engine in self.search_engines:
                    return requested_engine
            except ValueError:
                pass
        
        return self.default_engine
    
    async def _search_with_retry(self, search_api: SearchEngineAPI, 
                                query: str, num_results: int) -> List[SearchResult]:
        """帶重試機制的搜索"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                results = await asyncio.wait_for(
                    search_api.search(query, num_results),
                    timeout=self.timeout_seconds
                )
                return results
                
            except asyncio.TimeoutError:
                last_error = f"搜索超時 (第 {attempt + 1} 次嘗試)"
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # 指數退避
                    
            except Exception as e:
                last_error = str(e)
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
        
        raise Exception(f"搜索失敗，已重試 {self.retry_attempts} 次: {last_error}")
    
    async def _handle_search_failure(self, query: str, num_results: int, 
                                   error: str) -> str:
        """處理搜索失敗，嘗試備用引擎"""
        # 嘗試其他可用的搜索引擎
        for engine in self.search_engines:
            if engine != self.default_engine:
                try:
                    async with self.search_engines[engine] as search_api:
                        results = await search_api.search(query, num_results)
                    
                    response = SearchResponse(
                        query=query,
                        results=results,
                        total_results=len(results),
                        engine_used=engine.value,
                        error=f"主要搜索引擎失敗，使用備用引擎: {error}"
                    )
                    
                    return self._format_results(response)
                    
                except Exception:
                    continue
        
        # 所有搜索引擎都失敗
        error_response = SearchResponse(
            query=query,
            results=[],
            total_results=0,
            error=f"所有搜索引擎都無法使用: {error}"
        )
        
        return self._format_results(error_response)
    
    def _format_results(self, response: SearchResponse) -> str:
        """格式化搜索結果"""
        if response.error:
            return f"搜索錯誤: {response.error}"
        
        if not response.results:
            return f"沒有找到關於 '{response.query}' 的搜索結果"
        
        # 格式化結果
        formatted_results = []
        formatted_results.append(f"搜索查詢: {response.query}")
        formatted_results.append(f"搜索引擎: {response.engine_used}")
        formatted_results.append(f"找到 {response.total_results} 個結果 (耗時 {response.search_time:.2f}秒)")
        formatted_results.append("-" * 80)
        
        for i, result in enumerate(response.results[:10], 1):
            formatted_results.append(f"\n{i}. {result.title}")
            formatted_results.append(f"   網址: {result.url}")
            formatted_results.append(f"   摘要: {result.snippet}")
            
            if result.metadata:
                metadata_info = []
                for key, value in result.metadata.items():
                    if value:
                        metadata_info.append(f"{key}: {value}")
                if metadata_info:
                    formatted_results.append(f"   資訊: {', '.join(metadata_info)}")
        
        return "\n".join(formatted_results)
    
    def search_multiple_engines(self, query: str, engines: List[str] = None, 
                               num_results: int = 5) -> Dict[str, List[SearchResult]]:
        """使用多個搜索引擎搜索並比較結果"""
        return asyncio.run(self._search_multiple_engines_async(query, engines, num_results))
    
    async def _search_multiple_engines_async(self, query: str, engines: List[str] = None, 
                                           num_results: int = 5) -> Dict[str, List[SearchResult]]:
        """異步多引擎搜索"""
        if engines is None:
            engines = [engine.value for engine in self.search_engines.keys()]
        
        results = {}
        tasks = []
        
        for engine_name in engines:
            try:
                engine = SearchEngine(engine_name)
                if engine in self.search_engines:
                    task = self._single_engine_search(engine, query, num_results)
                    tasks.append((engine_name, task))
            except ValueError:
                continue
        
        # 並行執行所有搜索
        completed_searches = await asyncio.gather(
            *[task for _, task in tasks], 
            return_exceptions=True
        )
        
        # 整理結果
        for (engine_name, _), result in zip(tasks, completed_searches):
            if isinstance(result, Exception):
                results[engine_name] = []
            else:
                results[engine_name] = result
        
        return results
    
    async def _single_engine_search(self, engine: SearchEngine, query: str, 
                                   num_results: int) -> List[SearchResult]:
        """單個引擎搜索"""
        async with self.search_engines[engine] as search_api:
            return await search_api.search(query, num_results)


# 使用範例
if __name__ == "__main__":
    import os
    
    # 設置 API keys (如果有的話)
    # os.environ["SERPER_API_KEY"] = "your_serper_api_key"
    # os.environ["TAVILY_API_KEY"] = "your_tavily_api_key"
    
    # 創建搜索工具
    search_tool = WebSearchTool()
    
    # 執行搜索
    result = search_tool._run("CrewAI 多代理系統教學")
    print(result)
    
    # 多引擎搜索比較
    multi_results = search_tool.search_multiple_engines(
        "人工智慧最新發展", 
        engines=["duckduckgo"],
        num_results=3
    )
    
    for engine, results in multi_results.items():
        print(f"\n=== {engine.upper()} 搜索結果 ===")
        for result in results:
            print(f"標題: {result.title}")
            print(f"網址: {result.url}")
            print(f"摘要: {result.snippet[:100]}...")
            print("-" * 50) 