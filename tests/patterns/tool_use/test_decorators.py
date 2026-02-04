# tests/patterns/tool_use/test_decorators.py

import pytest
import time
import asyncio
from unittest.mock import Mock, patch

from src.patterns.tool_use.decorators import (
    tool,
    async_tool,
    robust_tool,
    cached_tool,
    quick_tool,
    ToolConfig,
    ToolBuilder,
    clear_tool_cache,
    get_tool_stats,
    _tool_cache
)


class TestToolConfig:
    """Test ToolConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ToolConfig()
        assert config.name is None
        assert config.description is None
        assert config.category is None
        assert config.tags == []
        assert config.auto_register is True
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.timeout is None
        assert config.cache is False
        assert config.cache_ttl == 300

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ToolConfig(
            name="test_tool",
            description="Test description",
            category="test",
            tags=["tag1", "tag2"],
            retry_attempts=5,
            cache=True,
            cache_ttl=600
        )
        assert config.name == "test_tool"
        assert config.description == "Test description"
        assert config.category == "test"
        assert config.tags == ["tag1", "tag2"]
        assert config.retry_attempts == 5
        assert config.cache is True
        assert config.cache_ttl == 600


class TestBasicToolDecorator:
    """Test the basic @tool decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    def test_basic_tool_decoration(self):
        """Test basic tool decoration without configuration."""
        @tool()
        def simple_func(x: int) -> str:
            """Simple test function."""
            return str(x * 2)

        # Test execution
        result = simple_func(5)
        assert result == "10"

        # Test metadata
        assert hasattr(simple_func, 'tool_config')
        config = simple_func.tool_config
        assert config.name == "simple_func"
        assert "Simple test function" in config.description

    def test_tool_with_config_object(self):
        """Test tool decoration with ToolConfig object."""
        config = ToolConfig(
            name="configured_tool",
            description="A configured tool",
            category="test",
            retry_attempts=5,
            cache=True
        )

        @tool(config)
        def configured_func(data: str) -> str:
            return f"Processed: {data}"

        # Test execution
        result = configured_func("test")
        assert result == "Processed: test"

        # Test configuration
        assert configured_func.tool_config.name == "configured_tool"
        assert configured_func.tool_config.retry_attempts == 5
        assert configured_func.tool_config.cache is True

    def test_tool_with_kwargs(self):
        """Test tool decoration with keyword arguments."""
        @tool(name="kwargs_tool", description="Tool with kwargs", cache=True, retry_attempts=2)
        def kwargs_func(value: int) -> int:
            return value + 1

        result = kwargs_func(10)
        assert result == 11

        config = kwargs_func.tool_config
        assert config.name == "kwargs_tool"
        assert config.description == "Tool with kwargs"
        assert config.cache is True
        assert config.retry_attempts == 2

    def test_tool_auto_name_from_function(self):
        """Test automatic name extraction from function name."""
        @tool()
        def auto_named_function() -> str:
            return "auto"

        assert auto_named_function.tool_config.name == "auto_named_function"

    @patch('src.patterns.tool_use.decorators.register_tool')
    def test_auto_registration_enabled(self, mock_register):
        """Test that auto-registration is called when enabled."""
        @tool(auto_register=True)
        def auto_registered_func() -> str:
            """Auto-registered function."""
            return "registered"

        # Should have attempted registration
        mock_register.assert_called_once()

    @patch('src.patterns.tool_use.decorators.register_tool')
    def test_auto_registration_disabled(self, mock_register):
        """Test that auto-registration is skipped when disabled."""
        @tool(auto_register=False)
        def not_registered_func() -> str:
            """Not auto-registered function."""
            return "not registered"

        # Should not have attempted registration
        mock_register.assert_not_called()


