# src/patterns/tool_use/validation.py

import inspect
import json
import time
from typing import Any, Dict, List, Optional, Callable, Type, get_type_hints
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass

from .registry import ToolMetadata, FrameworkType


@dataclass
class ValidationResult:
    """Result of tool validation."""
    is_valid: bool
    tool_name: str
    framework: FrameworkType
    issues: List[str]
    warnings: List[str]
    score: float  # 0.0 to 10.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for tool execution."""
    execution_time: float
    memory_usage: Optional[int] = None
    success_rate: float = 1.0
    average_response_time: float = 0.0
    error_rate: float = 0.0


class ToolValidator:
    """Comprehensive tool validation and testing framework."""

    def __init__(self):
        self.test_results: Dict[str, ValidationResult] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}

    def validate_tool(self, tool: Any, tool_name: Optional[str] = None) -> ValidationResult:
        """
        Comprehensively validate a tool.

        Args:
            tool: Tool to validate
            tool_name: Optional tool name

        Returns:
            ValidationResult with detailed analysis
        """
        if not tool_name:
            tool_name = getattr(tool, 'name', getattr(tool, '__name__', 'unknown'))

        issues = []
        warnings = []
        framework = self._detect_framework(tool)

        # Basic validation
        if not callable(tool) and not hasattr(tool, '_run'):
            issues.append("Tool is not callable and has no _run method")

        # Framework-specific validation
        if framework == FrameworkType.CREWAI:
            self._validate_crewai_tool(tool, issues, warnings)
        elif framework == FrameworkType.LANGCHAIN:
            self._validate_langchain_tool(tool, issues, warnings)
        elif framework == FrameworkType.GENERIC_FUNCTION:
            self._validate_function_tool(tool, issues, warnings)

        # Documentation validation
        self._validate_documentation(tool, warnings)

        # Parameter validation
        self._validate_parameters(tool, issues, warnings)

        # Calculate score
        score = self._calculate_score(issues, warnings)

        result = ValidationResult(
            is_valid=len(issues) == 0,
            tool_name=tool_name,
            framework=framework,
            issues=issues,
            warnings=warnings,
            score=score
        )

        self.test_results[tool_name] = result
        return result

    def _detect_framework(self, tool: Any) -> FrameworkType:
        """Detect the framework type of a tool."""
        try:
            from crewai.tools import BaseTool
            if isinstance(tool, BaseTool):
                return FrameworkType.CREWAI
        except ImportError:
            pass

        try:
            from langchain_core.tools import BaseTool
            if isinstance(tool, BaseTool):
                return FrameworkType.LANGCHAIN
        except ImportError:
            pass

        if callable(tool):
            return FrameworkType.GENERIC_FUNCTION

        return FrameworkType.GENERIC_FUNCTION

    def _validate_crewai_tool(self, tool: Any, issues: List[str], warnings: List[str]):
        """Validate CrewAI-specific requirements."""
        if not hasattr(tool, 'name') or not tool.name:
            issues.append("CrewAI tool missing required 'name' attribute")

        if not hasattr(tool, 'description') or not tool.description:
            issues.append("CrewAI tool missing required 'description' attribute")

        if not hasattr(tool, '_run'):
            issues.append("CrewAI tool missing required '_run' method")

        if hasattr(tool, 'args_schema') and tool.args_schema:
            try:
                # Try to create an instance of the schema
                if inspect.isclass(tool.args_schema):
                    schema_fields = tool.args_schema.model_fields if hasattr(tool.args_schema, 'model_fields') else {}
                    if not schema_fields:
                        warnings.append("args_schema has no defined fields")
            except Exception as e:
                issues.append(f"Invalid args_schema: {e}")
        else:
            warnings.append("No args_schema defined - parameters may not be validated")

    def _validate_langchain_tool(self, tool: Any, issues: List[str], warnings: List[str]):
        """Validate LangChain-specific requirements."""
        if not hasattr(tool, 'name') or not tool.name:
            issues.append("LangChain tool missing required 'name' attribute")

        if not hasattr(tool, 'description') or not tool.description:
            issues.append("LangChain tool missing required 'description' attribute")

        if not hasattr(tool, '_run') and not hasattr(tool, 'run'):
            issues.append("LangChain tool missing required '_run' or 'run' method")

    def _validate_function_tool(self, tool: Callable, issues: List[str], warnings: List[str]):
        """Validate generic function tools."""
        if not callable(tool):
            issues.append("Function tool is not callable")
            return

        # Check function signature
        try:
            sig = inspect.signature(tool)
            if len(sig.parameters) == 0:
                warnings.append("Function has no parameters - may be difficult for agents to use")

            # Check for type hints
            type_hints = get_type_hints(tool)
            if not type_hints:
                warnings.append("Function has no type hints - parameter types unclear")

        except Exception as e:
            warnings.append(f"Could not inspect function signature: {e}")

    def _validate_documentation(self, tool: Any, warnings: List[str]):
        """Validate tool documentation."""
        # Check for docstring
        docstring = None
        if hasattr(tool, '__doc__'):
            docstring = tool.__doc__
        elif hasattr(tool, '_run') and hasattr(tool._run, '__doc__'):
            docstring = tool._run.__doc__

        if not docstring or docstring.strip() == "":
            warnings.append("Tool lacks documentation (docstring)")
        elif len(docstring.strip()) < 20:
            warnings.append("Tool documentation is very brief")

    def _validate_parameters(self, tool: Any, issues: List[str], warnings: List[str]):
        """Validate tool parameters."""
        try:
            if hasattr(tool, '_run'):
                sig = inspect.signature(tool._run)
            else:
                sig = inspect.signature(tool)

            # Check for self parameter in _run methods
            params = list(sig.parameters.values())
            if hasattr(tool, '_run') and params and params[0].name == 'self':
                params = params[1:]  # Skip self parameter

            # Check for reasonable parameter count
            if len(params) > 10:
                warnings.append(f"Tool has many parameters ({len(params)}) - may be complex to use")

            # Check for default values
            required_params = [p for p in params if p.default == inspect.Parameter.empty]
            if len(required_params) > 5:
                warnings.append(f"Tool has many required parameters ({len(required_params)})")

        except Exception as e:
            warnings.append(f"Could not validate parameters: {e}")

    def _calculate_score(self, issues: List[str], warnings: List[str]) -> float:
        """Calculate a quality score for the tool."""
        base_score = 10.0

        # Deduct for issues (critical)
        base_score -= len(issues) * 2.0

        # Deduct for warnings (minor)
        base_score -= len(warnings) * 0.5

        return max(0.0, min(10.0, base_score))

    def performance_test(self, tool: Any, test_inputs: List[Dict[str, Any]],
                        iterations: int = 3) -> PerformanceMetrics:
        """
        Run performance tests on a tool.

        Args:
            tool: Tool to test
            test_inputs: List of input parameter sets to test
            iterations: Number of iterations per test

        Returns:
            PerformanceMetrics with detailed performance data
        """
        execution_times = []
        errors = 0
        total_tests = len(test_inputs) * iterations

        for test_input in test_inputs:
            for _ in range(iterations):
                start_time = time.time()
                try:
                    if hasattr(tool, '_run'):
                        tool._run(**test_input)
                    else:
                        tool(**test_input)

                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)

                except Exception as e:
                    errors += 1
                    print(f"Performance test error: {e}")

        # Calculate metrics
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
        else:
            avg_time = 0.0
            max_time = 0.0

        success_rate = (total_tests - errors) / total_tests if total_tests > 0 else 0.0
        error_rate = errors / total_tests if total_tests > 0 else 1.0

        metrics = PerformanceMetrics(
            execution_time=max_time,
            success_rate=success_rate,
            average_response_time=avg_time,
            error_rate=error_rate
        )

        tool_name = getattr(tool, 'name', getattr(tool, '__name__', 'unknown'))
        self.performance_metrics[tool_name] = metrics

        return metrics

    def generate_report(self, tool_name: Optional[str] = None) -> str:
        """
        Generate a comprehensive validation report.

        Args:
            tool_name: Optional specific tool name, or None for all tools

        Returns:
            Formatted validation report
        """
        if tool_name:
            if tool_name not in self.test_results:
                return f"No validation results found for tool '{tool_name}'"
            tools_to_report = {tool_name: self.test_results[tool_name]}
        else:
            tools_to_report = self.test_results

        report = []
        report.append("TOOL VALIDATION REPORT")
        report.append("=" * 50)

        for name, result in tools_to_report.items():
            report.append(f"\nTool: {name}")
            report.append(f"Framework: {result.framework.value}")
            report.append(f"Valid: {'✅' if result.is_valid else '❌'}")
            report.append(f"Score: {result.score:.1f}/10.0")

            if result.issues:
                report.append("\n🚨 Issues:")
                for issue in result.issues:
                    report.append(f"  - {issue}")

            if result.warnings:
                report.append("\n⚠️ Warnings:")
                for warning in result.warnings:
                    report.append(f"  - {warning}")

            # Add performance metrics if available
            if name in self.performance_metrics:
                metrics = self.performance_metrics[name]
                report.append("\n📊 Performance Metrics:")
                report.append(f"  - Average execution time: {metrics.average_response_time:.3f}s")
                report.append(f"  - Success rate: {metrics.success_rate:.1%}")
                report.append(f"  - Error rate: {metrics.error_rate:.1%}")

            report.append("-" * 30)

        # Summary statistics
        total_tools = len(tools_to_report)
        valid_tools = sum(1 for r in tools_to_report.values() if r.is_valid)
        avg_score = sum(r.score for r in tools_to_report.values()) / total_tools if total_tools > 0 else 0

        report.append(f"\n📈 Summary:")
        report.append(f"Total tools: {total_tools}")
        report.append(f"Valid tools: {valid_tools}")
        report.append(f"Average score: {avg_score:.1f}/10.0")

        return "\n".join(report)

    def get_recommendations(self, tool_name: str) -> List[str]:
        """
        Get improvement recommendations for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of improvement recommendations
        """
        if tool_name not in self.test_results:
            return ["Tool not found in validation results"]

        result = self.test_results[tool_name]
        recommendations = []

        # Address critical issues
        for issue in result.issues:
            if "missing required" in issue:
                recommendations.append(f"Add missing required attribute/method: {issue}")
            elif "not callable" in issue:
                recommendations.append("Ensure tool is callable or has a _run method")
            elif "Invalid args_schema" in issue:
                recommendations.append("Fix the args_schema definition using proper Pydantic models")

        # Address warnings
        for warning in result.warnings:
            if "no documentation" in warning:
                recommendations.append("Add comprehensive docstring explaining tool purpose and usage")
            elif "no type hints" in warning:
                recommendations.append("Add type hints to all function parameters")
            elif "many parameters" in warning:
                recommendations.append("Consider simplifying the tool by reducing the number of parameters")
            elif "no args_schema" in warning:
                recommendations.append("Define an args_schema using Pydantic for better parameter validation")

        # Performance recommendations
        if tool_name in self.performance_metrics:
            metrics = self.performance_metrics[tool_name]
            if metrics.average_response_time > 5.0:
                recommendations.append("Optimize tool performance - execution time is slow")
            if metrics.error_rate > 0.1:
                recommendations.append("Improve error handling - high failure rate detected")

        if not recommendations:
            recommendations.append("Tool validation passed! Consider adding more comprehensive tests.")

        return recommendations


