# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week06_flows_advanced_refactored\main.py
import sys
import os

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the current directory to sys.path
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from dotenv import load_dotenv
load_dotenv()

from flow_controller import run_dynamic_flow

if __name__ == "__main__":
    # Case 1: A technical issue
    run_dynamic_flow(
        request="I can't log in to my account, the password reset link is broken.", 
        is_premium=False
    )

    print("\n" + "="*50 + "\n")

    # Case 2: A billing issue
    run_dynamic_flow(
        request="I was charged twice for this month's subscription, I need a refund!", 
        is_premium=True
    )

