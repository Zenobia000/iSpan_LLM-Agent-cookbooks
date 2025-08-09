import json
import os
from textwrap import dedent
from typing import List, Dict, Optional

from crewai import Agent, Crew, Task
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

from src.core.tools.search_tool import TavilySearchTool

# Load .env file
load_dotenv(find_dotenv())


# --- 1. Pydantic Models for a Structured, Data-Driven Plan ---

class SubTask(BaseModel):
    """A model for a single task within the project plan."""
    id: int = Field(..., description="Unique identifier for the sub-task.")
    description: str = Field(..., description="Detailed description of the sub-task.")
    agent_role: str = Field(..., description="The role of the agent assigned to this task (e.g., Senior Research Specialist, Technical Content Writer, Quality Assurance Engineer).")
    dependencies: List[int] = Field(default=[], description="List of sub-task IDs that must be completed before this one can start.")
    status: str = Field(default="pending", description="Current status: pending, in_progress, completed, failed")
    result: Optional[str] = Field(default=None, description="The result or output of the completed task.")

class Risk(BaseModel):
    """A model for a potential risk in the project."""
    description: str = Field(..., description="Description of the potential risk.")
    likelihood: str = Field(..., description="Likelihood of the risk (Low, Medium, High).")
    impact: str = Field(..., description="Impact of the risk (Low, Medium, High).")
    mitigation: str = Field(..., description="Strategy to mitigate the risk.")

class ProjectPlan(BaseModel):
    """The main model for the entire structured project plan."""
    project_name: str
    tasks: List[SubTask]
    risks: List[Risk]


# --- 2. Hyper-Specialized Agents ---

class AdvancedPlannerAgents:
    """Manages agents with highly specialized roles."""

    def __init__(self):
        self.search_tool = TavilySearchTool()

    def planner_agent(self) -> Agent:
        """Agent responsible for creating the structured project plan."""
        return Agent(
            role="Expert Project Planner",
            goal="Create a detailed, structured project plan in JSON format based on the user's goal.",
            backstory="A master of project management, you excel at creating robust, machine-readable project plans.",
            verbose=True,
        )

    def risk_analyst_agent(self) -> Agent:
        """Agent specialized in identifying and mitigating risks."""
        return Agent(
            role="Senior Risk Analyst",
            goal="Identify potential risks in a project plan and suggest mitigation strategies.",
            backstory="With a keen eye for potential pitfalls, you specialize in making project plans more resilient.",
            verbose=True,
        )

    def researcher_agent(self) -> Agent:
        """The information gathering specialist."""
        return Agent(
            role="Senior Research Specialist",
            goal="Find and retrieve the most relevant and up-to-date information on any given topic.",
            backstory="An expert in information retrieval using advanced search techniques.",
            tools=[self.search_tool],
            verbose=True,
        )

    def writer_agent(self) -> Agent:
        """The content creation specialist."""
        return Agent(
            role="Technical Content Writer",
            goal="Create a clear, concise, and engaging technical article based on provided research.",
            backstory="A skilled writer who can transform complex technical information into accessible content.",
            verbose=True,
        )

    def qa_agent(self) -> Agent:
        """The quality assurance specialist."""
        return Agent(
            role="Quality Assurance Engineer",
            goal="Review the written article for technical accuracy, clarity, and overall quality.",
            backstory="A detail-oriented QA engineer with a passion for ensuring perfection.",
            verbose=True,
        )


# --- 3. Task Definitions ---

class AdvancedPlanningTasks:
    """Defines tasks that guide agents to produce structured output."""

    def get_planning_task(self, agent: Agent, goal: str, plan_schema: str) -> Task:
        """Task for the planner to generate the structured JSON plan."""
        return Task(
            description=f"Generate a structured project plan for the goal: '{goal}'.\n" \
                        f"The plan must include a sequence of tasks for research, writing, and quality assurance, " \
                        f"assigning each to the correct agent role (Senior Research Specialist, Technical Content Writer, Quality Assurance Engineer). " \
                        f"Ensure tasks have correct dependencies.",
            expected_output=f"A valid JSON object that conforms to the following Pydantic schema:\n```json\n{plan_schema}\n```",
            agent=agent,
        )


# --- 4. Custom Execution Loop (Workflow Orchestrator) ---

