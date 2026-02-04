# tests/patterns/tool_use/test_integration.py

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Type, Any, Dict
from pydantic import BaseModel, Field

from src.patterns.tool_use import (
    global_tool_registry,
    register_tool,
    get_tool,
    FrameworkType,
    tool,
    robust_tool,
    ToolValidator,
    UniversalToolRegistry
)


class TestCrossFrameworkCompatibility:
    """Test cross-framework compatibility and conversion."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use a local registry to avoid test interference
        self.registry = UniversalToolRegistry()

    def test_function_to_openai_conversion(self):
        """Test converting Python function to OpenAI function format."""
        def weather_lookup(city: str, country: str = "US") -> str:
            """Get weather information for a city and country."""
            return f"Weather in {city}, {country}: Sunny, 22°C"

        # Register function
        self.registry.register_tool(weather_lookup)

        # Convert to OpenAI format
        openai_format = self.registry.get_tool("weather_lookup", FrameworkType.OPENAI_FUNCTION)

        # Verify OpenAI function structure
        assert isinstance(openai_format, dict)
        assert openai_format["name"] == "weather_lookup"
        assert "Get weather information" in openai_format["description"]
        assert "parameters" in openai_format
        assert "properties" in openai_format["parameters"]
        assert "city" in openai_format["parameters"]["properties"]
        assert "country" in openai_format["parameters"]["properties"]
        assert "city" in openai_format["parameters"]["required"]
        assert "country" not in openai_format["parameters"]["required"]  # Has default

    def test_function_to_crewai_conversion(self):
        """Test converting Python function to CrewAI tool format."""
        def text_analyzer(text: str, analysis_type: str = "sentiment") -> str:
            """Analyze text content."""
            if analysis_type == "sentiment":
                return f"Sentiment: Positive (confidence: 0.8)"
            return f"Analysis type '{analysis_type}' completed"

        # Register function
        self.registry.register_tool(text_analyzer)

        # Convert to CrewAI format
        try:
            crewai_tool = self.registry.get_tool("text_analyzer", FrameworkType.CREWAI)

            # Verify CrewAI tool structure
            assert hasattr(crewai_tool, 'name')
            assert hasattr(crewai_tool, 'description')
            assert hasattr(crewai_tool, '_run')
            assert crewai_tool.name == "text_analyzer"
            assert "Analyze text content" in crewai_tool.description

            # Test execution
            result = crewai_tool._run(text="Hello world", analysis_type="sentiment")
            assert "Sentiment: Positive" in result

        except ImportError:
            pytest.skip("CrewAI not available for conversion test")

    @patch('src.patterns.tool_use.registry.CREWAI_AVAILABLE', True)
    def test_mock_crewai_tool_registration(self):
        """Test registering and converting mock CrewAI tools."""
        # Create mock CrewAI tool
        class MockToolInput(BaseModel):
            query: str = Field(..., description="Search query")
            limit: int = Field(default=10, description="Result limit")

        mock_tool = Mock()
        mock_tool.name = "mock_search_tool"
        mock_tool.description = "Mock search tool for testing"
        mock_tool.args_schema = MockToolInput
        mock_tool._run = Mock(return_value="Mock search results")

        # Mock the CrewAI validation
        with patch.object(self.registry.adapters[FrameworkType.CREWAI], 'validate_tool', return_value=True):
            # Register the mock tool
            tool_name = self.registry.register_tool(mock_tool)
            assert tool_name == "mock_search_tool"

            # Verify metadata extraction
            metadata = self.registry.metadata[tool_name]
            assert metadata.framework == FrameworkType.CREWAI
            assert metadata.name == "mock_search_tool"

            # Test conversion to OpenAI format
            openai_format = self.registry.get_tool(tool_name, FrameworkType.OPENAI_FUNCTION)
            assert openai_format["name"] == "mock_search_tool"
            assert "query" in openai_format["parameters"]["properties"]

    def test_bulk_framework_export(self):
        """Test bulk export of tools for specific framework."""
        # Register multiple tools
        def calculator(expr: str) -> str:
            return str(eval(expr))

        def formatter(text: str, style: str = "upper") -> str:
            return text.upper() if style == "upper" else text.lower()

        self.registry.register_tool(calculator, category="math")
        self.registry.register_tool(formatter, category="text")

        # Export all tools as OpenAI functions
        openai_tools = self.registry.export_for_framework(FrameworkType.OPENAI_FUNCTION)
        assert len(openai_tools) == 2

        tool_names = [tool["name"] for tool in openai_tools]
        assert "calculator" in tool_names
        assert "formatter" in tool_names

        # Export tools by category
        math_tools = self.registry.export_for_framework(FrameworkType.OPENAI_FUNCTION, category="math")
        assert len(math_tools) == 1
        assert math_tools[0]["name"] == "calculator"

    def test_framework_detection_accuracy(self):
        """Test that framework detection works correctly."""
        # Test function detection
        def regular_func() -> str:
            return "regular"

        adapter = self.registry._detect_adapter(regular_func)
        assert adapter is not None
        assert adapter.validate_tool(regular_func)

        # Test with mock CrewAI tool
        mock_crewai = Mock()
        mock_crewai.name = "mock"
        mock_crewai._run = Mock()

        # Should not detect as CrewAI without proper imports
        adapter = self.registry._detect_adapter(mock_crewai)
        # Falls back to function adapter
        assert adapter is not None


class TestDecoratorIntegration:
    """Test integration between decorators and registry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing registrations
        global_tool_registry.tools.clear()
        global_tool_registry.metadata.clear()

    def test_auto_registration_workflow(self):
        """Test automatic registration with decorators."""
        @tool(name="auto_registered", category="test", tags=["integration"])
        def auto_func(value: int) -> str:
            """Automatically registered function."""
            return f"Value: {value}"

        # Should be automatically registered
        assert "auto_registered" in global_tool_registry.tools

        # Test retrieval and conversion
        retrieved = get_tool("auto_registered")
        assert retrieved == auto_func

        # Test OpenAI conversion
        openai_format = get_tool("auto_registered", FrameworkType.OPENAI_FUNCTION)
        assert openai_format["name"] == "auto_registered"

    def test_robust_tool_with_validation(self):
        """Test robust tool decorator with validation."""
        @robust_tool(retries=2, cache=True, category="robust")
        def flaky_service(data: str, fail_first: bool = False) -> str:
            """Service that might fail on first attempt."""
            if fail_first:
                # Simulate failure on first call
                if not hasattr(flaky_service, '_called'):
                    flaky_service._called = True
                    raise ValueError("First attempt fails")
            return f"Processed: {data}"

        # Test execution with failure and recovery
        result = flaky_service("test_data", fail_first=True)
        assert result == "Processed: test_data"

        # Validate the tool
        validator = ToolValidator()
        validation_result = validator.validate_tool(flaky_service, "flaky_service")
        assert validation_result.is_valid

    def test_decorator_configuration_preservation(self):
        """Test that decorator configuration is preserved through conversions."""
        @tool(
            name="configured_tool",
            description="Specially configured tool",
            category="config",
            retry_attempts=5,
            cache=True,
            timeout=30.0
        )
        def configured_func(input_data: str) -> str:
            """Function with detailed configuration."""
            return f"Configured: {input_data}"

        # Check configuration preservation
        config = configured_func.tool_config
        assert config.name == "configured_tool"
        assert config.retry_attempts == 5
        assert config.cache is True
        assert config.timeout == 30.0

        # Test that conversion maintains metadata
        openai_format = get_tool("configured_tool", FrameworkType.OPENAI_FUNCTION)
        assert openai_format["description"] == "Specially configured tool"


