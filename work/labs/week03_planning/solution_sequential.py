#!/usr/bin/env python3
"""
CrewAI Basic Planning Pattern with Sequential Process and Explicit Planner
展示如何使用显式的 Planner Agent 进行任务规划和协调
"""

import sys
import os

# Add project root to sys.path for consistent imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from textwrap import dedent
from crewai import Agent, Crew, Process, Task
from src.core.tools.search_tool import TavilySearchTool


class BasicPlannerAgents:
    """Defines the basic agents for planning tasks."""

    def __init__(self):
        self.search_tool = TavilySearchTool()

    def planner_agent(self) -> Agent:
        """The planner agent that coordinates and delegates tasks."""
        return Agent(
            role="Project Planner",
            goal="Break down complex goals into actionable plans and coordinate team members to achieve them.",
            backstory="An experienced project manager who excels at creating clear, actionable plans from complex requirements. "
                     "You understand how to delegate tasks effectively and ensure quality outcomes.",
            allow_delegation=True,
            verbose=True,
        )

    def researcher_agent(self) -> Agent:
        """The worker agent that performs research."""
        return Agent(
            role="Research Analyst",
            goal="Gather comprehensive and accurate information on given topics.",
            backstory="An expert researcher skilled at finding relevant, up-to-date information using search tools. "
                     "You provide thorough, well-organized research findings.",
            tools=[self.search_tool],
            verbose=True,
        )

    def writer_agent(self) -> Agent:
        """The worker agent that writes content."""
        return Agent(
            role="Technical Writer",
            goal="Create clear, engaging, and well-structured technical content.",
            backstory="A skilled technical writer who can transform complex research into accessible, engaging articles. "
                     "You understand both technical and non-technical audiences.",
            verbose=True,
        )


class SequentialPlanningTasks:
    """Defines tasks for sequential planning with explicit coordination."""

    def planning_task(self, agent: Agent, topic: str) -> Task:
        """The coordination task that plans the overall workflow."""
        return Task(
            description=dedent(f"""
                As the Project Planner, create a detailed plan for writing a comprehensive blog post about: {topic}

                Your plan should:
                1. Identify the key research areas needed
                2. Define the structure and approach for the blog post
                3. Set clear expectations for the research and writing phases
                4. Ensure the final deliverable will be engaging and informative

                Create a structured plan that will guide the team to success.
            """),
            expected_output=dedent("""
                A detailed project plan including:
                - Research objectives and key areas to investigate
                - Proposed blog post structure and sections
                - Quality criteria and success metrics
                - Clear guidance for team members
            """),
            agent=agent,
        )

    def research_task(self, agent: Agent, topic: str) -> Task:
        """Research task to gather information."""
        return Task(
            description=dedent(f"""
                Based on the project plan, conduct comprehensive research on: {topic}

                Find and analyze:
                - Key differences and definitions
                - Technical specifications and capabilities
                - Use cases and applications
                - Current trends and developments
                - Examples of each type of model

                Use your search tools to gather the most current and accurate information.
            """),
            expected_output=dedent("""
                A comprehensive research report including:
                - Clear definitions of each model type
                - Technical comparisons and specifications
                - Real-world examples and use cases
                - Current trends and future directions
                - Properly cited sources and references
            """),
            agent=agent,
        )

    def writing_task(self, agent: Agent, topic: str) -> Task:
        """Writing task to create the blog post."""
        return Task(
            description=dedent(f"""
                Using the project plan and research findings, write an engaging and informative blog post about: {topic}

                Create content with:
                - A compelling introduction that hooks readers
                - Clear explanations of different model types
                - Comparative analysis sections
                - Practical examples and use cases
                - A conclusion with key takeaways

                Make the content accessible to both technical and non-technical readers.
                Format it for web publication with proper headings and structure.
            """),
            expected_output=dedent("""
                A well-structured blog post with:
                - Engaging title and introduction
                - Clear section headings
                - Easy-to-understand explanations
                - Comparative tables or lists where appropriate
                - Practical examples
                - Strong conclusion
                - Proper formatting for web publication
            """),
            agent=agent,
        )


def main():
    """Sets up and runs the sequential planning crew with explicit planner."""
    agents = BasicPlannerAgents()

    # Create all agent instances including explicit planner
    planner = agents.planner_agent()
    researcher = agents.researcher_agent()
    writer = agents.writer_agent()

    # Define the topic and create all tasks
    topic = "The difference between AI LLM, VLM, single-modal, and multi-modal models"
    tasks = SequentialPlanningTasks()

    # Create all tasks in sequence
    plan_task = tasks.planning_task(planner, topic)
    research_task = tasks.research_task(researcher, topic)
    writing_task = tasks.writing_task(writer, topic)

    # Set up task dependencies for sequential execution
    research_task.context = [plan_task]  # Research uses the plan
    writing_task.context = [plan_task, research_task]  # Writing uses plan and research

    # Setup the crew with sequential process
    crew = Crew(
        agents=[planner, researcher, writer],  # All agents including planner
        tasks=[plan_task, research_task, writing_task],  # All tasks in order
        process=Process.sequential,  # Sequential execution
        verbose=True,
    )

    print("======================================")
    print(f"## Goal: Create a blog post about: {topic}")
    print("## Process: Sequential with explicit planner")
    print("======================================")

    result = crew.kickoff()

    print("\n\n########################")
    print("## Final Blog Post:")
    print("########################\n")
    print(result)


if __name__ == "__main__":
    main()