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
        """The initial task for the planner to break down and coordinate."""
        return Task(
            description=dedent(f"""
                As the Project Planner, you need to coordinate the creation of a blog post about: {topic}

                Your responsibilities:
                1. First, delegate research to the Research Analyst to gather comprehensive information about the topic
                2. Then, delegate writing to the Technical Writer to create a blog post using the research findings
                3. Ensure the final output meets quality standards

                Use delegation to assign specific tasks to team members and coordinate their work.
            """),
            expected_output=dedent(
                """
                A well-coordinated blog post creation process where:
                1. Research has been completed by the Research Analyst
                2. A high-quality blog post has been written by the Technical Writer
                3. The final blog post is comprehensive, well-structured, and engaging
                """
            ),
            agent=agent,
        )

    def research_task(self, agent: Agent, topic: str) -> Task:
        """Task for the researcher to gather information."""
        return Task(
            description=dedent(f"""
                Conduct comprehensive research on: {topic}

                Find and analyze:
                - Key differences between AI LLM, VLM, single-modal, and multi-modal models
                - Technical specifications and capabilities
                - Use cases and applications
                - Current trends and developments
                - Examples of each type of model

                Use your search tools to gather the most current and accurate information.
            """),
            expected_output=dedent(
                """
                A comprehensive research report containing:
                - Clear definitions of each model type
                - Detailed comparison of capabilities
                - Real-world examples and applications
                - Current industry trends
                - Technical specifications and limitations
                """
            ),
            agent=agent,
        )

    def writing_task(self, agent: Agent, topic: str) -> Task:
        """Task for the writer to create the blog post."""
        return Task(
            description=dedent(f"""
                Write an engaging and informative blog post about: {topic}

                Use the research findings to create:
                - An compelling introduction
                - Clear explanations of different model types
                - Comparative analysis sections
                - Practical examples and use cases
                - A conclusion with key takeaways

                Make the content accessible to both technical and non-technical readers.
            """),
            expected_output=dedent(
                """
                A well-structured blog post with:
                - Engaging title and introduction
                - Clear section headings
                - Easy-to-understand explanations
                - Comparative tables or lists where appropriate
                - Practical examples
                - Strong conclusion
                - Proper formatting for web publication
                """
            ),
            agent=agent,
            # Note: In hierarchical process, the manager coordinates task execution order
        )


def main():
    """Sets up and runs the basic planning crew."""
    agents = BasicPlannerAgents()

    # Create worker agent instances (no manual planner needed in hierarchical mode)
    researcher = agents.researcher_agent()
    writer = agents.writer_agent()

    # Define the topic and create all tasks
    topic = "The difference between AI LLM, VLM, single-modal, and multi-modal models"
    tasks = BasicPlanningTasks()

    # Create tasks for worker agents
    research_task = tasks.research_task(researcher, topic)
    writing_task = tasks.writing_task(writer, topic)

    # Set up task dependencies - writing depends on research
    writing_task.context = [research_task]

    # Setup the crew with hierarchical process
    # CrewAI will automatically create a "Crew Manager" to coordinate tasks
    crew = Crew(
        agents=[researcher, writer],  # Only worker agents
        tasks=[research_task, writing_task],  # Worker tasks
        process=Process.hierarchical,  # Automatic manager coordination
        manager_llm="gpt-4o-mini",
        verbose=True,
    )

    print("======================================")
    print(f"## Goal: Create a blog post about: {topic}")
    print("## Process: Hierarchical with planner coordination")
    print("======================================")

    result = crew.kickoff()

    print("\n\n########################")
    print("## Final Blog Post:")
    print("########################\n")
    print(result)


if __name__ == "__main__":
    main()
