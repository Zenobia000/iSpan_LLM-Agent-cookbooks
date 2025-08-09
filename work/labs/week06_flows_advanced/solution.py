# week06_flows_advanced/solution.py
import sys
import os

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

import json
from textwrap import dedent
from typing import Dict, Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# --- Agent Definitions ---

# This agent's only job is to decide which specialist to use.
# It does NOT delegate, it simply returns the name of the specialist.
routing_agent = Agent(
    role="Intelligent Routing Agent",
    goal=dedent("""
        Analyze the user's request and current context, then decide which specialist agent is most appropriate to handle the task.
        Your final answer MUST be a JSON object with the keys 'specialist_role' and 'new_task_description'.
        """),
    backstory="You are the central dispatcher in a high-tech customer support center. Your sole purpose is to analyze incoming requests and choose the best specialist for the job. You do not solve the tasks yourself.",
    verbose=True,
)

# Worker Agent 1: Technical Support
tech_support_agent = Agent(
    role="Technical Support Specialist",
    goal="Resolve technical issues, such as website errors or login problems.",
    backstory="You are a patient and skilled tech support agent, an expert in troubleshooting complex technical problems.",
    verbose=True,
)

# Worker Agent 2: Billing Support
billing_agent = Agent(
    role="Billing Support Specialist",
    goal="Handle all inquiries related to billing, invoices, and payments.",
    backstory="You are a detail-oriented billing expert who can resolve any financial query with precision and clarity.",
    verbose=True,
)

def run_dynamic_flow(request: str, is_premium: bool):
    """
    This function orchestrates a two-step flow:
    1. A "decision" crew with a routing agent decides which specialist to use.
    2. An "execution" crew with the chosen specialist performs the task.
    """
    print(f"--- Running dynamic flow for request: '{request}' ---")

    # --- Step 1: Decision Crew ---
    # This crew's only job is to decide which agent should handle the request.
    
    routing_task = Task(
        description=dedent(f"""
            A customer has submitted a support request. Your job is to analyze it and decide which specialist to assign the task to.

            **Customer Request:**
            {request}

            **Customer Status:**
            Premium User: {is_premium}

            **Available Specialists and their roles:**
            - `Technical Support Specialist`: For technical issues like website errors, login problems, etc.
            - `Billing Support Specialist`: For financial questions about invoices, payments, etc.

            Based on the request, choose the single best specialist.
            Then, create a new, clear task description for them to execute.
            """),
        expected_output=dedent("""
            A JSON object containing two keys:
            - `specialist_role`: The role of the chosen specialist (e.g., "Technical Support Specialist").
            - `new_task_description`: A detailed and specific task description for the chosen specialist to perform.
            
            Example:
            ```json
            {{
                "specialist_role": "Technical Support Specialist",
                "new_task_description": "A customer is unable to log in because their password reset link is broken. Please investigate the issue and help them regain access to their account."
            }}
            ```
            """),
        agent=routing_agent,
    )

    decision_crew = Crew(
        agents=[routing_agent],
        tasks=[routing_task],
        process=Process.sequential,
        verbose=True
    )
    
    print("\n--- 1. Running Decision Crew ---")
    decision_result_output = decision_crew.kickoff()
    decision_result_str = str(decision_result_output)
    print(f"Decision Crew Result: {decision_result_str}")

    try:
        # A more robust way to handle potential markdown code blocks
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
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error: Could not parse the decision from the routing agent. Error: {e}")
        print(f"Raw Output: {decision_result_str}")
        return

    # --- Step 2: Execution Crew ---
    # This crew executes the task with the specialist chosen by the decision crew.
    
    agent_map = {
        "Technical Support Specialist": tech_support_agent,
        "Billing Support Specialist": billing_agent,
    }

    specialist_agent = agent_map.get(specialist_role)
    if not specialist_agent:
        print(f"❌ Error: No agent found for role '{specialist_role}'.")
        return

    execution_task = Task(
        description=new_task_description,
        expected_output="A clear and concise summary of the action taken and the final resolution.",
        agent=specialist_agent
    )

    execution_crew = Crew(
        agents=[specialist_agent],
        tasks=[execution_task],
        process=Process.sequential,
        verbose=True
    )
    
    print("\n--- 2. Running Execution Crew ---")
    final_result = execution_crew.kickoff()

    print(f"\n✅ Flow finished. Final Resolution: {final_result}")

if __name__ == "__main__":
    # Case 1: A technical issue, should be routed to Technical Support
    run_dynamic_flow(
        request="I can't log in to my account, the password reset link is broken.", 
        is_premium=False
    )

    print("\n" + "="*50 + "\n")

    # Case 2: A billing issue, should be routed to Billing Support
    run_dynamic_flow(
        request="I was charged twice for this month's subscription, I need a refund!", 
        is_premium=True
    )