class ToolTestSuite:
    """Test suite for comprehensive tool testing."""

    def __init__(self, validator: Optional[ToolValidator] = None):
        self.validator = validator or ToolValidator()
        self.test_cases: Dict[str, List[Dict[str, Any]]] = {}

    def add_test_case(self, tool_name: str, inputs: Dict[str, Any], expected_type: type = str):
        """
        Add a test case for a tool.

        Args:
            tool_name: Name of the tool to test
            inputs: Input parameters for the tool
            expected_type: Expected return type
        """
        if tool_name not in self.test_cases:
            self.test_cases[tool_name] = []

        self.test_cases[tool_name].append({
            'inputs': inputs,
            'expected_type': expected_type
        })

    def run_all_tests(self, tools: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Run all validation tests on provided tools.

        Args:
            tools: Dictionary of tool name to tool instance

        Returns:
            Dictionary of validation results
        """
        results = {}

        for tool_name, tool in tools.items():
            # Validation test
            validation_result = self.validator.validate_tool(tool, tool_name)
            results[tool_name] = validation_result

            # Performance test if test cases are available
            if tool_name in self.test_cases:
                test_inputs = [case['inputs'] for case in self.test_cases[tool_name]]
                self.validator.performance_test(tool, test_inputs)

        return results

    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        return self.validator.generate_report()