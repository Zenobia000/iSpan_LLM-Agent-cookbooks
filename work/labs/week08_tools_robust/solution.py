import sys
import os
import time
import random
from textwrap import dedent
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool

# --- Step 1: Define the RobustToolWrapper ---
class RobustToolWrapper(BaseTool):
    """
    A wrapper for CrewAI tools that makes them robust by adding retry and fallback mechanisms.
    It correctly inherits metadata and handles crewai's complex argument passing.
    """
    tool: BaseTool
    max_retries: int = 3
    fallback_func: Optional[Callable[..., Any]] = None

    def __init__(self, tool: BaseTool, **kwargs: Any):
        # We initialize the BaseTool with all the necessary fields.
        # This ensures Pydantic validation passes and the wrapper has all its data.
        super().__init__(
            name=tool.name, 
            description=tool.description, 
            args_schema=tool.args_schema,
            tool=tool,
            **kwargs
        )

    def _run(self, **kwargs: Any) -> Any:
        """
        This is the core logic. It tries to execute the tool, retries on failure,
        and uses a fallback if all retries fail.
        It also intelligently handles crewai's nested argument passing.
        """
        # The agent might pass arguments directly or nested inside 'tool_input'.
        actual_args = kwargs.get('tool_input', kwargs)
        
        for attempt in range(self.max_retries):
            try:
                print(f"\nAttempt {attempt + 1}/{self.max_retries} for tool '{self.name}'...")
                return self.tool._run(**actual_args)
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("All retries failed.")
                    if self.fallback_func:
                        print("Executing fallback function...")
                        return self.fallback_func(**actual_args)
                    else:
                        raise e

# --- Step 2: Create a mock unstable tool ---
class UnstableSearchToolSchema(BaseModel):
    query: str = Field(description="The search query.")

class UnstableSearchTool(BaseTool):
    name: str = "Unstable Search"
    description: str = "A search tool that has a 70% chance of failing, used to test robustness."
    args_schema: type[BaseModel] = UnstableSearchToolSchema

    def _run(self, query: str) -> str:
        if random.random() < 0.7:
            raise ConnectionError("API connection failed. Try again now.")
        return f"Search results for '{query}': Successfully retrieved data."

# --- Step 3: Define a fallback function ---
def fallback_search(query: str) -> str:
    return f"Fallback search results for '{query}': Data retrieved from local cache."

# --- Step 4: Setup and run the Crew ---
def main():
    """Sets up and runs a Crew to demonstrate the RobustToolWrapper."""
    unstable_tool = UnstableSearchTool()
    
    # Wrap the tool with our robust wrapper
    robust_search_tool = RobustToolWrapper(
        tool=unstable_tool,
        max_retries=5,
        fallback_func=fallback_search
    )

    researcher = Agent(
        role="Senior Research Analyst",
        goal="Uncover cutting-edge developments in AI.",
        backstory=dedent(
            """You are a renowned research analyst, known for your ability to find
            critical information even when data sources are unreliable."""
        ),
        tools=[robust_search_tool],
        verbose=True
    )

    task = Task(
        description="Search for the latest trends in multi-agent AI systems.",
        expected_output="A summary of the latest trends, based on the search results.",
        agent=researcher
    )

    crew = Crew(agents=[researcher], tasks=[task], verbose=True)
    result = crew.kickoff()

    print("\n\n########################")
    print("## Robust Tool Execution Result:")
    print("########################\n")
    print(result)

if __name__ == "__main__":
    main()
