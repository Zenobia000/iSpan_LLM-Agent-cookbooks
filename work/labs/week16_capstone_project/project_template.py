# project_template.py - Capstone Project Template

"""
This template provides a starting structure for Week 16 capstone projects.
Customize this template based on your specific project requirements.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from textwrap import dedent

from crewai import Agent, Crew, Task, Process
from dotenv import find_dotenv, load_dotenv

# Import course framework components
from src.core.agents import AgentConfig, StandardAgentFactory, AgentTeamBuilder
from src.core.crews import StandardCrewFactory, CrewConfig
from src.patterns.multi_agent import CollaborationBuilder, CollaborationPattern
from src.core.tools.search_tool import TavilySearchTool

# Load environment
load_dotenv(find_dotenv())


class CapstoneProjectBase(ABC):
    """
    Abstract base class for capstone projects.

    This provides a consistent structure and interface for different types
    of capstone projects while allowing for customization.
    """

    def __init__(self, project_name: str, domain: str):
        """
        Initialize the capstone project.

        Args:
            project_name: Name of your project
            domain: Domain/industry your project focuses on
        """
        self.project_name = project_name
        self.domain = domain
        self.agent_factory = StandardAgentFactory(tools=[TavilySearchTool()])
        self.crew_factory = StandardCrewFactory()

        # Initialize project components
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Any] = {}

        print(f"Initializing {project_name} for {domain} domain")
        self.setup_project()

    @abstractmethod
    def setup_project(self) -> None:
        """Set up project-specific components."""
        pass

    @abstractmethod
    def create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents for your project."""
        pass

    @abstractmethod
    def define_workflows(self) -> Dict[str, Any]:
        """Define the main workflows for your project."""
        pass

    @abstractmethod
    def execute_main_workflow(self, input_data: Any) -> Any:
        """Execute the main project workflow."""
        pass

    def get_project_info(self) -> Dict[str, Any]:
        """Get project information summary."""
        return {
            "name": self.project_name,
            "domain": self.domain,
            "agents": list(self.agents.keys()),
            "workflows": list(self.workflows.keys())
        }


