# src/core/crews/crew_factory.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.base_agent import AgentTeamBuilder, StandardAgentFactory, AgentConfig


class CrewConfig(BaseModel):
    """Configuration for creating CrewAI crews."""
    process: Process = Field(default=Process.sequential, description="The crew's execution process")
    verbose: Union[bool, int] = Field(default=2, description="Verbosity level for crew execution")
    memory: bool = Field(default=False, description="Enable crew memory")
    manager_llm: Optional[str] = Field(default=None, description="LLM model for hierarchical manager")
    max_execution_time: Optional[int] = Field(default=None, description="Maximum execution time in seconds")
    share_crew: bool = Field(default=False, description="Enable crew sharing")
    step_callback: Optional[Any] = Field(default=None, description="Callback function for each step")


class BaseCrewFactory(ABC):
    """
    Abstract base factory for creating specialized CrewAI crews.
    This provides a consistent interface for crew creation across different patterns.
    """

    def __init__(self, agent_factory: Optional[StandardAgentFactory] = None):
        """
        Initialize the crew factory with an agent factory.

        Args:
            agent_factory: Factory for creating agents. If None, creates a default one.
        """
        self.agent_factory = agent_factory or StandardAgentFactory()

    @abstractmethod
    def create_crew(self, agents: List[Agent], tasks: List[Task], config: CrewConfig) -> Crew:
        """
        Create a specialized crew based on configuration.

        Args:
            agents: List of agents for the crew
            tasks: List of tasks for the crew
            config: CrewConfig containing the crew's parameters

        Returns:
            A configured CrewAI Crew instance
        """
        pass

    def _create_base_crew(self, agents: List[Agent], tasks: List[Task], config: CrewConfig) -> Crew:
        """
        Create a basic CrewAI crew with common configuration.

        Args:
            agents: List of agents for the crew
            tasks: List of tasks for the crew
            config: CrewConfig containing the crew's parameters

        Returns:
            A configured CrewAI Crew instance
        """
        crew_params = {
            "agents": agents,
            "tasks": tasks,
            "process": config.process,
            "verbose": config.verbose,
            "memory": config.memory,
            "share_crew": config.share_crew,
        }

        # Add optional parameters if they're set
        if config.manager_llm:
            crew_params["manager_llm"] = config.manager_llm
        if config.max_execution_time:
            crew_params["max_execution_time"] = config.max_execution_time
        if config.step_callback:
            crew_params["step_callback"] = config.step_callback

        return Crew(**crew_params)


class StandardCrewFactory(BaseCrewFactory):
    """
    Factory for creating standard crew configurations.
    """

    def create_crew(self, agents: List[Agent], tasks: List[Task], config: CrewConfig) -> Crew:
        """Create a standard crew with the given configuration."""
        return self._create_base_crew(agents, tasks, config)

    def create_sequential_crew(self, agents: List[Agent], tasks: List[Task], **kwargs) -> Crew:
        """
        Create a crew with sequential process.

        Args:
            agents: List of agents for the crew
            tasks: List of tasks for the crew
            **kwargs: Additional configuration options

        Returns:
            A configured sequential Crew
        """
        config = CrewConfig(
            process=Process.sequential,
            **kwargs
        )
        return self._create_base_crew(agents, tasks, config)

    def create_hierarchical_crew(self, manager: Agent, workers: List[Agent], tasks: List[Task],
                               manager_llm: str = "gpt-4o-mini", **kwargs) -> Crew:
        """
        Create a crew with hierarchical process.

        Args:
            manager: The manager agent
            workers: List of worker agents
            tasks: List of tasks for the crew
            manager_llm: LLM model for the manager
            **kwargs: Additional configuration options

        Returns:
            A configured hierarchical Crew
        """
        all_agents = [manager] + workers
        config = CrewConfig(
            process=Process.hierarchical,
            manager_llm=manager_llm,
            **kwargs
        )
        return self._create_base_crew(all_agents, tasks, config)

    def create_consensus_crew(self, agents: List[Agent], tasks: List[Task], **kwargs) -> Crew:
        """
        Create a crew with consensus process.

        Args:
            agents: List of agents for the crew
            tasks: List of tasks for the crew
            **kwargs: Additional configuration options

        Returns:
            A configured consensus Crew
        """
        config = CrewConfig(
            process=Process.consensus,
            **kwargs
        )
        return self._create_base_crew(agents, tasks, config)


