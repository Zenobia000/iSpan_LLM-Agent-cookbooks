# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week06_flows_advanced_refactored\flow_controller.py
import json
from decision_crew_factory import create_decision_crew
from execution_crew_factory import create_execution_crew

def run_dynamic_flow(request: str, is_premium: bool):
    """
    Orchestrates the two-stage decision and execution flow.
    """
    print(f"--- Running dynamic flow for request: '{request}' ---")

    # --- Step 1: Run Decision Crew ---
    print("\n--- 1. Running Decision Crew ---")
    decision_crew = create_decision_crew(request, is_premium)
    decision_result_output = decision_crew.kickoff()
    decision_result_str = str(decision_result_output)
    print(f"Decision Crew Result: {decision_result_str}")

    # --- Step 2: Parse Decision and Run Execution Crew ---
    try:
        json_start = decision_result_str.find('{')
        json_end = decision_result_str.rfind('}')
        if json_start != -1 and json_end != -1:
            cleaned_json_str = decision_result_str[json_start:json_end+1]
            decision = json.loads(cleaned_json_str)
        else:
            raise json.JSONDecodeError("No JSON object found in the output.", decision_result_str, 0)

        specialist_role = decision["specialist_role"]
        new_task_description = decision["new_task_description"]
        print(f"Chosen Specialist: {specialist_role}")

        print("\n--- 2. Running Execution Crew ---")
        execution_crew = create_execution_crew(specialist_role, new_task_description)
        final_result = execution_crew.kickoff()

        print(f"\nFlow finished. Final Resolution: {final_result}")

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: Could not parse the decision from the routing agent. Error: {e}")
        print(f"Raw Output: {decision_result_str}")
        return
