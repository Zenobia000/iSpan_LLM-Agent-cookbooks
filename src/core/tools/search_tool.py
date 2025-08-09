# tavily_search.py

# 修復 SQLite 版本兼容性
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    pass

import os
import requests
from typing import Optional, List, Dict, Any, Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

load_dotenv()


class TavilySearchInput(BaseModel):
    """Input schema for the enhanced TavilySearchTool."""
    query: str = Field(..., description="The search query string.")
    max_results: int = Field(default=5, description="Maximum number of search results to return.")
    include_raw_content: bool = Field(default=False, description="Whether to include the full raw content of the search results.")
    search_depth: str = Field(default="basic", description="Search depth: 'basic' or 'advanced'.")


def tavily_search(api_key: str, query: str, **kwargs) -> Dict[str, Any]:
    """Sends a request to the Tavily Search API."""
    payload = {"api_key": api_key, "query": query, **kwargs}
    response = requests.post("https://api.tavily.com/search", json=payload)
    response.raise_for_status()
    return response.json()

def format_tavily_results(results: List[Dict[str, Any]]) -> str:
    """
    Formats Tavily search results into a structured string, including raw content if available.
    """
    if not results:
        return "No search results found."

    string_parts = []
    for i, result in enumerate(results, 1):
        string_parts.append(
            f"- Result {i}:\n" \
            f"  - Title: {result.get('title', 'N/A')}\n" \
            f"  - URL: {result.get('url', 'N/A')}\n" \
            f"  - Summary: {result.get('content', 'N/A')}"
        )
        if 'raw_content' in result and result['raw_content']:
            string_parts.append(f"  - Full Content: {result['raw_content'][:1000]}...")
    return "\n".join(string_parts)


class TavilySearchTool(BaseTool):
    """
    A powerful tool that uses the Tavily Search API to find information and optionally
    retrieve the full content of the search results in a single call.
    """
    
    name: str = "TavilySearchTool"
    description: str = (
        "Performs a web search for a given query. Can optionally include the full raw content of the websites found."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
        search_depth: str = "basic",
    ) -> str:
        """
        Executes the Tavily search.
        """
        try:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return "Error: TAVILY_API_KEY environment variable is not set."

            print(f"🔍 Searching for: '{query}' (Raw Content: {include_raw_content})...")
            search_results = tavily_search(
                api_key=api_key,
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                search_depth=search_depth,
            )
            
            return format_tavily_results(search_results.get('results', []))

        except Exception as e:
            return f"An error occurred during the search: {e}"


# Example usage
if __name__ == "__main__":
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️ TAVILY_API_KEY not set. Cannot run example.")
    else:
        tool = TavilySearchTool()
        # Example 1: Basic search without raw content
        basic_results = tool.run(query="Latest news on CrewAI framework", include_raw_content=False)
        print("=== Basic Search Results ===")
        print(basic_results)
        
        print("\n" + "="*50 + "\n")

        # Example 2: Search with raw content
        detailed_results = tool.run(query="What is the main idea of the paper 'Self-Refine'?", include_raw_content=True)
        print("=== Detailed Search Results (with Raw Content) ===")
        print(detailed_results)
