# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week12_testing_qa\benchmark_fixed.py
import sys
import os
import time
import pandas as pd
from typing import List, Dict, Any
import json

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

# Import the crew factory functions
from work.labs.week12_testing_qa.decision_crew_factory import create_decision_crew
from work.labs.week12_testing_qa.execution_crew_factory import create_execution_crew

# --- 1. Define Test Cases ---
# A list of standard inputs to test the crews against.
benchmark_cases: List[Dict[str, Any]] = [
    {
        "name": "Technical Support - Login Issue",
        "request": "I can't log in to my account, the password reset link is broken.",
        "is_premium": False
    },
    {
        "name": "Billing Support - Double Charge",
        "request": "I was charged twice for this month's subscription, I need a refund!",
        "is_premium": True
    },
    {
        "name": "Technical Support - Slow Website",
        "request": "The main dashboard of the website is loading very slowly for the past hour.",
        "is_premium": True
    },
    {
        "name": "Billing Support - Unclear Invoice",
        "request": "I don't understand the charges on my latest invoice, can someone explain them?",
        "is_premium": False
    }
]

# --- 2. Define A/B Testing Setups ---
# We will create two versions of the crew to compare.

# Setup A: Standard Crew (as defined in week06)
def run_crew_a(request: str, is_premium: bool) -> Dict[str, Any]:
    """Runs the standard version of the crew."""
    start_time = time.time()
    
    try:
        # Step 1: Run the decision crew
        decision_crew = create_decision_crew(request, is_premium)
        decision_result = decision_crew.kickoff()
        
        # Step 2: Parse the decision
        decision_data = json.loads(decision_result)
        specialist_role = decision_data['specialist_role']
        new_task_description = decision_data['new_task_description']
        
        # Step 3: Run the execution crew
        execution_crew = create_execution_crew(specialist_role, new_task_description)
        final_result = execution_crew.kickoff()
        
    except Exception as e:
        final_result = f"Error: {e}"

    end_time = time.time()
    return {"output": final_result, "time": end_time - start_time}

# Setup B: Modified Crew (e.g., with a different prompt strategy or model)
def run_crew_b(request: str, is_premium: bool) -> Dict[str, Any]:
    """Runs the modified version of the crew for comparison."""
    start_time = time.time()
    
    try:
        # We can simulate a modification, for example, by adding more context for the decision agent
        modified_request = f"[Modified Prompt] Priority: {'High' if is_premium else 'Normal'}. Request: {request}"
        
        # Step 1: Run the decision crew
        decision_crew = create_decision_crew(modified_request, is_premium)
        decision_result = decision_crew.kickoff()
        
        # Step 2: Parse the decision
        decision_data = json.loads(decision_result)
        specialist_role = decision_data['specialist_role']
        new_task_description = decision_data['new_task_description']
        
        # Step 3: Run the execution crew with a potentially different model or config
        execution_crew = create_execution_crew(specialist_role, new_task_description)
        final_result = execution_crew.kickoff()

    except Exception as e:
        final_result = f"Error: {e}"

    end_time = time.time()
    return {"output": final_result, "time": end_time - start_time}

# --- 3. Run Benchmark and A/B Test ---

def run_benchmark():
    """Executes the benchmark and A/B test and prints the results."""
    results = []

    print("Starting A/B Performance Benchmark...")
    print("-" * 50)

    for i, case in enumerate(benchmark_cases):
        print(f"Running Case {i+1}/{len(benchmark_cases)}: {case['name']}")
        
        result_a = run_crew_a(case["request"], case["is_premium"])
        result_b = run_crew_b(case["request"], case["is_premium"])
        
        results.append({
            "Test Case": case["name"],
            "Crew A Time (s)": f"{result_a['time']:.4f}",
            "Crew A Output": result_a['output'],
            "Crew B Time (s)": f"{result_b['time']:.4f}",
            "Crew B Output": result_b['output']
        })

    # --- 4. Display Results ---
    print("\nBenchmark Results")
    print("=" * 50)
    
    df = pd.DataFrame(results)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 80)
    
    print(df)
    print("\nBenchmark complete.")

if __name__ == "__main__":
    run_benchmark()
