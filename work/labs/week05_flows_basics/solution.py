# week05_flows_basics/solution.py
import sys
import os

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from textwrap import dedent
from typing import Dict, Any

from crewai import Agent, Task, Crew
from src.core.flows import flow

# --- Agent Definition ---

logistics_agent = Agent(
    role="Logistics Coordinator",
    goal="Manage supplies for outdoor events based on clear instructions.",
    backstory="You are an experienced logistics expert who executes tasks precisely as instructed.",
    verbose=True
)

# --- Task Definitions ---

# Notice these are now functions that RETURN a Task object.
# This allows us to create them dynamically based on the script's logic.

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

# --- Main Execution Block (The "Flow Controller") ---

@flow
def run_logistics_flow(stock_level: int):
    """
    This function acts as the external script controller for the flow.
    It contains the deterministic if/else logic.
    """
    print(f"--- Running flow for stock level: {stock_level} ---")
    
    # 1. Get the initial state
    # In a real app, this would come from APIs or databases.
    state = {"weather": "sunny", "stock": stock_level}
    print(f"📊 Initial State: {state}")

    # 2. The Code-Driven Logic (The Router)
    # The decision is made here, in pure Python, before any Crew is created.
    print("⚙️ Checking conditions in the Python script...")
    is_sunny = state.get("weather") == "sunny"
    is_low_stock = state.get("stock", 100) < 50

    if is_sunny and is_low_stock:
        print("🔀 Decision: Order supplies.")
        task_to_execute = create_order_task(state)
    else:
        print("🔀 Decision: Standby.")
        task_to_execute = create_standby_task(state)

    # 3. Create and run a Crew to execute the chosen task
    # The Crew is simple and linear, only executing the single task decided by the script.
    logistics_crew = Crew(
        agents=[logistics_agent],
        tasks=[task_to_execute],
        verbose=False
    )
    
    print("🚀 Kicking off Crew to execute the decided task...")
    result = logistics_crew.kickoff()

    print(f"\n✅ Flow finished. Result: {result}")

if __name__ == "__main__":
    run_logistics_flow(stock_level=30)
    print("\n" + "="*50 + "\n")
    run_logistics_flow(stock_level=100)