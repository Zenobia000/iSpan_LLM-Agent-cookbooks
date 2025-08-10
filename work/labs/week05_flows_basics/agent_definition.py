# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week05_flows_basics_refactored\agent_definition.py
from crewai import Agent

logistics_agent = Agent(
    role="Logistics Coordinator",
    goal="Manage supplies for outdoor events based on clear instructions.",
    backstory="You are an experienced logistics expert who executes tasks precisely as instructed.",
    verbose=True
)