def main():
    """Main function to run the advanced planning and execution workflow."""
    goal = "Develop a fully automated blog writing platform using CrewAI."
    print(f"🎯 Goal: {goal}\n---")

    # Initialize agents and tasks
    agents = AdvancedPlannerAgents()
    tasks = AdvancedPlanningTasks()

    planner = agents.planner_agent()
    risk_analyst = agents.risk_analyst_agent()
    researcher = agents.researcher_agent()
    writer = agents.writer_agent()
    qa_agent = agents.qa_agent()

    # --- Phase 1: Generate the Structured Plan ---
    print("Phase 1: Generating Project Plan...")
    plan_schema = ProjectPlan.model_json_schema()
    planning_task = tasks.get_planning_task(planner, goal, json.dumps(plan_schema, indent=2))

    planning_crew = Crew(agents=[planner, risk_analyst], tasks=[planning_task], verbose=False)
    crew_output = planning_crew.kickoff()

    try:
        # Extract and clean the raw JSON string from the output
        raw_json_str = str(crew_output)

        # A more robust way to handle potential markdown code blocks
        json_start = raw_json_str.find('{')
        json_end = raw_json_str.rfind('}')
        if json_start != -1 and json_end != -1:
            cleaned_json_str = raw_json_str[json_start:json_end+1]
        else:
            cleaned_json_str = raw_json_str

        plan = ProjectPlan.parse_raw(cleaned_json_str)
        print("✅ Plan generated and validated successfully.")
        print(f"Project: {plan.project_name}")
        print(f"Total Tasks: {len(plan.tasks)}")
        print(f"Identified Risks: {len(plan.risks)}\n---")
    except Exception as e:
        print(f"❌ Error: Failed to parse the generated plan. {e}")
        print(f"Raw output from planner:\n{crew_output}")
        return

    # --- Phase 2: Execute the Plan using a DAG Runner ---
    print("Phase 2: Executing Plan...")
    task_outputs = {}
    completed_task_ids = set()

    agent_map = {
        "Senior Research Specialist": researcher,
        "Technical Content Writer": writer,
        "Quality Assurance Engineer": qa_agent,
    }

    while len(completed_task_ids) < len(plan.tasks):
        runnable_tasks = [t for t in plan.tasks if t.status == 'pending' and set(t.dependencies).issubset(completed_task_ids)]

        if not runnable_tasks:
            print("❌ Error: Deadlock detected or no runnable tasks found.")
            break

        for task_to_run in runnable_tasks:
            task_to_run.status = 'in_progress'
            print(f"🏃‍♂️ Executing Task {task_to_run.id} ({task_to_run.agent_role}): {task_to_run.description}")

            executor_agent = agent_map.get(task_to_run.agent_role)
            if not executor_agent:
                print(f"❌ Error: No agent found for role '{task_to_run.agent_role}'. Aborting task.")
                task_to_run.status = 'failed'
                continue

            # Create a specific task for the agent
            context_str = "\n".join([f"Task {dep_id} Output: {task_outputs[dep_id]}" for dep_id in task_to_run.dependencies if dep_id in task_outputs])
            
            task_description_with_context = f"{task_to_run.description}\n\n"
            if context_str:
                task_description_with_context += f"You must use the following context to complete your task:\n---\n{context_str}\n---\n"
                
            execution_task = Task(
                description=task_description_with_context,
                expected_output="The result of the task, clearly summarized.",
                agent=executor_agent,
            )

            # Run a temporary crew for this single task
            single_task_crew = Crew(agents=[executor_agent], tasks=[execution_task], verbose=False)
            result_output = single_task_crew.kickoff()
            result_str = str(result_output)

            if "error" in result_str.lower() or "failed" in result_str.lower():
                print(f"❌ Task {task_to_run.id} Failed. Result: {result_str}")
                task_to_run.status = 'failed'
                print("🚨 TRIGGERING RE-PLANNING LOGIC (DEMO) 🚨")
                return
            else:
                print(f"✅ Task {task_to_run.id} Completed.")
                task_to_run.status = 'completed'
                task_to_run.result = result_str
                task_outputs[task_to_run.id] = result_str
                completed_task_ids.add(task_to_run.id)

    print("---\nPhase 3: All tasks completed.")
    print("\n\n########################")
    print("## Final Project Output:")
    print("########################\n")
    
    final_task = max([t for t in plan.tasks if t.status == 'completed'], key=lambda t: t.id, default=None)
    if final_task:
        print(final_task.result)
    else:
        print("No tasks were successfully completed.")


if __name__ == "__main__":
    main()

