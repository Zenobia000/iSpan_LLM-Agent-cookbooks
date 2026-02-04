#!/usr/bin/env python3
# tests/patterns/tool_use/test_runner.py

"""
Comprehensive test runner for the Universal Tool Framework.

This script provides various testing modes and configurations for the tool_use module.
"""

import sys
import pytest
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def run_basic_tests():
    """Run basic unit tests."""
    print("Running basic unit tests...")
    test_args = [
        str(Path(__file__).parent),
        "-v",
        "--tb=short",
        "-k", "not performance and not integration"
    ]
    return pytest.main(test_args)


def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    test_args = [
        str(Path(__file__).parent / "test_integration.py"),
        "-v",
        "--tb=short"
    ]
    return pytest.main(test_args)


def run_performance_tests():
    """Run performance benchmarks."""
    print("Running performance benchmarks...")
    test_args = [
        str(Path(__file__).parent / "test_performance.py"),
        "-v",
        "--tb=short",
        "-s"  # Show output for performance results
    ]
    return pytest.main(test_args)


def run_all_tests():
    """Run complete test suite."""
    print("Running complete test suite...")
    test_args = [
        str(Path(__file__).parent),
        "-v",
        "--tb=short",
        "--durations=10"  # Show 10 slowest tests
    ]
    return pytest.main(test_args)


def run_coverage_tests():
    """Run tests with coverage reporting."""
    print("Running tests with coverage...")
    try:
        import pytest_cov
    except ImportError:
        print("pytest-cov not available. Install with: pip install pytest-cov")
        return 1

    test_args = [
        str(Path(__file__).parent),
        "--cov=src.patterns.tool_use",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]
    return pytest.main(test_args)


def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality."""
    print("Running quick smoke test...")

    try:
        # Test basic imports
        from src.patterns.tool_use import (
            tool, register_tool, get_tool, FrameworkType,
            ToolValidator, UniversalToolRegistry
        )
        print("✓ Imports successful")

        # Test basic tool creation
        @tool(name="smoke_test_tool")
        def smoke_test_func(x: int) -> str:
            return f"Result: {x}"

        result = smoke_test_func(42)
        assert result == "Result: 42"
        print("✓ Basic tool creation and execution")

        # Test registry
        registry = UniversalToolRegistry()
        registry.register_tool(smoke_test_func, "smoke_tool")
        retrieved = registry.get_tool("smoke_tool")
        assert retrieved == smoke_test_func
        print("✓ Registry operations")

        # Test validation
        validator = ToolValidator()
        validation_result = validator.validate_tool(smoke_test_func)
        assert validation_result.is_valid
        print("✓ Tool validation")

        # Test conversion
        openai_format = registry.get_tool("smoke_tool", FrameworkType.OPENAI_FUNCTION)
        assert "name" in openai_format
        print("✓ Framework conversion")

        print("\n✅ All smoke tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Universal Tool Framework Test Runner")
    parser.add_argument(
        "mode",
        choices=["basic", "integration", "performance", "all", "coverage", "smoke"],
        help="Test mode to run"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Include benchmark results in performance tests"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Universal Tool Framework Test Runner")
    print("=" * 60)

    start_time = time.time()

    if args.mode == "smoke":
        exit_code = run_quick_smoke_test()
    elif args.mode == "basic":
        exit_code = run_basic_tests()
    elif args.mode == "integration":
        exit_code = run_integration_tests()
    elif args.mode == "performance":
        exit_code = run_performance_tests()
    elif args.mode == "coverage":
        exit_code = run_coverage_tests()
    elif args.mode == "all":
        exit_code = run_all_tests()
    else:
        print(f"Unknown mode: {args.mode}")
        exit_code = 1

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print(f"Test run completed in {elapsed_time:.2f} seconds")
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())