class SmartContentPlatformExample(CapstoneProjectBase):
    """
    Example capstone project: Smart Content Creation Platform

    This demonstrates integration of multiple Agentic patterns:
    - Planning Pattern for content strategy
    - Multi-Agent collaboration for content creation
    - Reflection Pattern for quality improvement
    - Tool Use for research and optimization
    """

    def setup_project(self) -> None:
        """Set up the smart content platform."""
        self.agents = self.create_agents()
        self.workflows = self.define_workflows()

    def create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents for content platform."""

        # Content Strategy Agent (Planner role)
        strategy_config = AgentConfig(
            role=f"{self.domain} Content Strategist",
            goal="Develop comprehensive content strategies and coordinate content creation workflows",
            backstory=dedent(f"""
                You are an experienced content strategist specializing in {self.domain}.
                Your expertise lies in understanding audience needs, market trends, and
                creating strategic content plans that drive engagement and achieve business goals.
            """).strip(),
            allow_delegation=True
        )

        # Research Agent
        research_config = AgentConfig(
            role=f"{self.domain} Research Specialist",
            goal="Conduct thorough research on topics, trends, and competitive landscape",
            backstory=dedent(f"""
                You are a skilled research specialist with deep knowledge of {self.domain}.
                You excel at finding relevant, current information and transforming it into
                actionable insights for content creation.
            """).strip()
        )

        # Content Creator Agent
        creator_config = AgentConfig(
            role=f"{self.domain} Content Creator",
            goal="Create engaging, high-quality content in various formats",
            backstory=dedent(f"""
                You are a creative content creator specializing in {self.domain}.
                You have a talent for transforming complex information into compelling,
                accessible content that resonates with target audiences.
            """).strip()
        )

        # SEO Optimization Agent
        seo_config = AgentConfig(
            role=f"{self.domain} SEO Specialist",
            goal="Optimize content for search engines and improve online visibility",
            backstory=dedent(f"""
                You are an SEO expert with deep understanding of {self.domain} markets.
                You know how to optimize content for search engines while maintaining
                quality and readability for human audiences.
            """).strip()
        )

        # Quality Assurance Agent (Reflection role)
        qa_config = AgentConfig(
            role=f"{self.domain} Content Quality Lead",
            goal="Review and improve content quality, consistency, and effectiveness",
            backstory=dedent(f"""
                You are a quality assurance leader focused on content excellence.
                You have a keen eye for detail, consistency, and effectiveness,
                ensuring all content meets the highest standards.
            """).strip()
        )

        return {
            "strategist": self.agent_factory.create_agent(strategy_config),
            "researcher": self.agent_factory.create_agent(research_config),
            "creator": self.agent_factory.create_agent(creator_config),
            "seo": self.agent_factory.create_agent(seo_config),
            "qa": self.agent_factory.create_agent(qa_config)
        }

    def define_workflows(self) -> Dict[str, Any]:
        """Define content creation workflows."""

        # Main Content Creation Workflow (Hierarchical)
        content_workflow = CollaborationBuilder(
            CollaborationPattern.HIERARCHICAL,
            self.domain
        ).with_quality_threshold(8.0).build()

        # SEO Optimization Workflow (Sequential)
        seo_workflow = CollaborationBuilder(
            CollaborationPattern.SEQUENTIAL,
            f"{self.domain}_seo"
        ).with_quality_threshold(7.5).build()

        return {
            "content_creation": content_workflow,
            "seo_optimization": seo_workflow
        }

    def create_content_tasks(self, content_brief: str) -> List[Task]:
        """Create tasks for content creation workflow."""

        # Strategic Planning Task
        strategy_task = Task(
            description=dedent(f"""
                Develop a comprehensive content strategy for:
                {content_brief}

                Your responsibilities:
                1. Analyze the content requirements and target audience
                2. Create a detailed content plan with structure and key points
                3. Coordinate research and creation activities
                4. Ensure all content aligns with strategic objectives
                5. Manage quality and timeline requirements
            """),
            expected_output="Detailed content strategy and coordination plan",
            agent=self.agents["strategist"]
        )

        # Research Task
        research_task = Task(
            description=dedent(f"""
                Conduct comprehensive research for:
                {content_brief}

                Research areas:
                1. Current trends and developments
                2. Competitive landscape analysis
                3. Audience interests and preferences
                4. Supporting data and statistics
                5. Expert insights and quotes
            """),
            expected_output="Comprehensive research report with actionable insights",
            agent=self.agents["researcher"]
        )

        # Content Creation Task
        creation_task = Task(
            description=dedent(f"""
                Create engaging content based on the strategy and research:
                {content_brief}

                Content requirements:
                1. Follow the strategic framework provided
                2. Incorporate research insights effectively
                3. Maintain engaging and accessible tone
                4. Structure content for optimal readability
                5. Include relevant examples and case studies
            """),
            expected_output="High-quality, engaging content ready for optimization",
            agent=self.agents["creator"]
        )

        # SEO Optimization Task
        seo_task = Task(
            description=dedent(f"""
                Optimize the created content for search engines:

                Optimization areas:
                1. Keyword research and integration
                2. Meta descriptions and titles
                3. Header structure and internal linking
                4. Content structure for featured snippets
                5. Technical SEO considerations
            """),
            expected_output="SEO-optimized content with technical recommendations",
            agent=self.agents["seo"]
        )

        # Quality Assurance Task
        qa_task = Task(
            description=dedent(f"""
                Review and improve all content components:

                Quality review areas:
                1. Content accuracy and completeness
                2. Tone and style consistency
                3. Strategic alignment
                4. Technical correctness
                5. Overall effectiveness and engagement potential

                Provide specific improvement recommendations.
            """),
            expected_output="Quality assessment report with final optimized content",
            agent=self.agents["qa"],
            context=[strategy_task, research_task, creation_task, seo_task]
        )

        return [strategy_task, research_task, creation_task, seo_task, qa_task]

    def execute_main_workflow(self, content_brief: str) -> Any:
        """Execute the main content creation workflow."""

        print(f"\n{'='*60}")
        print(f"SMART CONTENT PLATFORM - {self.domain.upper()}")
        print(f"{'='*60}")
        print(f"Content Brief: {content_brief}")
        print(f"{'='*60}")

        # Create tasks
        tasks = self.create_content_tasks(content_brief)

        # Set up hierarchical crew
        crew_config = CrewConfig(
            process=Process.hierarchical,
            manager_llm="gpt-4o-mini",
            verbose=2,
            memory=True
        )

        crew = self.crew_factory.create_crew(
            list(self.agents.values()),
            tasks,
            crew_config
        )

        result = crew.kickoff()

        print(f"\n{'='*60}")
        print("CONTENT CREATION COMPLETED")
        print(f"{'='*60}")

        return result


class CapstoneProjectRunner:
    """
    Runner for executing and managing capstone projects.
    """

    def __init__(self):
        self.projects: Dict[str, CapstoneProjectBase] = {}

    def register_project(self, project: CapstoneProjectBase) -> None:
        """Register a capstone project."""
        self.projects[project.project_name] = project
        print(f"Registered project: {project.project_name}")

    def run_project(self, project_name: str, input_data: Any) -> Any:
        """Run a specific project."""
        if project_name not in self.projects:
            raise ValueError(f"Project '{project_name}' not found")

        project = self.projects[project_name]
        return project.execute_main_workflow(input_data)

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all registered projects."""
        return [project.get_project_info() for project in self.projects.values()]


def main():
    """
    Example usage of the capstone project template.
    """
    print("Week 16: Capstone Project Template Demo")
    print("="*50)

    # Create project runner
    runner = CapstoneProjectRunner()

    # Create example project
    content_platform = SmartContentPlatformExample(
        project_name="Smart Content Platform",
        domain="technology"
    )

    # Register project
    runner.register_project(content_platform)

    # Example content brief
    content_brief = dedent("""
        Create a comprehensive guide about "The Future of AI Agents in Enterprise Automation"

        Target Audience: Technology decision-makers and business executives
        Content Type: In-depth article (2000-3000 words)
        Goals: Educate about AI agent capabilities, showcase business value, drive interest

        Key Topics to Cover:
        - Current state of AI agent technology
        - Enterprise use cases and benefits
        - Implementation challenges and solutions
        - Future trends and opportunities
        - ROI considerations and case studies
    """).strip()

    # Execute project
    result = runner.run_project("Smart Content Platform", content_brief)

    # Show project information
    projects = runner.list_projects()
    print(f"\nRegistered Projects: {len(projects)}")
    for project_info in projects:
        print(f"- {project_info['name']} ({project_info['domain']})")
        print(f"  Agents: {', '.join(project_info['agents'])}")
        print(f"  Workflows: {', '.join(project_info['workflows'])}")

    return result


if __name__ == "__main__":
    main()