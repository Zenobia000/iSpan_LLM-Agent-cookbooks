# tests/patterns/tool_use/test_validation.py

import pytest
import time
from unittest.mock import Mock, patch
from typing import Type
from pydantic import BaseModel, Field

from src.patterns.tool_use.validation import (
    ToolValidator,
    ToolTestSuite,
    ValidationResult,
    PerformanceMetrics,
    FrameworkType
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating validation results."""
        result = ValidationResult(
            is_valid=True,
            tool_name="test_tool",
            framework=FrameworkType.GENERIC_FUNCTION,
            issues=[],
            warnings=["Minor warning"],
            score=8.5
        )

        assert result.is_valid is True
        assert result.tool_name == "test_tool"
        assert result.framework == FrameworkType.GENERIC_FUNCTION
        assert len(result.issues) == 0
        assert len(result.warnings) == 1
        assert result.score == 8.5


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            execution_time=0.25,
            memory_usage=1024,
            success_rate=0.95,
            average_response_time=0.15,
            error_rate=0.05
        )

        assert metrics.execution_time == 0.25
        assert metrics.memory_usage == 1024
        assert metrics.success_rate == 0.95
        assert metrics.average_response_time == 0.15
        assert metrics.error_rate == 0.05


class TestToolValidator:
    """Test the ToolValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ToolValidator()

    def test_validate_simple_function(self):
        """Test validation of a simple function."""
        def simple_func(x: int, y: str = "default") -> str:
            """A simple test function with type hints."""
            return f"{x}: {y}"

        result = self.validator.validate_tool(simple_func, "simple_func")

        assert result.is_valid is True
        assert result.tool_name == "simple_func"
        assert result.framework == FrameworkType.GENERIC_FUNCTION
        assert len(result.issues) == 0
        assert result.score > 7.0  # Should have decent score

    def test_validate_function_without_docstring(self):
        """Test validation of function without docstring."""
        def no_doc_func(x: int) -> int:
            return x * 2

        result = self.validator.validate_tool(no_doc_func)

        assert result.is_valid is True  # Still valid, just warnings
        assert any("documentation" in warning.lower() for warning in result.warnings)
        assert result.score < 10.0  # Should lose points for missing docs

    def test_validate_function_without_type_hints(self):
        """Test validation of function without type hints."""
        def no_hints_func(x, y=None):
            """Function without type hints."""
            return str(x) + str(y or "")

        result = self.validator.validate_tool(no_hints_func)

        assert result.is_valid is True
        assert any("type hints" in warning.lower() for warning in result.warnings)

    def test_validate_function_with_many_parameters(self):
        """Test validation of function with many parameters."""
        def many_params_func(a, b, c, d, e, f, g, h, i, j, k) -> str:
            """Function with many parameters."""
            return "many params"

        result = self.validator.validate_tool(many_params_func)

        assert result.is_valid is True
        assert any("many parameters" in warning.lower() for warning in result.warnings)

    def test_validate_non_callable_object(self):
        """Test validation of non-callable object."""
        non_callable = "this is not a function"

        result = self.validator.validate_tool(non_callable)

        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("not callable" in issue.lower() for issue in result.issues)
        assert result.score < 5.0

    def test_validate_mock_crewai_tool(self):
        """Test validation of mock CrewAI tool."""
        # Create a mock that looks like a CrewAI tool
        mock_tool = Mock()
        mock_tool.name = "mock_crewai_tool"
        mock_tool.description = "A mock CrewAI tool for testing"
        mock_tool._run = Mock(return_value="mock result")

        # Mock args_schema
        class MockSchema(BaseModel):
            query: str = Field(..., description="Search query")

        mock_tool.args_schema = MockSchema

        # Mock the framework detection to return CrewAI
        with patch.object(self.validator, '_detect_framework', return_value=FrameworkType.CREWAI):
            result = self.validator.validate_tool(mock_tool)

            assert result.framework == FrameworkType.CREWAI
            # Should pass basic validation for a properly structured mock

    def test_validate_crewai_tool_missing_attributes(self):
        """Test validation of CrewAI tool missing required attributes."""
        mock_tool = Mock()
        # Deliberately omit required attributes
        mock_tool.name = None
        mock_tool.description = ""
        delattr(mock_tool, '_run')

        with patch.object(self.validator, '_detect_framework', return_value=FrameworkType.CREWAI):
            result = self.validator.validate_tool(mock_tool)

            assert result.is_valid is False
            assert len(result.issues) >= 2  # Missing name, description, and _run
            assert result.score < 5.0

    def test_calculate_score_with_issues_and_warnings(self):
        """Test score calculation with various issues and warnings."""
        issues = ["Critical issue 1", "Critical issue 2"]
        warnings = ["Warning 1", "Warning 2", "Warning 3"]

        score = self.validator._calculate_score(issues, warnings)

        # Base score 10.0 - (2 issues * 2.0) - (3 warnings * 0.5) = 4.5
        assert score == 4.5

    def test_calculate_score_minimum_zero(self):
        """Test that score doesn't go below zero."""
        many_issues = ["Issue"] * 10  # Would result in negative score

        score = self.validator._calculate_score(many_issues, [])

        assert score >= 0.0

    def test_get_recommendations_for_issues(self):
        """Test recommendation generation for common issues."""
        # Create a tool with known issues
        def poor_tool():
            # No docstring, no type hints, no args_schema
            pass

        # Validate to populate test_results
        self.validator.validate_tool(poor_tool, "poor_tool")

        recommendations = self.validator.get_recommendations("poor_tool")

        assert len(recommendations) > 0
        # Should contain specific recommendations based on the validation issues/warnings

    def test_get_recommendations_for_unknown_tool(self):
        """Test recommendations for tool not in results."""
        recommendations = self.validator.get_recommendations("unknown_tool")

        assert len(recommendations) == 1
        assert "not found" in recommendations[0]

    def test_performance_test_successful_execution(self):
        """Test performance testing with successful executions."""
        def fast_func(value: int) -> int:
            return value * 2

        test_inputs = [{"value": 1}, {"value": 2}, {"value": 3}]

        metrics = self.validator.performance_test(fast_func, test_inputs, iterations=2)

        assert metrics.success_rate == 1.0  # All should succeed
        assert metrics.error_rate == 0.0
        assert metrics.average_response_time >= 0.0
        assert len(self.validator.performance_metrics) == 1

    def test_performance_test_with_failures(self):
        """Test performance testing with some failures."""
        def flaky_func(value: int) -> int:
            if value == 2:
                raise ValueError("Deliberate failure")
            return value * 2

        test_inputs = [{"value": 1}, {"value": 2}, {"value": 3}]

        metrics = self.validator.performance_test(flaky_func, test_inputs, iterations=1)

        assert metrics.success_rate < 1.0  # Some should fail
        assert metrics.error_rate > 0.0

    def test_performance_test_with_slow_function(self):
        """Test performance testing with slow function."""
        def slow_func(delay: float) -> str:
            time.sleep(delay)
            return "done"

        test_inputs = [{"delay": 0.01}, {"delay": 0.01}]  # Small delays for testing

        metrics = self.validator.performance_test(slow_func, test_inputs, iterations=1)

        assert metrics.average_response_time > 0.01  # Should measure the delay
        assert metrics.success_rate == 1.0

    def test_generate_report_single_tool(self):
        """Test generating validation report for single tool."""
        def test_func(x: int) -> str:
            """Test function for reporting."""
            return str(x)

        self.validator.validate_tool(test_func, "test_func")

        report = self.validator.generate_report("test_func")

        assert "TOOL VALIDATION REPORT" in report
        assert "test_func" in report
        assert "Valid:" in report
        assert "Score:" in report

    def test_generate_report_all_tools(self):
        """Test generating validation report for all tools."""
        def func1(x: int) -> str:
            return str(x)

        def func2(y: str) -> int:
            return len(y)

        self.validator.validate_tool(func1, "func1")
        self.validator.validate_tool(func2, "func2")

        report = self.validator.generate_report()

        assert "func1" in report
        assert "func2" in report
        assert "Summary:" in report
        assert "Total tools:" in report

    def test_generate_report_nonexistent_tool(self):
        """Test report generation for non-existent tool."""
        report = self.validator.generate_report("nonexistent")

        assert "No validation results found" in report


class TestToolTestSuite:
    """Test the ToolTestSuite class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_suite = ToolTestSuite()

    def test_add_test_case(self):
        """Test adding test cases to the suite."""
        inputs = {"x": 5, "y": "test"}

        self.test_suite.add_test_case("test_tool", inputs, str)

        assert "test_tool" in self.test_suite.test_cases
        assert len(self.test_suite.test_cases["test_tool"]) == 1
        assert self.test_suite.test_cases["test_tool"][0]["inputs"] == inputs
        assert self.test_suite.test_cases["test_tool"][0]["expected_type"] == str

    def test_add_multiple_test_cases(self):
        """Test adding multiple test cases for same tool."""
        self.test_suite.add_test_case("tool", {"a": 1})
        self.test_suite.add_test_case("tool", {"a": 2})
        self.test_suite.add_test_case("tool", {"a": 3})

        assert len(self.test_suite.test_cases["tool"]) == 3

    def test_run_all_tests_with_valid_tools(self):
        """Test running all tests with valid tools."""
        def calculator(x: int, y: int) -> int:
            """Simple calculator."""
            return x + y

        def formatter(text: str, prefix: str = ">>") -> str:
            """Text formatter."""
            return f"{prefix} {text}"

        # Add test cases
        self.test_suite.add_test_case("calculator", {"x": 2, "y": 3})
        self.test_suite.add_test_case("formatter", {"text": "hello"})

        tools = {
            "calculator": calculator,
            "formatter": formatter
        }

        results = self.test_suite.run_all_tests(tools)

        assert len(results) == 2
        assert "calculator" in results
        assert "formatter" in results

        # Both should be valid
        assert results["calculator"].is_valid
        assert results["formatter"].is_valid

    def test_run_all_tests_with_performance_data(self):
        """Test that performance tests are run when test cases exist."""
        def perf_func(value: int) -> int:
            return value * 2

        # Add test case
        self.test_suite.add_test_case("perf_func", {"value": 5})

        tools = {"perf_func": perf_func}
        results = self.test_suite.run_all_tests(tools)

        # Should have both validation and performance data
        assert "perf_func" in results
        assert "perf_func" in self.test_suite.validator.performance_metrics

    def test_generate_test_report(self):
        """Test generating comprehensive test report."""
        def simple_func(x: int) -> str:
            """Simple function."""
            return str(x)

        # Add test case and run tests
        self.test_suite.add_test_case("simple_func", {"x": 42})
        tools = {"simple_func": simple_func}
        self.test_suite.run_all_tests(tools)

        # Generate report
        report = self.test_suite.generate_test_report()

        assert isinstance(report, str)
        assert "TOOL VALIDATION REPORT" in report
        assert "simple_func" in report


class TestFrameworkDetection:
    """Test framework detection logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ToolValidator()

    def test_detect_generic_function(self):
        """Test detection of generic Python functions."""
        def regular_function() -> str:
            return "regular"

        framework = self.validator._detect_framework(regular_function)
        assert framework == FrameworkType.GENERIC_FUNCTION

    def test_detect_non_callable(self):
        """Test detection of non-callable objects."""
        non_callable = "not a function"

        framework = self.validator._detect_framework(non_callable)
        # Should still return generic function as fallback
        assert framework == FrameworkType.GENERIC_FUNCTION

    @patch('src.patterns.tool_use.validation.CREWAI_AVAILABLE', True)
    def test_detect_mock_crewai_tool(self):
        """Test detection of mock CrewAI tools."""
        # This test would require actual CrewAI import
        # For now, we test the framework detection logic
        mock_tool = Mock()

        # Mock the isinstance check
        with patch('builtins.isinstance', return_value=True):
            framework = self.validator._detect_framework(mock_tool)
            # The actual result depends on the mocking setup


class TestIntegrationValidation:
    """Integration tests for validation workflow."""

    def test_complete_validation_workflow(self):
        """Test complete validation workflow from tool to recommendations."""
        def example_tool(query: str, limit: int = 10) -> str:
            """
            Search for information with optional limit.

            Args:
                query: Search query string
                limit: Maximum number of results

            Returns:
                Formatted search results
            """
            return f"Found {limit} results for '{query}'"

        # Create validator and test suite
        validator = ToolValidator()
        test_suite = ToolTestSuite(validator)

        # Add test cases
        test_suite.add_test_case("example_tool", {"query": "test", "limit": 5})
        test_suite.add_test_case("example_tool", {"query": "another", "limit": 3})

        # Run validation and performance tests
        tools = {"example_tool": example_tool}
        results = test_suite.run_all_tests(tools)

        # Verify results
        assert len(results) == 1
        assert results["example_tool"].is_valid
        assert results["example_tool"].score > 8.0  # Should have high score

        # Check performance metrics
        assert "example_tool" in validator.performance_metrics
        metrics = validator.performance_metrics["example_tool"]
        assert metrics.success_rate == 1.0

        # Get recommendations
        recommendations = validator.get_recommendations("example_tool")
        assert len(recommendations) >= 1

        # Generate comprehensive report
        report = test_suite.generate_test_report()
        assert "example_tool" in report
        assert "Performance Metrics" in report


if __name__ == "__main__":
    pytest.main([__file__])