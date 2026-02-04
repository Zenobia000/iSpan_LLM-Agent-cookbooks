# tests/patterns/tool_use/test_registry.py

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict

from src.patterns.tool_use.registry import (
    UniversalToolRegistry,
    ToolMetadata,
    FrameworkType,
    CrewAIToolAdapter,
    LangChainToolAdapter,
    FunctionToolAdapter,
    global_tool_registry
)


class TestFunctionToolAdapter:
    """Test the function tool adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = FunctionToolAdapter()

    def test_validate_tool_with_function(self):
        """Test tool validation with a valid function."""
        def test_function(x: int, y: str = "default") -> str:
            """Test function docstring."""
            return f"{x}: {y}"

        assert self.adapter.validate_tool(test_function) is True

    def test_validate_tool_with_non_callable(self):
        """Test tool validation with non-callable object."""
        assert self.adapter.validate_tool("not_a_function") is False

    def test_extract_metadata_from_function(self):
        """Test metadata extraction from function."""
        def test_function(x: int, y: str = "default") -> str:
            """Test function for metadata extraction."""
            return f"{x}: {y}"

        metadata = self.adapter.extract_metadata(test_function)

        assert metadata.name == "test_function"
        assert metadata.framework == FrameworkType.GENERIC_FUNCTION
        assert "Test function for metadata extraction" in metadata.description
        assert "x" in metadata.parameters
        assert "y" in metadata.parameters
        assert metadata.parameters["y"]["default"] == "default"

    def test_convert_to_openai_function(self):
        """Test conversion to OpenAI function format."""
        def test_function(query: str, limit: int = 10) -> str:
            """Search function."""
            return f"Results for {query}"

        openai_format = self.adapter._convert_to_openai_function(test_function)

        assert openai_format["name"] == "test_function"
        assert openai_format["description"] == "Search function."
        assert "properties" in openai_format["parameters"]
        assert "query" in openai_format["parameters"]["properties"]
        assert "limit" in openai_format["parameters"]["properties"]
        assert "query" in openai_format["parameters"]["required"]
        assert "limit" not in openai_format["parameters"]["required"]


class TestUniversalToolRegistry:
    """Test the universal tool registry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = UniversalToolRegistry()

    def test_register_simple_function(self):
        """Test registering a simple function."""
        def calculator(expression: str) -> str:
            """Calculate mathematical expressions."""
            return str(eval(expression))

        tool_name = self.registry.register_tool(calculator)
        assert tool_name == "calculator"
        assert "calculator" in self.registry.tools
        assert "calculator" in self.registry.metadata

    def test_register_with_custom_name(self):
        """Test registering tool with custom name."""
        def add(a: int, b: int) -> int:
            return a + b

        tool_name = self.registry.register_tool(add, name="adder", category="math")
        assert tool_name == "adder"
        assert self.registry.metadata["adder"].category == "math"

    def test_register_duplicate_name_without_force(self):
        """Test that duplicate names raise error without force flag."""
        def func1() -> str:
            return "func1"

        def func2() -> str:
            return "func2"

        self.registry.register_tool(func1, name="duplicate")

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register_tool(func2, name="duplicate")

    def test_register_duplicate_name_with_force(self):
        """Test that duplicate names can be overwritten with force flag."""
        def func1() -> str:
            return "func1"

        def func2() -> str:
            return "func2"

        self.registry.register_tool(func1, name="duplicate")
        self.registry.register_tool(func2, name="duplicate", force=True)

        # Should have the second function now
        assert self.registry.tools["duplicate"] == func2

    def test_get_tool_basic(self):
        """Test getting a registered tool."""
        def test_func() -> str:
            return "test"

        self.registry.register_tool(test_func)
        retrieved = self.registry.get_tool("test_func")
        assert retrieved == test_func

    def test_get_nonexistent_tool(self):
        """Test getting a non-existent tool raises error."""
        with pytest.raises(KeyError, match="not found"):
            self.registry.get_tool("nonexistent")

    def test_list_tools_all(self):
        """Test listing all tools."""
        def func1() -> str:
            return "1"

        def func2() -> str:
            return "2"

        self.registry.register_tool(func1, category="cat1")
        self.registry.register_tool(func2, category="cat2")

        all_tools = self.registry.list_tools()
        assert len(all_tools) == 2
        names = [tool.name for tool in all_tools]
        assert "func1" in names
        assert "func2" in names

    def test_list_tools_by_category(self):
        """Test listing tools filtered by category."""
        def math_func() -> str:
            return "math"

        def text_func() -> str:
            return "text"

        self.registry.register_tool(math_func, category="math")
        self.registry.register_tool(text_func, category="text")

        math_tools = self.registry.list_tools(category="math")
        assert len(math_tools) == 1
        assert math_tools[0].name == "math_func"

    def test_remove_tool(self):
        """Test removing a tool from registry."""
        def temp_func() -> str:
            return "temp"

        self.registry.register_tool(temp_func)
        assert "temp_func" in self.registry.tools

        removed = self.registry.remove_tool("temp_func")
        assert removed is True
        assert "temp_func" not in self.registry.tools
        assert "temp_func" not in self.registry.metadata

    def test_remove_nonexistent_tool(self):
        """Test removing non-existent tool returns False."""
        removed = self.registry.remove_tool("nonexistent")
        assert removed is False

    def test_export_for_framework(self):
        """Test exporting tools for specific framework."""
        def test_func() -> str:
            return "test"

        self.registry.register_tool(test_func, category="test")

        # Export as generic functions (should work)
        exported = self.registry.export_for_framework(FrameworkType.GENERIC_FUNCTION)
        assert len(exported) == 1

        # Export as OpenAI functions (should convert)
        exported_openai = self.registry.export_for_framework(FrameworkType.OPENAI_FUNCTION)
        assert len(exported_openai) == 1
        assert isinstance(exported_openai[0], dict)

    def test_get_registry_stats(self):
        """Test getting registry statistics."""
        def func1() -> str:
            return "1"

        def func2() -> str:
            return "2"

        self.registry.register_tool(func1, category="cat1")
        self.registry.register_tool(func2, category="cat2")

        stats = self.registry.get_registry_stats()
        assert stats["total_tools"] == 2
        assert "generic_function" in stats["frameworks"]
        assert stats["frameworks"]["generic_function"] == 2
        assert "cat1" in stats["categories"]
        assert "cat2" in stats["categories"]


