# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week12_testing_qa\test_agents_and_crews.py
import unittest
from crewai import Agent

# Imports from the code to be tested
from agent_definitions import routing_agent, tech_support_agent, billing_agent, specialists

class TestWeek12AgentDefinitions(unittest.TestCase):
    """Unit tests for the agent definitions from week12."""

    def test_routing_agent_creation(self):
        """Test if the routing_agent is created correctly."""
        self.assertIsInstance(routing_agent, Agent)
        self.assertEqual(routing_agent.role, "Intelligent Routing Agent")
        self.assertIn("Your final answer MUST be a JSON object", routing_agent.goal)

    def test_specialist_agents_creation(self):
        """Test if the specialist agents are created correctly."""
        self.assertIsInstance(tech_support_agent, Agent)
        self.assertEqual(tech_support_agent.role, "Technical Support Specialist")

        self.assertIsInstance(billing_agent, Agent)
        self.assertEqual(billing_agent.role, "Billing Support Specialist")

    def test_specialists_dictionary(self):
        """Test if the specialists dictionary is structured correctly."""
        self.assertIn("Technical Support Specialist", specialists)
        self.assertIn("Billing Support Specialist", specialists)
        self.assertIs(specialists["Technical Support Specialist"], tech_support_agent)
        self.assertIs(specialists["Billing Support Specialist"], billing_agent)
        self.assertEqual(len(specialists), 2)

if __name__ == '__main__':
    unittest.main()