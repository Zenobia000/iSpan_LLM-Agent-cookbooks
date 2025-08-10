# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week05_flows_basics_refactored\main.py
import sys
import os

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from flow_controller import run_logistics_flow

if __name__ == "__main__":
    # Scenario 1: Low stock, requires ordering
    run_logistics_flow(stock_level=30)
    
    print("\n" + "="*50 + "\n")
    
    # Scenario 2: Sufficient stock, standby
    run_logistics_flow(stock_level=100)

