# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week06_flows_advanced_refactored\execution_crew_factory.py
from crewai import Task, Crew, Process
from agent_definitions import specialists

def create_execution_crew(specialist_role: str, task_description: str) -> Crew:
    """Factory function to create the specialist execution crew."""
    specialist_agent = specialists.get(specialist_role)
    if not specialist_agent:
        raise ValueError(f"No agent found for role '{specialist_role}'.")

    execution_task = Task(
        description=task_description,
        expected_output="A clear and concise summary of the action taken and the final resolution.",
        agent=specialist_agent
    )

    return Crew(
        agents=[specialist_agent],
        tasks=[execution_task],
        process=Process.sequential,
        verbose=True
    )
