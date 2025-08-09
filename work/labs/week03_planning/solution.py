import os
from textwrap import dedent

from crewai import Agent, Crew, Process, Task
from dotenv import find_dotenv, load_dotenv

# Import the consolidated search tool
from src.core.tools.search_tool import TavilySearchTool

# Load the .env file
load_dotenv(find_dotenv())


class BasicPlannerAgents:
    """Manages agents for the basic planning crew."""

    def __init__(self):
        self.search_tool = TavilySearchTool()

    def planner_agent(self) -> Agent:
        """The manager agent that breaks down the main goal."""
        return Agent(
            role="Project Planner",
            goal="Break down a given goal into a simple plan of research and writing steps.",
            backstory="An experienced project manager, I create clear, actionable steps from complex goals.",
            allow_delegation=True,
            verbose=True,
        )

    def researcher_agent(self) -> Agent:
        """The worker agent that performs basic research."""
        return Agent(
            role="Research Analyst",
            goal="Gather the latest technical information on a given topic.",
            backstory="I am an expert at finding relevant information using search tools.",
            tools=[self.search_tool],
            verbose=True,
        )

    def writer_agent(self) -> Agent:
        """The worker agent that writes content based on research."""
        return Agent(
            role="Technical Writer",
            goal="Write a clear and engaging technical blog post based on provided research.",
            backstory="I am a skilled writer who can turn complex topics into easy-to-understand articles.",
            verbose=True,
        )


class BasicPlanningTasks:
    """Defines tasks for the basic planning crew."""

    def planning_task(self, agent: Agent, topic: str) -> Task:
        """The initial task for the planner to break down."""
        return Task(
            description=f"Develop a plan to create a blog post about: {topic}",
            expected_output=dedent(
                """
                A structured list of tasks to be delegated:
                1. A research task for the Research Analyst to find information. This task should NOT request raw content.
                2. A writing task for the Technical Writer, which will use the research findings.
                """
            ),
            agent=agent,
        )


def main():
    """Sets up and runs the basic planning crew."""
    agents = BasicPlannerAgents()

    # Create agent instances
    planner = agents.planner_agent()
    researcher = agents.researcher_agent()
    writer = agents.writer_agent()

    # Define the topic and create the initial task
    topic = "The difference between AI LLM, VLM, single-modal, and multi-modal models"
    tasks = BasicPlanningTasks()
    plan_task = tasks.planning_task(planner, topic)

    # Setup the crew
    crew = Crew(
        agents=[planner, researcher, writer],
        tasks=[plan_task],
        process=Process.hierarchical,
        manager_llm="gpt-4.1-mini",
        verbose=2,
    )

    print("======================================")
    print(f"## Goal: Create a blog post about: {topic}")
    print("======================================")

    result = crew.kickoff()

    print("\n\n########################")
    print("## Final Blog Post:")
    print("########################\n")
    print(result)


if __name__ == "__main__":
    main()
