# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week06_flows_advanced_refactored\agent_definitions.py
from textwrap import dedent
from crewai import Agent

# Decision Agent
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

# A dictionary to easily access agents by their role
specialists = {
    "Technical Support Specialist": tech_support_agent,
    "Billing Support Specialist": billing_agent,
}
