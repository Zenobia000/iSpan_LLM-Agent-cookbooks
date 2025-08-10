# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week06_flows_advanced_refactored\decision_crew_factory.py
from textwrap import dedent
from crewai import Task, Crew, Process
from agent_definitions import routing_agent

def create_decision_crew(request: str, is_premium: bool) -> Crew:
    """Factory function to create the decision-making crew."""
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

    return Crew(
        agents=[routing_agent],
        tasks=[routing_task],
        process=Process.sequential,
        verbose=True
    )
