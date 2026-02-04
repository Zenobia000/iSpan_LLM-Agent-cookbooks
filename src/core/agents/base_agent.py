# src/core/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from crewai import Agent
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for creating specialized agents."""
    role: str = Field(..., description="The agent's role")
    goal: str = Field(..., description="The agent's primary goal")
    backstory: str = Field(..., description="The agent's background story")
    verbose: bool = Field(default=True, description="Enable verbose output")
    allow_delegation: bool = Field(default=False, description="Allow delegation to other agents")
    memory: bool = Field(default=False, description="Enable memory for the agent")
    max_iter: int = Field(default=25, description="Maximum iterations for the agent")
    max_execution_time: Optional[int] = Field(default=None, description="Maximum execution time in seconds")


class BaseAgentFactory(ABC):
    """
    Abstract base factory for creating specialized CrewAI agents.
    This provides a consistent interface for agent creation across different patterns.
    """

    def __init__(self, tools: Optional[List[Any]] = None):
        """
        Initialize the agent factory with optional tools.

        Args:
            tools: List of tools available to agents created by this factory
        """
        self.tools = tools or []

    @abstractmethod
    def create_agent(self, config: AgentConfig, **kwargs) -> Agent:
        """
        Create a specialized agent based on configuration.

        Args:
            config: AgentConfig containing the agent's basic parameters
            **kwargs: Additional parameters specific to the agent type

        Returns:
            A configured CrewAI Agent instance
        """
        pass

    def _create_base_agent(self, config: AgentConfig, tools: Optional[List[Any]] = None) -> Agent:
        """
        Create a basic CrewAI agent with common configuration.

        Args:
            config: AgentConfig containing the agent's parameters
            tools: Optional tools specific to this agent

        Returns:
            A configured CrewAI Agent instance
        """
        agent_tools = tools or self.tools

        return Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=config.verbose,
            allow_delegation=config.allow_delegation,
            memory=config.memory,
            max_iter=config.max_iter,
            max_execution_time=config.max_execution_time,
            tools=agent_tools
        )


class StandardAgentFactory(BaseAgentFactory):
    """
    Factory for creating standard agents commonly used in multi-agent systems.
    """

    def create_agent(self, config: AgentConfig, **kwargs) -> Agent:
        """Create a standard agent with the given configuration."""
        return self._create_base_agent(config, kwargs.get('tools'))

    def create_planner_agent(self, domain: str = "general") -> Agent:
        """
        Create a planning agent for coordinating work.

        Args:
            domain: The domain this planner specializes in

        Returns:
            A configured planning agent
        """
        config = AgentConfig(
            role=f"{domain.title()} Project Planner",
            goal=f"Break down complex {domain} goals into actionable plans and coordinate team execution",
            backstory=f"An experienced project manager specialized in {domain}, skilled at creating clear, actionable steps from complex objectives and managing team coordination.",
            allow_delegation=True
        )
        return self._create_base_agent(config)

    def create_researcher_agent(self, domain: str = "general") -> Agent:
        """
        Create a research agent for gathering information.

        Args:
            domain: The domain this researcher specializes in

        Returns:
            A configured research agent
        """
        config = AgentConfig(
            role=f"{domain.title()} Research Analyst",
            goal=f"Gather comprehensive and accurate information about {domain} topics",
            backstory=f"An expert researcher with deep knowledge in {domain}, skilled at finding relevant information using various tools and sources."
        )
        return self._create_base_agent(config, self.tools)

    def create_writer_agent(self, content_type: str = "technical content") -> Agent:
        """
        Create a writing agent for content creation.

        Args:
            content_type: The type of content this writer specializes in

        Returns:
            A configured writing agent
        """
        config = AgentConfig(
            role=f"{content_type.title()} Writer",
            goal=f"Create clear, engaging, and well-structured {content_type}",
            backstory=f"A skilled writer specialized in {content_type}, capable of transforming complex information into accessible and engaging written material."
        )
        return self._create_base_agent(config)

    def create_qa_agent(self, domain: str = "general") -> Agent:
        """
        Create a quality assurance agent for reviewing work.

        Args:
            domain: The domain this QA agent specializes in

        Returns:
            A configured QA agent
        """
        config = AgentConfig(
            role=f"{domain.title()} Quality Assurance Specialist",
            goal=f"Ensure high quality and accuracy in all {domain} deliverables",
            backstory=f"A meticulous quality assurance expert with extensive experience in {domain}, focused on maintaining excellence and catching issues before final delivery."
        )
        return self._create_base_agent(config)


class AgentRole:
    """Standard agent roles for common use cases."""

    # Planning and Coordination
    PLANNER = "planner"
    COORDINATOR = "coordinator"
    MANAGER = "manager"

    # Research and Analysis
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    DATA_COLLECTOR = "data_collector"

    # Content Creation
    WRITER = "writer"
    EDITOR = "editor"
    REVIEWER = "reviewer"

    # Quality and Testing
    QA_SPECIALIST = "qa_specialist"
    TESTER = "tester"
    VALIDATOR = "validator"

    # Customer Service
    SUPPORT_AGENT = "support_agent"
    RESPONDER = "responder"
    ESCALATION_HANDLER = "escalation_handler"

    # Technical Roles
    DEVELOPER = "developer"
    ARCHITECT = "architect"
    DEPLOYER = "deployer"


class AgentTeamBuilder:
    """
    Builder class for creating teams of agents with predefined roles and relationships.
    """

    def __init__(self, factory: BaseAgentFactory):
        """
        Initialize the team builder with an agent factory.

        Args:
            factory: The agent factory to use for creating agents
        """
        self.factory = factory
        self.agents: Dict[str, Agent] = {}

    def add_agent(self, name: str, config: AgentConfig, **kwargs) -> 'AgentTeamBuilder':
        """
        Add an agent to the team.

        Args:
            name: Unique name for the agent within the team
            config: Configuration for the agent
            **kwargs: Additional parameters for agent creation

        Returns:
            Self for method chaining
        """
        self.agents[name] = self.factory.create_agent(config, **kwargs)
        return self

    def add_standard_team(self, domain: str = "general") -> 'AgentTeamBuilder':
        """
        Add a standard team (planner, researcher, writer, qa) for the given domain.

        Args:
            domain: The domain the team will work in

        Returns:
            Self for method chaining
        """
        if isinstance(self.factory, StandardAgentFactory):
            self.agents.update({
                "planner": self.factory.create_planner_agent(domain),
                "researcher": self.factory.create_researcher_agent(domain),
                "writer": self.factory.create_writer_agent(f"{domain} content"),
                "qa": self.factory.create_qa_agent(domain)
            })
        return self

    def build(self) -> Dict[str, Agent]:
        """
        Build and return the team of agents.

        Returns:
            Dictionary mapping agent names to Agent instances
        """
        return self.agents.copy()

    def get_agent_list(self) -> List[Agent]:
        """
        Get the agents as a list (useful for CrewAI Crew initialization).

        Returns:
            List of Agent instances
        """
        return list(self.agents.values())