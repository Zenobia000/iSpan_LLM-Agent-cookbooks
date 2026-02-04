# src/patterns/multi_agent/collaboration.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Task, Process

from ...core.agents.base_agent import AgentTeamBuilder, StandardAgentFactory, AgentConfig
from ...core.crews.crew_factory import StandardCrewFactory, CrewConfig


class CollaborationPattern(Enum):
    """Different patterns of multi-agent collaboration."""
    SEQUENTIAL = "sequential"  # Agents work one after another
    HIERARCHICAL = "hierarchical"  # Manager coordinates workers
    CONSENSUS = "consensus"  # Agents work together to reach agreement
    PIPELINE = "pipeline"  # Structured data flow between agents
    SWARM = "swarm"  # Decentralized collaboration


class CommunicationProtocol(BaseModel):
    """Defines how agents communicate during collaboration."""
    message_format: str = Field(default="structured", description="Format for inter-agent messages")
    shared_memory: bool = Field(default=False, description="Whether agents share memory")
    handoff_rules: Dict[str, str] = Field(default_factory=dict, description="Rules for agent handoffs")
    escalation_rules: Dict[str, str] = Field(default_factory=dict, description="Rules for escalating tasks")


class CollaborationConfig(BaseModel):
    """Configuration for multi-agent collaboration."""
    pattern: CollaborationPattern = Field(..., description="The collaboration pattern to use")
    protocol: CommunicationProtocol = Field(default_factory=CommunicationProtocol, description="Communication protocol")
    domain: str = Field(default="general", description="The domain of collaboration")
    quality_threshold: float = Field(default=8.0, description="Minimum quality threshold for completion")
    max_iterations: int = Field(default=3, description="Maximum number of collaboration iterations")


class BaseCollaborationOrchestrator(ABC):
    """
    Abstract base class for orchestrating multi-agent collaboration.
    """

    def __init__(self, config: CollaborationConfig):
        """
        Initialize the collaboration orchestrator.

        Args:
            config: Configuration for the collaboration
        """
        self.config = config
        self.agent_factory = StandardAgentFactory()
        self.crew_factory = StandardCrewFactory()
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Task] = []

    @abstractmethod
    def setup_agents(self, **kwargs) -> Dict[str, Agent]:
        """
        Set up agents for the collaboration.

        Returns:
            Dictionary of agent name to Agent instance
        """
        pass

    @abstractmethod
    def create_tasks(self, **kwargs) -> List[Task]:
        """
        Create tasks for the collaboration.

        Returns:
            List of Task instances
        """
        pass

    @abstractmethod
    def execute_collaboration(self, **kwargs) -> Any:
        """
        Execute the multi-agent collaboration.

        Returns:
            The result of the collaboration
        """
        pass


class SequentialCollaboration(BaseCollaborationOrchestrator):
    """
    Orchestrator for sequential collaboration pattern.
    Agents work one after another in a defined order.
    """

    def setup_agents(self, roles: List[str], **kwargs) -> Dict[str, Agent]:
        """
        Set up agents for sequential collaboration.

        Args:
            roles: List of agent roles in execution order

        Returns:
            Dictionary of agent name to Agent instance
        """
        team_builder = AgentTeamBuilder(self.agent_factory)

        for role in roles:
            if role == "planner":
                agent = self.agent_factory.create_planner_agent(self.config.domain)
            elif role == "researcher":
                agent = self.agent_factory.create_researcher_agent(self.config.domain)
            elif role == "writer":
                agent = self.agent_factory.create_writer_agent(f"{self.config.domain} content")
            elif role == "qa":
                agent = self.agent_factory.create_qa_agent(self.config.domain)
            else:
                # Create custom agent
                config = AgentConfig(
                    role=f"{self.config.domain.title()} {role.title()}",
                    goal=f"Perform {role} tasks in the {self.config.domain} domain",
                    backstory=f"A specialist in {role} for {self.config.domain} projects."
                )
                agent = self.agent_factory.create_agent(config)

            team_builder.add_agent(role, AgentConfig(
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory
            ))

        self.agents = team_builder.build()
        return self.agents

    def create_tasks(self, task_descriptions: List[str], **kwargs) -> List[Task]:
        """
        Create tasks for sequential execution.

        Args:
            task_descriptions: List of task descriptions matching agent order

        Returns:
            List of Task instances
        """
        agent_names = list(self.agents.keys())
        tasks = []

        for i, (agent_name, description) in enumerate(zip(agent_names, task_descriptions)):
            agent = self.agents[agent_name]

            # Set up task dependencies
            context = []
            if i > 0:
                context = [f"task_{j}" for j in range(i)]

            task = Task(
                description=description,
                expected_output=f"High-quality output from {agent_name} following the task requirements",
                agent=agent,
                context=context if context else None
            )
            task.name = f"task_{i}"  # Set task name for context referencing
            tasks.append(task)

        self.tasks = tasks
        return tasks

    def execute_collaboration(self, **kwargs) -> Any:
        """
        Execute sequential collaboration.

        Returns:
            The final result from the sequential execution
        """
        crew_config = CrewConfig(
            process=Process.sequential,
            verbose=kwargs.get('verbose', 2)
        )

        crew = self.crew_factory.create_crew(
            list(self.agents.values()),
            self.tasks,
            crew_config
        )

        return crew.kickoff()


