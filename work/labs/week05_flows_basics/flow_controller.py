# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week05_flows_basics_refactored\flow_controller.py
from crewai import Crew
from task_factory import create_order_task, create_standby_task
from agent_definition import logistics_agent
from src.core.flows import flow

@flow
def run_logistics_flow(stock_level: int):
    """
    This function acts as the external script controller for the flow.
    It contains the deterministic if/else logic.
    """
    print(f"--- Running flow for stock level: {stock_level} ---")
    
    # 1. Get the initial state
    state = {"weather": "sunny", "stock": stock_level}
    print(f"Initial State: {state}")

    # 2. The Code-Driven Logic (The Router)
    print("Checking conditions in the Python script...")
    is_sunny = state.get("weather") == "sunny"
    is_low_stock = state.get("stock", 100) < 50

    if is_sunny and is_low_stock:
        print("Decision: Order supplies.")
        task_to_execute = create_order_task(state)
    else:
        print("Decision: Standby.")
        task_to_execute = create_standby_task(state)

    # 3. Create and run a Crew to execute the chosen task
    logistics_crew = Crew(
        agents=[logistics_agent],
        tasks=[task_to_execute],
        verbose=False
    )
    
    print("Kicking off Crew to execute the decided task...")
    result = logistics_crew.kickoff()

    print(f"\nFlow finished. Result: {result}")
