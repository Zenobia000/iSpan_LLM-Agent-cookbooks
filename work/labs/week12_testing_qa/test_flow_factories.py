# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week12_testing_qa\test_flow_factories.py
import unittest
from unittest.mock import patch, MagicMock

# Import the factory functions and agents
from decision_crew_factory import create_decision_crew
from execution_crew_factory import create_execution_crew
from agent_definitions import routing_agent, specialists

class TestDecisionCrewFactory(unittest.TestCase):

    @patch('decision_crew_factory.Crew')
    def test_create_decision_crew_structure(self, MockCrew):
        """Test if the decision crew is created with the correct structure."""
        mock_crew_instance = MockCrew.return_value
        
        request = "I have a problem with my bill."
        is_premium = True

        # Call the factory function
        crew = create_decision_crew(request, is_premium)

        # Assert that the Crew was instantiated once
        MockCrew.assert_called_once()

        # Get the arguments passed to the Crew constructor
        args, kwargs = MockCrew.call_args
        
        # Check agents
        self.assertIn('agents', kwargs)
        self.assertEqual(len(kwargs['agents']), 1)
        self.assertIs(kwargs['agents'][0], routing_agent)

        # Check tasks
        self.assertIn('tasks', kwargs)
        self.assertEqual(len(kwargs['tasks']), 1)
        task = kwargs['tasks'][0]
        self.assertIn(request, task.description)
        self.assertIn(str(is_premium), task.description)
        self.assertIs(task.agent, routing_agent)
        
        # Check that the returned object is the mocked instance
        self.assertIs(crew, mock_crew_instance)

class TestExecutionCrewFactory(unittest.TestCase):

    @patch('execution_crew_factory.Crew')
    def test_create_execution_crew_valid_role(self, MockCrew):
        """Test if the execution crew is created correctly for a valid role."""
        mock_crew_instance = MockCrew.return_value
        
        role = "Technical Support Specialist"
        task_desc = "Fix the login issue."

        # Call the factory function
        crew = create_execution_crew(role, task_desc)

        # Assert that the Crew was instantiated once
        MockCrew.assert_called_once()
        
        # Get the arguments passed to the Crew constructor
        args, kwargs = MockCrew.call_args

        # Check agents
        self.assertIn('agents', kwargs)
        self.assertEqual(len(kwargs['agents']), 1)
        self.assertIs(kwargs['agents'][0], specialists[role])

        # Check tasks
        self.assertIn('tasks', kwargs)
        self.assertEqual(len(kwargs['tasks']), 1)
        task = kwargs['tasks'][0]
        self.assertEqual(task.description, task_desc)
        self.assertIs(task.agent, specialists[role])

        # Check that the returned object is the mocked instance
        self.assertIs(crew, mock_crew_instance)

    def test_create_execution_crew_invalid_role(self):
        """Test if the factory raises ValueError for an invalid role."""
        role = "NonExistent Specialist"
        task_desc = "This should fail."

        # Assert that a ValueError is raised for an unknown role
        with self.assertRaises(ValueError) as context:
            create_execution_crew(role, task_desc)
        
        self.assertIn(f"No agent found for role '{role}'", str(context.exception))

if __name__ == '__main__':
    unittest.main()
