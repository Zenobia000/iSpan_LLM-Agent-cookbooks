# tests/patterns/tool_use/conftest.py

import pytest
from unittest.mock import Mock
from src.patterns.tool_use.decorators import clear_tool_cache
from src.patterns.tool_use.registry import UniversalToolRegistry


@pytest.fixture(autouse=True)
def clean_cache():
    """Automatically clear tool cache before each test."""
    clear_tool_cache()
    yield
    clear_tool_cache()


@pytest.fixture
def fresh_registry():
    """Provide a fresh registry for tests that need isolation."""
    return UniversalToolRegistry()


@pytest.fixture
def mock_crewai_tool():
    """Provide a mock CrewAI tool for testing."""
    from pydantic import BaseModel, Field

    class MockToolInput(BaseModel):
        query: str = Field(..., description="Search query")
        limit: int = Field(default=10, description="Maximum results")

    mock_tool = Mock()
    mock_tool.name = "mock_crewai_tool"
    mock_tool.description = "Mock CrewAI tool for testing"
    mock_tool.args_schema = MockToolInput
    mock_tool._run = Mock(return_value="mock result")

    return mock_tool


@pytest.fixture
def sample_functions():
    """Provide sample functions for testing."""
    def calculator(expression: str) -> str:
        """Calculate mathematical expressions."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    def text_processor(text: str, operation: str = "upper") -> str:
        """Process text with various operations."""
        if operation == "upper":
            return text.upper()
        elif operation == "lower":
            return text.lower()
        elif operation == "reverse":
            return text[::-1]
        return text

    def data_validator(data: dict, required_fields: list = None) -> bool:
        """Validate data against required fields."""
        if required_fields is None:
            required_fields = []
        return all(field in data for field in required_fields)

    return {
        "calculator": calculator,
        "text_processor": text_processor,
        "data_validator": data_validator
    }


@pytest.fixture
def performance_test_config():
    """Configuration for performance tests."""
    return {
        "small_dataset_size": 10,
        "medium_dataset_size": 100,
        "large_dataset_size": 1000,
        "timeout_threshold": 1.0,
        "cache_hit_speedup": 10.0  # Minimum speedup expected from cache hits
    }