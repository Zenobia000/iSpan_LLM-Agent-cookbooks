import os
from textwrap import dedent
from typing import Dict, Any

from crewai import Agent, Crew, Process, Task
from dotenv import find_dotenv, load_dotenv

# Import our new multi-agent collaboration framework
from src.patterns.multi_agent import (
    CollaborationPattern,
    CollaborationBuilder,
    MultiAgentWorkflow
)
from src.core.agents import AgentConfig, StandardAgentFactory
from src.core.crews import StandardCrewFactory, CrewConfig
from src.core.tools.search_tool import TavilySearchTool

# Load environment
load_dotenv(find_dotenv())


class SmartCustomerServiceSystem:
    """
    Comprehensive multi-agent customer service system demonstrating advanced collaboration patterns.

    This implementation showcases:
    1. Hierarchical collaboration with coordinator oversight
    2. Specialized agent roles and responsibilities
    3. Dynamic task routing and escalation
    4. Quality assurance and feedback loops
    """

    def __init__(self, domain: str = "technology"):
        """
        Initialize the customer service system.

        Args:
            domain: The business domain for specialized service
        """
        self.domain = domain
        self.agent_factory = StandardAgentFactory(tools=[TavilySearchTool()])
        self.crew_factory = StandardCrewFactory()
        self.agents: Dict[str, Agent] = {}
        self.setup_agents()

    def setup_agents(self) -> None:
        """Set up specialized customer service agents."""

        # Service Coordinator - Manager who triages and coordinates
        coordinator_config = AgentConfig(
            role=f"{self.domain.title()} Service Coordinator",
            goal="Efficiently triage customer inquiries and coordinate appropriate responses",
            backstory=dedent(f"""
                You are an experienced customer service manager specializing in {self.domain}.
                Your expertise lies in quickly understanding customer needs, determining the right
                specialist to handle each case, and ensuring customer satisfaction through effective
                coordination and follow-up.
            """).strip(),
            allow_delegation=True,
            verbose=True
        )

        # Customer Support Specialist - Handles general inquiries
        support_config = AgentConfig(
            role=f"{self.domain.title()} Support Specialist",
            goal="Provide helpful, accurate, and friendly responses to customer inquiries",
            backstory=dedent(f"""
                You are a knowledgeable customer support specialist with expertise in {self.domain}.
                You excel at understanding customer problems, providing clear explanations, and
                offering practical solutions. Your communication style is warm, professional, and
                solution-focused.
            """).strip(),
            verbose=True
        )

        # Technical Expert - Handles complex technical issues
        technical_config = AgentConfig(
            role=f"{self.domain.title()} Technical Expert",
            goal="Resolve complex technical issues and provide in-depth technical guidance",
            backstory=dedent(f"""
                You are a senior technical expert with deep knowledge of {self.domain} systems,
                processes, and troubleshooting. You handle the most challenging technical issues
                that require specialized expertise and provide detailed technical guidance to
                both customers and other team members.
            """).strip(),
            verbose=True
        )

        # Quality Assurance Agent - Reviews and ensures quality
        qa_config = AgentConfig(
            role=f"{self.domain.title()} Quality Assurance Lead",
            goal="Ensure all customer interactions meet high quality standards",
            backstory=dedent(f"""
                You are a quality assurance leader focused on maintaining excellence in customer
                service. You review responses for accuracy, completeness, tone, and effectiveness.
                Your role is to ensure every customer receives the best possible service experience.
            """).strip(),
            verbose=True
        )

        # Create agents
        self.agents = {
            "coordinator": self.agent_factory.create_agent(coordinator_config),
            "support": self.agent_factory.create_agent(support_config),
            "technical": self.agent_factory.create_agent(technical_config),
            "qa": self.agent_factory.create_agent(qa_config)
        }

    def create_service_tasks(self, customer_inquiry: str) -> list[Task]:
        """
        Create tasks for handling a customer service inquiry.

        Args:
            customer_inquiry: The customer's inquiry or issue

        Returns:
            List of tasks for the service workflow
        """

        # Triage and Coordination Task
        triage_task = Task(
            description=dedent(f"""
                Analyze the following customer inquiry and coordinate the appropriate response:

                Customer Inquiry:
                {customer_inquiry}

                Your responsibilities:
                1. Assess the complexity and type of the inquiry
                2. Determine which specialist(s) should handle this case
                3. Delegate tasks to appropriate team members
                4. Ensure timely and comprehensive response
                5. Coordinate quality review process

                Consider factors such as:
                - Technical complexity
                - Urgency level
                - Required expertise
                - Customer communication style
            """),
            expected_output=dedent("""
                A comprehensive coordination plan including:
                - Assessment of inquiry type and complexity
                - Assigned specialist(s) and their responsibilities
                - Timeline for response
                - Quality checkpoints
                - Final coordinated response to the customer
            """),
            agent=self.agents["coordinator"]
        )

        # Support Response Task
        support_task = Task(
            description=dedent(f"""
                Provide initial support response to the customer inquiry:

                Customer Inquiry:
                {customer_inquiry}

                Your responsibilities:
                1. Acknowledge the customer's concern with empathy
                2. Provide initial guidance or solutions for standard issues
                3. Identify if technical escalation is needed
                4. Maintain professional and friendly communication tone
                5. Use search tools to gather relevant information if needed

                Focus on:
                - Customer satisfaction and experience
                - Clear, actionable guidance
                - Proactive problem-solving
            """),
            expected_output=dedent("""
                A customer-ready response including:
                - Empathetic acknowledgment of the issue
                - Clear explanation of the problem/solution
                - Step-by-step guidance where applicable
                - Next steps or escalation path if needed
                - Professional and friendly tone throughout
            """),
            agent=self.agents["support"]
        )

        # Technical Escalation Task (conditional)
        technical_task = Task(
            description=dedent(f"""
                Provide technical analysis and resolution for complex issues:

                Customer Inquiry:
                {customer_inquiry}

                Your responsibilities:
                1. Perform detailed technical analysis of the issue
                2. Research latest solutions and best practices
                3. Provide comprehensive technical guidance
                4. Create step-by-step troubleshooting instructions
                5. Identify any systemic issues or improvements needed

                Technical focus areas:
                - Root cause analysis
                - Advanced troubleshooting
                - System integration issues
                - Performance optimization
                - Security considerations
            """),
            expected_output=dedent("""
                Detailed technical response including:
                - Technical root cause analysis
                - Comprehensive solution with step-by-step instructions
                - Alternative approaches or workarounds
                - Prevention recommendations
                - Technical documentation references
            """),
            agent=self.agents["technical"]
        )

        # Quality Assurance Task
        qa_task = Task(
            description=dedent("""
                Review all responses to ensure they meet quality standards:

                Your responsibilities:
                1. Evaluate response accuracy and completeness
                2. Assess communication tone and professionalism
                3. Verify technical correctness
                4. Ensure customer satisfaction potential
                5. Provide improvement recommendations if needed

                Quality criteria:
                - Accuracy of information
                - Clarity of communication
                - Completeness of solution
                - Professional tone
                - Customer-centric approach
            """),
            expected_output=dedent("""
                Quality assessment report including:
                - Overall quality score and assessment
                - Specific feedback on each response component
                - Recommendations for improvement
                - Final approved response for the customer
                - Learning points for team improvement
            """),
            agent=self.agents["qa"],
            context=[triage_task, support_task, technical_task]  # Review all previous tasks
        )

        return [triage_task, support_task, technical_task, qa_task]

    def handle_customer_inquiry(self, customer_inquiry: str, verbose: int = 2) -> Any:
        """
        Process a customer inquiry through the multi-agent service system.

        Args:
            customer_inquiry: The customer's inquiry
            verbose: Verbosity level for execution

        Returns:
            The final service response
        """
        print(f"\n{'='*60}")
        print(f"SMART CUSTOMER SERVICE SYSTEM")
        print(f"Domain: {self.domain.title()}")
        print(f"{'='*60}")
        print(f"\nCustomer Inquiry:")
        print(f"{customer_inquiry}")
        print(f"\n{'='*60}")

        # Create tasks for this inquiry
        tasks = self.create_service_tasks(customer_inquiry)

        # Create hierarchical crew with coordinator as manager
        crew_config = CrewConfig(
            process=Process.hierarchical,
            manager_llm="gpt-4o-mini",
            verbose=verbose,
            memory=True  # Enable memory for better context sharing
        )

        crew = self.crew_factory.create_crew(
            list(self.agents.values()),
            tasks,
            crew_config
        )

        result = crew.kickoff()

        print(f"\n{'='*60}")
        print("FINAL SERVICE RESPONSE")
        print(f"{'='*60}")

        return result