class TestValidationIntegration:
    """Test integration between validation and other components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ToolValidator()
        self.registry = UniversalToolRegistry()

    def test_end_to_end_quality_assurance(self):
        """Test complete quality assurance workflow."""
        # Define tools with varying quality
        @tool(name="high_quality_tool", category="quality")
        def excellent_tool(query: str, options: Dict[str, Any] = None) -> str:
            """
            High-quality tool with comprehensive documentation.

            This tool demonstrates best practices for tool development:
            - Clear, detailed documentation
            - Proper type hints
            - Sensible parameter structure
            - Good error handling

            Args:
                query: The search query to process
                options: Optional configuration parameters

            Returns:
                Formatted search results

            Raises:
                ValueError: If query is empty or invalid
            """
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")

            if options is None:
                options = {}

            return f"Results for '{query}' with options {options}"

        def poor_tool(x, y, z, a, b, c):
            # No docstring, no type hints, too many parameters
            return str(x) + str(y) + str(z) + str(a) + str(b) + str(c)

        # Register tools
        self.registry.register_tool(excellent_tool)
        self.registry.register_tool(poor_tool, name="poor_tool")

        # Validate both tools
        excellent_result = self.validator.validate_tool(excellent_tool, "excellent_tool")
        poor_result = self.validator.validate_tool(poor_tool, "poor_tool")

        # Excellent tool should score very highly
        assert excellent_result.is_valid
        assert excellent_result.score >= 9.0
        assert len(excellent_result.issues) == 0

        # Poor tool should have issues but still be valid (it's callable)
        assert poor_result.is_valid  # Still callable
        assert poor_result.score < 7.0
        assert len(poor_result.warnings) > 0

        # Get improvement recommendations
        excellent_recommendations = self.validator.get_recommendations("excellent_tool")
        poor_recommendations = self.validator.get_recommendations("poor_tool")

        # Excellent tool should need minimal improvements
        assert len(excellent_recommendations) <= 2

        # Poor tool should have many recommendations
        assert len(poor_recommendations) >= 3

    def test_performance_validation_integration(self):
        """Test integration of performance testing with validation."""
        @tool(name="performance_test_tool")
        def performance_tool(complexity: int = 1) -> str:
            """Tool for performance testing."""
            # Simulate work based on complexity
            import time
            time.sleep(complexity * 0.01)  # Small delay for testing
            return f"Completed work with complexity {complexity}"

        # Register and validate
        self.registry.register_tool(performance_tool)
        validation_result = self.validator.validate_tool(performance_tool, "performance_tool")

        # Run performance tests
        test_inputs = [
            {"complexity": 1},
            {"complexity": 2},
            {"complexity": 1}  # Repeat to test consistency
        ]

        performance_metrics = self.validator.performance_test(
            performance_tool,
            test_inputs,
            iterations=2
        )

        # Verify performance metrics
        assert performance_metrics.success_rate == 1.0
        assert performance_metrics.error_rate == 0.0
        assert performance_metrics.average_response_time > 0.01  # Should measure delay

        # Generate comprehensive report
        report = self.validator.generate_report("performance_tool")
        assert "Performance Metrics" in report
        assert "execution time" in report


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_api_tool_development_workflow(self):
        """Test typical API tool development workflow."""
        # Step 1: Define API tool with proper structure
        @robust_tool(
            retries=3,
            timeout=10.0,
            cache=True,
            category="api",
            tags=["external", "weather"]
        )
        def weather_api_tool(city: str, units: str = "metric") -> str:
            """
            Fetch weather data for a specified city.

            Args:
                city: Name of the city to get weather for
                units: Temperature units ('metric', 'imperial', 'kelvin')

            Returns:
                Weather information as formatted string

            Raises:
                ValueError: If city name is invalid
                TimeoutError: If API request times out
            """
            # Simulate API call with potential failure
            if city.lower() == "invalid":
                raise ValueError("Invalid city name")

            # Simulate successful API response
            temp = 22 if units == "metric" else 72
            unit_symbol = "°C" if units == "metric" else "°F"

            return f"Weather in {city}: {temp}{unit_symbol}, Sunny"

        # Step 2: Validate the tool
        validator = ToolValidator()
        validation_result = validator.validate_tool(weather_api_tool, "weather_api_tool")

        assert validation_result.is_valid
        assert validation_result.score >= 8.0  # Should be high quality

        # Step 3: Performance test
        test_scenarios = [
            {"city": "London", "units": "metric"},
            {"city": "New York", "units": "imperial"},
            {"city": "Tokyo"},  # Test default parameter
        ]

        metrics = validator.performance_test(weather_api_tool, test_scenarios)
        assert metrics.success_rate == 1.0

        # Step 4: Test error handling
        error_scenarios = [{"city": "invalid"}]
        error_metrics = validator.performance_test(weather_api_tool, error_scenarios)
        assert error_metrics.error_rate == 1.0  # Should fail as expected

        # Step 5: Convert to different frameworks
        registry = UniversalToolRegistry()
        registry.register_tool(weather_api_tool)

        openai_format = registry.get_tool("weather_api_tool", FrameworkType.OPENAI_FUNCTION)
        assert "city" in openai_format["parameters"]["properties"]
        assert "units" in openai_format["parameters"]["properties"]

    def test_multi_tool_ecosystem(self):
        """Test managing a complete ecosystem of tools."""
        # Create a suite of related tools
        tools = {}

        @tool(category="text", tags=["nlp"])
        def text_cleaner(text: str) -> str:
            """Clean and normalize text."""
            return text.strip().lower()

        @tool(category="text", tags=["nlp", "analysis"])
        def sentiment_analyzer(text: str) -> str:
            """Analyze sentiment of text."""
            positive_words = ["good", "great", "excellent", "amazing"]
            negative_words = ["bad", "terrible", "awful", "horrible"]

            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if pos_count > neg_count:
                return "Positive"
            elif neg_count > pos_count:
                return "Negative"
            return "Neutral"

        @tool(category="data", tags=["processing"])
        def data_formatter(data: Any, format_type: str = "json") -> str:
            """Format data in specified format."""
            if format_type == "json":
                return json.dumps(data, indent=2)
            elif format_type == "csv":
                return f"data,{data}"  # Simple CSV
            return str(data)

        tools = {
            "text_cleaner": text_cleaner,
            "sentiment_analyzer": sentiment_analyzer,
            "data_formatter": data_formatter
        }

        # Validate entire ecosystem
        validator = ToolValidator()
        validation_results = {}

        for name, tool_func in tools.items():
            result = validator.validate_tool(tool_func, name)
            validation_results[name] = result

        # All tools should be valid
        assert all(result.is_valid for result in validation_results.values())

        # Generate ecosystem report
        report = validator.generate_report()
        assert "Summary:" in report
        assert "Total tools: 3" in report

        # Test tool interactions (using one tool's output as another's input)
        cleaned_text = text_cleaner("  Great Product! Amazing Quality!  ")
        sentiment = sentiment_analyzer(cleaned_text)
        formatted_result = data_formatter({"text": cleaned_text, "sentiment": sentiment})

        assert "great product! amazing quality!" in cleaned_text
        assert sentiment == "Positive"
        assert "Positive" in formatted_result


if __name__ == "__main__":
    pytest.main([__file__])