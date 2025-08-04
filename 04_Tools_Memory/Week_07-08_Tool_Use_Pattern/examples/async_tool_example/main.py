import os
import asyncio
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# --- Tool Definition ---
# Use the @tool decorator to easily create a tool from a function.
# This tool is defined as an async function to simulate a non-blocking operation.
@tool("Web Search")
async def search_web_async(query: str) -> str:
    """
    Asynchronously searches the web for a given query.
    Simulates a network request with a delay.
    """
    print(f"\nTool: Starting async web search for '{query}'...")
    # Simulate a network delay of 2 seconds
    await asyncio.sleep(2)
    print("Tool: ...Async search finished.")
    # In a real tool, you would perform the actual web search here.
    return f"Simulated search results for '{query}': AI is transforming industries."

# --- Agent Definition ---
# Set your API Key
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

researcher = Agent(
    role="Senior Researcher",
    goal="Find the most relevant and up-to-date information on any topic.",
    backstory="You are an expert researcher, skilled in using advanced search techniques to find valuable information.",
    verbose=True,
    tools=[search_web_async] # Assign the async tool to the agent
)

# --- Task Definition ---
research_task = Task(
    description="What is the impact of AI on modern industries?",
    expected_output="A concise summary of the impact of AI.",
    agent=researcher
)

# --- Crew Definition ---
research_crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    process=Process.sequential,
    verbose=2
)

# --- Execution ---
if __name__ == "__main__":
    print("## Welcome to the Async Web Search Crew")
    print("--------------------------------------")
    
    # Running the crew
    # CrewAI handles the async tool execution automatically.
    result = research_crew.kickoff()

    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################\n")
    print(result)