class MultiAgentCollaborationDemo:
    """
    Demonstration of different multi-agent collaboration patterns using our framework.
    """

    def __init__(self):
        """Initialize the collaboration demo."""
        self.workflow_manager = MultiAgentWorkflow("customer_service")

    def demo_sequential_collaboration(self, topic: str) -> Any:
        """
        Demonstrate sequential collaboration for content creation.

        Args:
            topic: Topic for content creation

        Returns:
            Result of sequential collaboration
        """
        print(f"\n{'='*60}")
        print("SEQUENTIAL COLLABORATION DEMO")
        print("Pattern: Research → Write → Review → Publish")
        print(f"{'='*60}")

        # Set up sequential workflow
        self.workflow_manager.add_workflow(
            "content_creation",
            CollaborationPattern.SEQUENTIAL,
            quality_threshold=7.5
        )

        # Execute workflow
        result = self.workflow_manager.execute_workflow(
            "content_creation",
            roles=["researcher", "writer", "qa"],
            task_descriptions=[
                f"Research comprehensive information about {topic}",
                f"Write an engaging article about {topic} based on the research",
                f"Review and improve the article for quality and accuracy"
            ]
        )

        return result

    def demo_hierarchical_collaboration(self, project_goal: str) -> Any:
        """
        Demonstrate hierarchical collaboration for project management.

        Args:
            project_goal: The project goal to achieve

        Returns:
            Result of hierarchical collaboration
        """
        print(f"\n{'='*60}")
        print("HIERARCHICAL COLLABORATION DEMO")
        print("Pattern: Manager coordinates Workers")
        print(f"{'='*60}")

        # Set up hierarchical workflow
        self.workflow_manager.add_workflow(
            "project_management",
            CollaborationPattern.HIERARCHICAL,
            quality_threshold=8.0
        )

        # Execute workflow
        result = self.workflow_manager.execute_workflow(
            "project_management",
            manager_role="planner",
            worker_roles=["researcher", "writer"],
            coordination_task=f"Coordinate the team to achieve: {project_goal}",
            worker_tasks=[
                f"Conduct research needed for: {project_goal}",
                f"Create deliverables for: {project_goal}"
            ]
        )

        return result