class HierarchicalCollaboration(BaseCollaborationOrchestrator):
    """
    Orchestrator for hierarchical collaboration pattern.
    A manager agent coordinates and delegates to worker agents.
    """

    def setup_agents(self, manager_role: str = "planner", worker_roles: List[str] = None, **kwargs) -> Dict[str, Agent]:
        """
        Set up agents for hierarchical collaboration.

        Args:
            manager_role: Role of the manager agent
            worker_roles: List of worker agent roles

        Returns:
            Dictionary of agent name to Agent instance
        """
        if worker_roles is None:
            worker_roles = ["researcher", "writer", "qa"]

        team_builder = AgentTeamBuilder(self.agent_factory)

        # Create manager
        if manager_role == "planner":
            manager = self.agent_factory.create_planner_agent(self.config.domain)
        else:
            config = AgentConfig(
                role=f"{self.config.domain.title()} {manager_role.title()}",
                goal=f"Coordinate and manage {self.config.domain} projects",
                backstory=f"An experienced manager in {self.config.domain}, skilled at delegation and coordination.",
                allow_delegation=True
            )
            manager = self.agent_factory.create_agent(config)

        self.agents["manager"] = manager

        # Create workers
        for role in worker_roles:
            if role == "researcher":
                worker = self.agent_factory.create_researcher_agent(self.config.domain)
            elif role == "writer":
                worker = self.agent_factory.create_writer_agent(f"{self.config.domain} content")
            elif role == "qa":
                worker = self.agent_factory.create_qa_agent(self.config.domain)
            else:
                config = AgentConfig(
                    role=f"{self.config.domain.title()} {role.title()}",
                    goal=f"Execute {role} tasks as directed by the manager",
                    backstory=f"A skilled specialist in {role} for {self.config.domain} projects."
                )
                worker = self.agent_factory.create_agent(config)

            self.agents[role] = worker

        return self.agents

    def create_tasks(self, coordination_task: str, worker_tasks: List[str] = None, **kwargs) -> List[Task]:
        """
        Create tasks for hierarchical execution.

        Args:
            coordination_task: Main task for the manager
            worker_tasks: Optional specific tasks for workers

        Returns:
            List of Task instances
        """
        tasks = []

        # Manager's coordination task
        manager_task = Task(
            description=coordination_task,
            expected_output="Successful coordination and delegation of work to achieve project goals",
            agent=self.agents["manager"]
        )
        tasks.append(manager_task)

        # Worker tasks (if specified)
        if worker_tasks:
            worker_names = [name for name in self.agents.keys() if name != "manager"]
            for worker_name, task_desc in zip(worker_names, worker_tasks):
                if worker_name in self.agents:
                    worker_task = Task(
                        description=task_desc,
                        expected_output=f"High-quality deliverable from {worker_name}",
                        agent=self.agents[worker_name]
                    )
                    tasks.append(worker_task)

        self.tasks = tasks
        return tasks

    def execute_collaboration(self, manager_llm: str = "gpt-4o-mini", **kwargs) -> Any:
        """
        Execute hierarchical collaboration.

        Args:
            manager_llm: LLM model for the manager agent

        Returns:
            The result from the hierarchical execution
        """
        crew_config = CrewConfig(
            process=Process.hierarchical,
            manager_llm=manager_llm,
            verbose=kwargs.get('verbose', 2)
        )

        crew = self.crew_factory.create_crew(
            list(self.agents.values()),
            self.tasks,
            crew_config
        )

        return crew.kickoff()


