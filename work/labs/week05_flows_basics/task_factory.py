# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week05_flows_basics_refactored\task_factory.py
from typing import Dict, Any
from crewai import Task
from agent_definition import logistics_agent

def create_order_task(state: Dict[str, Any]) -> Task:
    """Creates a task for ordering supplies."""
    return Task(
        description=f"Weather is sunny, but stock is low at {state['stock']}. Order new supplies for the outdoor event immediately.",
        agent=logistics_agent,
        expected_output="A confirmation that the order has been placed."
    )

def create_standby_task(state: Dict[str, Any]) -> Task:
    """Creates a task for standing by."""
    reason = "weather is not suitable" if state.get("weather") != "sunny" else f"stock is sufficient ({state['stock']})"
    return Task(
        description=f"No action is needed because {reason}. Confirm this standby status.",
        agent=logistics_agent,
        expected_output="A confirmation that no action is required."
    )