def main():
    """
    Main function demonstrating Week 15 multi-agent collaboration patterns.
    """
    print("Week 15: Multi-Agent Collaboration System")
    print("Demonstrating Advanced Agent Coordination Patterns")
    print("=" * 70)

    # 1. Smart Customer Service System (Main Demo)
    print("\n1. SMART CUSTOMER SERVICE SYSTEM DEMO")
    service_system = SmartCustomerServiceSystem("technology")

    customer_inquiry = dedent("""
        Hi, I'm having trouble with my cloud deployment. My application was working fine
        yesterday, but now I'm getting 504 Gateway Timeout errors when users try to access
        certain features. The error seems to be intermittent - sometimes it works, sometimes
        it doesn't. I've checked the basic server status and everything looks normal, but
        I'm not sure what's causing these random timeouts. This is affecting our production
        environment and our customers are starting to complain. Can you help me figure out
        what's going wrong and how to fix it?
    """).strip()

    service_result = service_system.handle_customer_inquiry(customer_inquiry)

    # 2. Multi-Agent Collaboration Patterns Demo
    print("\n\n2. COLLABORATION PATTERNS DEMONSTRATION")
    demo = MultiAgentCollaborationDemo()

    # Sequential Pattern
    sequential_result = demo.demo_sequential_collaboration(
        "The impact of AI agents on customer service automation"
    )

    # Hierarchical Pattern
    hierarchical_result = demo.demo_hierarchical_collaboration(
        "Create a comprehensive guide for implementing multi-agent systems"
    )

    print("\n" + "="*70)
    print("DEMO COMPLETED")
    print("="*70)
    print("\nKey Patterns Demonstrated:")
    print("✅ Hierarchical Coordination (Customer Service)")
    print("✅ Sequential Workflow (Content Creation)")
    print("✅ Specialized Agent Roles")
    print("✅ Dynamic Task Routing")
    print("✅ Quality Assurance Integration")
    print("✅ Multi-pattern Workflow Management")

    return {
        "service_result": service_result,
        "sequential_result": sequential_result,
        "hierarchical_result": hierarchical_result
    }


if __name__ == "__main__":
    main()