class PrebuiltCrewFactory(StandardCrewFactory):
    """
    Factory for creating common, prebuilt crew configurations.
    """

    def create_research_crew(self, topic: str, **kwargs) -> Crew:
        """
        Create a research-focused crew.

        Args:
            topic: The research topic
            **kwargs: Additional configuration options

        Returns:
            A configured research crew
        """
        from ..tasks.research_tasks import ResearchTaskFactory

        # Create agents
        team_builder = AgentTeamBuilder(self.agent_factory)
        team = team_builder.add_standard_team("research").build()

        # Create tasks
        task_factory = ResearchTaskFactory()
        tasks = [
            task_factory.create_research_task(team["researcher"], topic),
            task_factory.create_analysis_task(team["analyst"] if "analyst" in team else team["qa"], topic),
            task_factory.create_report_task(team["writer"], topic)
        ]

        return self.create_sequential_crew(list(team.values()), tasks, **kwargs)

    def create_content_crew(self, content_type: str, topic: str, **kwargs) -> Crew:
        """
        Create a content creation crew.

        Args:
            content_type: Type of content to create
            topic: The content topic
            **kwargs: Additional configuration options

        Returns:
            A configured content creation crew
        """
        from ..tasks.content_tasks import ContentTaskFactory

        # Create agents
        team_builder = AgentTeamBuilder(self.agent_factory)
        team = team_builder.add_standard_team("content").build()

        # Create tasks
        task_factory = ContentTaskFactory()
        tasks = [
            task_factory.create_planning_task(team["planner"], content_type, topic),
            task_factory.create_research_task(team["researcher"], topic),
            task_factory.create_writing_task(team["writer"], content_type, topic),
            task_factory.create_review_task(team["qa"], content_type)
        ]

        # Use hierarchical process with planner as manager
        return self.create_hierarchical_crew(
            team["planner"],
            [team["researcher"], team["writer"], team["qa"]],
            tasks,
            **kwargs
        )

    def create_customer_service_crew(self, domain: str = "general", **kwargs) -> Crew:
        """
        Create a customer service crew.

        Args:
            domain: The service domain
            **kwargs: Additional configuration options

        Returns:
            A configured customer service crew
        """
        from ..tasks.service_tasks import ServiceTaskFactory

        # Create specialized customer service agents
        planner_config = AgentConfig(
            role=f"{domain.title()} Service Coordinator",
            goal=f"Coordinate customer service responses and escalations in {domain}",
            backstory=f"An experienced customer service manager in {domain}, skilled at triaging requests and coordinating team responses.",
            allow_delegation=True
        )

        responder_config = AgentConfig(
            role=f"{domain.title()} Support Specialist",
            goal=f"Provide helpful and accurate responses to customer inquiries about {domain}",
            backstory=f"A friendly and knowledgeable support specialist with expertise in {domain} products and services."
        )

        escalation_config = AgentConfig(
            role=f"{domain.title()} Technical Expert",
            goal=f"Handle complex technical issues and escalations in {domain}",
            backstory=f"A senior technical expert in {domain}, capable of resolving complex issues and providing in-depth solutions."
        )

        agents = {
            "coordinator": self.agent_factory.create_agent(planner_config),
            "responder": self.agent_factory.create_agent(responder_config),
            "expert": self.agent_factory.create_agent(escalation_config)
        }

        # Create tasks
        task_factory = ServiceTaskFactory()
        tasks = [
            task_factory.create_triage_task(agents["coordinator"]),
            task_factory.create_response_task(agents["responder"]),
            task_factory.create_escalation_task(agents["expert"])
        ]

        return self.create_hierarchical_crew(
            agents["coordinator"],
            [agents["responder"], agents["expert"]],
            tasks,
            **kwargs
        )


class CrewTemplate:
    """Predefined crew templates for common use cases."""

    @staticmethod
    def get_research_template() -> Dict[str, Any]:
        """Get configuration template for research crews."""
        return {
            "agents": ["researcher", "analyst", "writer", "qa"],
            "process": Process.sequential,
            "description": "Research and analysis focused crew"
        }

    @staticmethod
    def get_content_template() -> Dict[str, Any]:
        """Get configuration template for content creation crews."""
        return {
            "agents": ["planner", "researcher", "writer", "qa"],
            "process": Process.hierarchical,
            "manager_role": "planner",
            "description": "Content creation and publishing crew"
        }

    @staticmethod
    def get_service_template() -> Dict[str, Any]:
        """Get configuration template for customer service crews."""
        return {
            "agents": ["coordinator", "responder", "expert"],
            "process": Process.hierarchical,
            "manager_role": "coordinator",
            "description": "Customer service and support crew"
        }

    @staticmethod
    def get_development_template() -> Dict[str, Any]:
        """Get configuration template for development crews."""
        return {
            "agents": ["architect", "developer", "tester", "reviewer"],
            "process": Process.hierarchical,
            "manager_role": "architect",
            "description": "Software development crew"
        }


class CrewOrchestrator:
    """
    High-level orchestrator for managing multiple crews and complex workflows.
    """

    def __init__(self, factory: BaseCrewFactory):
        """
        Initialize the orchestrator with a crew factory.

        Args:
            factory: The crew factory to use for creating crews
        """
        self.factory = factory
        self.crews: Dict[str, Crew] = {}

    def register_crew(self, name: str, crew: Crew) -> 'CrewOrchestrator':
        """
        Register a crew with a given name.

        Args:
            name: Unique name for the crew
            crew: The crew instance

        Returns:
            Self for method chaining
        """
        self.crews[name] = crew
        return self

    def execute_sequential(self, crew_names: List[str]) -> List[Any]:
        """
        Execute multiple crews sequentially.

        Args:
            crew_names: List of crew names to execute in order

        Returns:
            List of results from each crew
        """
        results = []
        for name in crew_names:
            if name in self.crews:
                result = self.crews[name].kickoff()
                results.append(result)
        return results

    def get_crew(self, name: str) -> Optional[Crew]:
        """
        Get a registered crew by name.

        Args:
            name: The crew name

        Returns:
            The crew instance or None if not found
        """
        return self.crews.get(name)