class CollaborationBuilder:
    """
    Builder class for setting up complex multi-agent collaborations.
    """

    def __init__(self, pattern: CollaborationPattern, domain: str = "general"):
        """
        Initialize the collaboration builder.

        Args:
            pattern: The collaboration pattern to use
            domain: The domain for the collaboration
        """
        self.config = CollaborationConfig(pattern=pattern, domain=domain)
        self.orchestrator = None

    def with_protocol(self, protocol: CommunicationProtocol) -> 'CollaborationBuilder':
        """
        Set the communication protocol.

        Args:
            protocol: The communication protocol to use

        Returns:
            Self for method chaining
        """
        self.config.protocol = protocol
        return self

    def with_quality_threshold(self, threshold: float) -> 'CollaborationBuilder':
        """
        Set the quality threshold.

        Args:
            threshold: Minimum quality threshold

        Returns:
            Self for method chaining
        """
        self.config.quality_threshold = threshold
        return self

    def with_max_iterations(self, max_iter: int) -> 'CollaborationBuilder':
        """
        Set the maximum number of iterations.

        Args:
            max_iter: Maximum iterations

        Returns:
            Self for method chaining
        """
        self.config.max_iterations = max_iter
        return self

    def build(self) -> BaseCollaborationOrchestrator:
        """
        Build the collaboration orchestrator.

        Returns:
            The configured orchestrator
        """
        if self.config.pattern == CollaborationPattern.SEQUENTIAL:
            self.orchestrator = SequentialCollaboration(self.config)
        elif self.config.pattern == CollaborationPattern.HIERARCHICAL:
            self.orchestrator = HierarchicalCollaboration(self.config)
        else:
            raise NotImplementedError(f"Pattern {self.config.pattern} not yet implemented")

        return self.orchestrator


class MultiAgentWorkflow:
    """
    High-level workflow manager for complex multi-agent collaborations.
    """

    def __init__(self, domain: str = "general"):
        """
        Initialize the workflow manager.

        Args:
            domain: The domain for workflows
        """
        self.domain = domain
        self.workflows: Dict[str, BaseCollaborationOrchestrator] = {}

    def add_workflow(self, name: str, pattern: CollaborationPattern, **config_kwargs) -> 'MultiAgentWorkflow':
        """
        Add a workflow to the manager.

        Args:
            name: Name for the workflow
            pattern: Collaboration pattern to use
            **config_kwargs: Additional configuration

        Returns:
            Self for method chaining
        """
        builder = CollaborationBuilder(pattern, self.domain)

        # Apply additional configuration
        if 'quality_threshold' in config_kwargs:
            builder.with_quality_threshold(config_kwargs['quality_threshold'])
        if 'max_iterations' in config_kwargs:
            builder.with_max_iterations(config_kwargs['max_iterations'])

        self.workflows[name] = builder.build()
        return self

    def execute_workflow(self, name: str, **execution_kwargs) -> Any:
        """
        Execute a specific workflow.

        Args:
            name: Name of the workflow to execute
            **execution_kwargs: Parameters for the execution

        Returns:
            The workflow result
        """
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found")

        orchestrator = self.workflows[name]

        # Setup agents and tasks based on execution parameters
        orchestrator.setup_agents(**execution_kwargs)
        orchestrator.create_tasks(**execution_kwargs)

        return orchestrator.execute_collaboration(**execution_kwargs)

    def get_workflow(self, name: str) -> Optional[BaseCollaborationOrchestrator]:
        """
        Get a workflow by name.

        Args:
            name: The workflow name

        Returns:
            The workflow orchestrator or None if not found
        """
        return self.workflows.get(name)