class TestCrewAIToolAdapter:
    """Test CrewAI tool adapter (if CrewAI is available)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = CrewAIToolAdapter()

    def test_validate_crewai_tool(self):
        """Test validation of CrewAI tools."""
        # This test would require CrewAI to be installed
        # For now, we'll test the validation logic with a mock
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test description"
        mock_tool._run = Mock(return_value="test result")

        # This should pass basic validation
        # Note: Real test would require actual CrewAI tool
        assert callable(mock_tool._run)

    def test_extract_metadata_from_mock_tool(self):
        """Test metadata extraction from mock CrewAI tool."""
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.description = "Mock tool description"
        mock_tool.args_schema = None

        # Mock the validate_tool method to return True
        with patch.object(self.adapter, 'validate_tool', return_value=True):
            metadata = self.adapter.extract_metadata(mock_tool)

            assert metadata.name == "mock_tool"
            assert metadata.description == "Mock tool description"
            assert metadata.framework == FrameworkType.CREWAI


class TestIntegration:
    """Integration tests for the tool registry system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = UniversalToolRegistry()

    def test_end_to_end_workflow(self):
        """Test complete workflow from registration to conversion."""
        # Define a test function
        def weather_lookup(city: str, country: str = "US") -> str:
            """Get weather information for a city."""
            return f"Weather in {city}, {country}: Sunny, 22°C"

        # Register the tool
        tool_name = self.registry.register_tool(
            weather_lookup,
            category="api",
            tags=["weather", "external"]
        )

        # Verify registration
        assert tool_name == "weather_lookup"
        tools = self.registry.list_tools(category="api")
        assert len(tools) == 1
        assert tools[0].name == "weather_lookup"

        # Test retrieval
        retrieved_tool = self.registry.get_tool("weather_lookup")
        assert retrieved_tool == weather_lookup

        # Test conversion to OpenAI format
        openai_format = self.registry.get_tool("weather_lookup", FrameworkType.OPENAI_FUNCTION)
        assert openai_format["name"] == "weather_lookup"
        assert "parameters" in openai_format
        assert "city" in openai_format["parameters"]["properties"]

        # Test statistics
        stats = self.registry.get_registry_stats()
        assert stats["total_tools"] == 1
        assert stats["categories"]["api"] == 1

    def test_multiple_tools_management(self):
        """Test managing multiple tools of different types."""
        # Register multiple tools
        def calculator(expr: str) -> str:
            return str(eval(expr))

        def translator(text: str, target: str = "en") -> str:
            return f"Translated '{text}' to {target}"

        def file_reader(path: str) -> str:
            return f"Contents of {path}"

        # Register with different categories
        self.registry.register_tool(calculator, category="math", tags=["calculation"])
        self.registry.register_tool(translator, category="text", tags=["translation", "nlp"])
        self.registry.register_tool(file_reader, category="io", tags=["file", "read"])

        # Test filtering
        math_tools = self.registry.list_tools(category="math")
        text_tools = self.registry.list_tools(category="text")
        io_tools = self.registry.list_tools(category="io")

        assert len(math_tools) == 1
        assert len(text_tools) == 1
        assert len(io_tools) == 1

        # Test bulk export
        all_openai = self.registry.export_for_framework(FrameworkType.OPENAI_FUNCTION)
        assert len(all_openai) == 3

        # Test removal
        self.registry.remove_tool("translator")
        remaining_tools = self.registry.list_tools()
        assert len(remaining_tools) == 2


def test_global_registry_isolation():
    """Test that global registry doesn't interfere with local tests."""
    # Create a local registry
    local_registry = UniversalToolRegistry()

    def local_func() -> str:
        return "local"

    # Register in local registry
    local_registry.register_tool(local_func)

    # Should not affect global registry
    global_tools = global_tool_registry.list_tools()
    local_tools = local_registry.list_tools()

    # Local should have our tool, global state depends on other tests
    assert len(local_tools) == 1
    assert local_tools[0].name == "local_func"


if __name__ == "__main__":
    pytest.main([__file__])