class TestToolRetryMechanism:
    """Test retry functionality in tools."""

    def test_successful_execution_no_retry(self):
        """Test successful execution without retries."""
        call_count = 0

        @tool(retry_attempts=3)
        def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test retry mechanism on function failure."""
        call_count = 0

        @tool(retry_attempts=3, retry_delay=0.01)  # Fast retry for testing
        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success after retries"

        result = failing_func()
        assert result == "success after retries"
        assert call_count == 3

    def test_all_retries_exhausted(self):
        """Test behavior when all retries are exhausted."""
        call_count = 0

        @tool(retry_attempts=2, retry_delay=0.01)
        def always_failing_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RuntimeError, match="failed after 2 attempts"):
            always_failing_func()

        assert call_count == 2


class TestToolCaching:
    """Test caching functionality in tools."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    def test_caching_enabled(self):
        """Test that caching works when enabled."""
        call_count = 0

        @tool(cache=True, cache_ttl=60)
        def cached_func(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed_{value}"

        # First call
        result1 = cached_func("test")
        assert result1 == "processed_test"
        assert call_count == 1

        # Second call should use cache
        result2 = cached_func("test")
        assert result2 == "processed_test"
        assert call_count == 1  # Should not increment

        # Different input should not use cache
        result3 = cached_func("different")
        assert result3 == "processed_different"
        assert call_count == 2

    def test_caching_disabled(self):
        """Test that caching is bypassed when disabled."""
        call_count = 0

        @tool(cache=False)
        def uncached_func(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed_{value}"

        # Multiple calls should always execute
        uncached_func("test")
        uncached_func("test")
        assert call_count == 2

    def test_cache_clear_functionality(self):
        """Test cache clearing functionality."""
        call_count = 0

        @tool(cache=True)
        def clearable_func(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # First call
        clearable_func("test")
        assert call_count == 1

        # Second call uses cache
        clearable_func("test")
        assert call_count == 1

        # Clear cache
        clear_tool_cache()

        # Third call should execute again
        clearable_func("test")
        assert call_count == 2


class TestConvenienceDecorators:
    """Test convenience decorator functions."""

    def test_robust_tool_decorator(self):
        """Test @robust_tool convenience decorator."""
        call_count = 0

        @robust_tool(retries=2, delay=0.01, cache=True)
        def robust_func(data: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt fails")
            return f"robust_{data}"

        result = robust_func("test")
        assert result == "robust_test"
        assert call_count == 2

        # Test caching
        result2 = robust_func("test")
        assert call_count == 2  # Should use cache

    def test_cached_tool_decorator(self):
        """Test @cached_tool convenience decorator."""
        call_count = 0

        @cached_tool(ttl=30, category="test")
        def cached_convenience_func(value: int) -> int:
            nonlocal call_count
            call_count += 1
            return value * 2

        result1 = cached_convenience_func(5)
        result2 = cached_convenience_func(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Second call should use cache

    def test_quick_tool_decorator(self):
        """Test @quick_tool convenience decorator."""
        @quick_tool(name="quick", description="Quick tool")
        def quick_func() -> str:
            return "quick"

        result = quick_func()
        assert result == "quick"

        config = quick_func.tool_config
        assert config.name == "quick"
        assert config.description == "Quick tool"
        assert config.retry_attempts == 1  # Quick tools don't retry
        assert config.cache is False


class TestToolBuilder:
    """Test the ToolBuilder fluent interface."""

    def test_builder_pattern(self):
        """Test building tool configuration with fluent interface."""
        builder = ToolBuilder()
        decorator = (builder
                    .name("built_tool")
                    .description("Tool built with builder")
                    .category("builder")
                    .tags("tag1", "tag2")
                    .retry(5, 0.5)
                    .timeout(30.0)
                    .cache(True, 600)
                    .build())

        @decorator
        def built_func(data: str) -> str:
            return f"built_{data}"

        config = built_func.tool_config
        assert config.name == "built_tool"
        assert config.description == "Tool built with builder"
        assert config.category == "builder"
        assert config.tags == ["tag1", "tag2"]
        assert config.retry_attempts == 5
        assert config.retry_delay == 0.5
        assert config.timeout == 30.0
        assert config.cache is True
        assert config.cache_ttl == 600


class TestAsyncToolDecorator:
    """Test async tool decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    @pytest.mark.asyncio
    async def test_basic_async_tool(self):
        """Test basic async tool functionality."""
        @async_tool()
        async def async_func(delay: float) -> str:
            """Async test function."""
            await asyncio.sleep(delay)
            return f"completed after {delay}s"

        result = await async_func(0.01)
        assert result == "completed after 0.01s"

    @pytest.mark.asyncio
    async def test_async_tool_with_retry(self):
        """Test async tool retry mechanism."""
        call_count = 0

        @async_tool(retry_attempts=3, retry_delay=0.01)
        async def async_retry_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Async failure")
            return "async success"

        result = await async_retry_func()
        assert result == "async success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_tool_caching(self):
        """Test async tool caching."""
        call_count = 0

        @async_tool(cache=True)
        async def async_cached_func(value: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"async_{value}"

        # First call
        result1 = await async_cached_func("test")
        assert result1 == "async_test"
        assert call_count == 1

        # Second call should use cache
        result2 = await async_cached_func("test")
        assert result2 == "async_test"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_tool_timeout(self):
        """Test async tool timeout functionality."""
        @async_tool(timeout=0.05)
        async def slow_async_func() -> str:
            await asyncio.sleep(0.1)  # Longer than timeout
            return "should not complete"

        with pytest.raises(asyncio.TimeoutError):
            await slow_async_func()


class TestCacheUtilities:
    """Test cache utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    def test_cache_stats(self):
        """Test cache statistics functionality."""
        @cached_tool()
        def stats_func(value: int) -> int:
            return value * 2

        # Initial stats
        initial_stats = get_tool_stats()
        assert initial_stats["cached_entries"] == 0

        # Add some cached data
        stats_func(1)
        stats_func(2)
        stats_func(1)  # Should hit cache

        # Check updated stats
        updated_stats = get_tool_stats()
        assert updated_stats["cached_entries"] >= 1  # At least one cached entry

    def test_clear_cache_function(self):
        """Test global cache clearing."""
        @cached_tool()
        def clear_test_func(value: str) -> str:
            return f"cached_{value}"

        # Add cached data
        clear_test_func("test")
        stats_before = get_tool_stats()
        assert stats_before["cached_entries"] > 0

        # Clear cache
        clear_tool_cache()
        stats_after = get_tool_stats()
        assert stats_after["cached_entries"] == 0


def test_tool_config_preservation():
    """Test that tool configuration is preserved across calls."""
    config = ToolConfig(
        name="preserved",
        retry_attempts=10,
        cache=True
    )

    @tool(config)
    def preservation_test() -> str:
        return "preserved"

    # Call the function multiple times
    for _ in range(3):
        preservation_test()

    # Configuration should remain unchanged
    final_config = preservation_test.tool_config
    assert final_config.name == "preserved"
    assert final_config.retry_attempts == 10
    assert final_config.cache is True


if __name__ == "__main__":
    pytest.main([__file__])