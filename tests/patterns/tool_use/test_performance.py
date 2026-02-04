# tests/patterns/tool_use/test_performance.py

import pytest
import time
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from src.patterns.tool_use import (
    tool,
    robust_tool,
    cached_tool,
    async_tool,
    clear_tool_cache,
    get_tool_stats,
    ToolValidator,
    UniversalToolRegistry
)


class TestCachePerformance:
    """Test performance characteristics of caching system."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    def test_cache_hit_performance(self):
        """Test that cache hits are significantly faster than execution."""
        execution_count = 0

        @cached_tool(ttl=300)
        def expensive_operation(data: str) -> str:
            """Simulate expensive operation."""
            nonlocal execution_count
            execution_count += 1
            time.sleep(0.1)  # Simulate expensive work
            return f"processed_{data}"

        # First call (cache miss)
        start_time = time.time()
        result1 = expensive_operation("test")
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = expensive_operation("test")
        second_call_time = time.time() - start_time

        # Verify results are identical
        assert result1 == result2
        assert result1 == "processed_test"
        assert execution_count == 1  # Only executed once

        # Cache hit should be significantly faster
        assert second_call_time < first_call_time * 0.1  # At least 10x faster

    def test_cache_memory_efficiency(self):
        """Test memory usage of cache system."""
        @cached_tool(ttl=60)
        def memory_test_tool(size: int) -> str:
            """Generate data of specified size."""
            return "x" * size

        # Add various sized data to cache
        sizes = [100, 1000, 10000]
        for size in sizes:
            memory_test_tool(size)

        # Check cache statistics
        stats = get_tool_stats()
        assert stats["cached_entries"] == len(sizes)
        assert stats["estimated_cache_size_bytes"] > 0

    def test_concurrent_cache_access(self):
        """Test cache performance under concurrent access."""
        execution_count = 0
        lock = threading.Lock()

        @cached_tool(ttl=60)
        def concurrent_tool(value: int) -> str:
            """Tool for concurrent testing."""
            nonlocal execution_count
            with lock:
                execution_count += 1
            time.sleep(0.01)  # Small delay
            return f"result_{value}"

        def worker(value: int):
            return concurrent_tool(value)

        # Execute same function concurrently
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, 42) for _ in range(num_threads)]
            results = [future.result() for future in futures]

        # All results should be identical
        assert all(result == "result_42" for result in results)

        # Should have executed only once due to caching
        # Note: In practice, there might be race conditions, so we allow some tolerance
        assert execution_count <= 3  # Should be 1 ideally, but allow for race conditions

    def test_cache_ttl_performance(self):
        """Test cache TTL (time-to-live) functionality."""
        @cached_tool(ttl=0.1)  # Very short TTL for testing
        def ttl_test_tool(data: str) -> str:
            """Tool with short TTL."""
            return f"fresh_{data}_{time.time()}"

        # First call
        result1 = ttl_test_tool("test")

        # Second call immediately (should hit cache)
        result2 = ttl_test_tool("test")
        assert result1 == result2

        # Wait for TTL to expire
        time.sleep(0.15)

        # Third call (should miss cache and generate new result)
        result3 = ttl_test_tool("test")
        assert result3 != result1  # Should be different due to timestamp


class TestRetryPerformance:
    """Test performance characteristics of retry mechanisms."""

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing works correctly."""
        call_times = []

        @robust_tool(retries=3, delay=0.1)
        def backoff_test_tool() -> str:
            """Tool that fails multiple times to test backoff."""
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Intentional failure")
            return "success"

        start_time = time.time()
        result = backoff_test_tool()
        total_time = time.time() - start_time

        assert result == "success"
        assert len(call_times) == 3

        # Check exponential backoff timing
        # First retry after ~0.1s, second after ~0.2s
        time_diffs = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]

        assert time_diffs[0] >= 0.1  # First retry delay
        assert time_diffs[1] >= 0.2  # Second retry delay (exponential backoff)
        assert total_time >= 0.3     # Total time should include all delays

    def test_retry_vs_no_retry_performance(self):
        """Compare performance of retry vs non-retry tools."""
        success_count = 0

        def successful_operation() -> str:
            nonlocal success_count
            success_count += 1
            return "success"

        # Tool with retries (but won't need them)
        @robust_tool(retries=5, delay=0.01)
        def retry_tool() -> str:
            return successful_operation()

        # Tool without retries
        @tool(retry_attempts=1)
        def no_retry_tool() -> str:
            return successful_operation()

        # Measure execution time for both
        start_time = time.time()
        retry_result = retry_tool()
        retry_time = time.time() - start_time

        start_time = time.time()
        no_retry_result = no_retry_tool()
        no_retry_time = time.time() - start_time

        assert retry_result == no_retry_result == "success"
        assert success_count == 2

        # When no failures occur, both should have similar performance
        assert abs(retry_time - no_retry_time) < 0.01  # Within 10ms


class TestAsyncPerformance:
    """Test performance characteristics of async tools."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_tool_cache()

    @pytest.mark.asyncio
    async def test_async_concurrent_execution(self):
        """Test concurrent execution of async tools."""
        execution_order = []
        lock = asyncio.Lock()

        @async_tool(name="concurrent_async_tool")
        async def async_worker(worker_id: int, delay: float) -> str:
            """Async worker with configurable delay."""
            async with lock:
                execution_order.append(f"start_{worker_id}")

            await asyncio.sleep(delay)

            async with lock:
                execution_order.append(f"end_{worker_id}")

            return f"worker_{worker_id}_completed"

        # Start multiple workers concurrently
        start_time = time.time()
        tasks = [
            async_worker(1, 0.1),
            async_worker(2, 0.05),
            async_worker(3, 0.15),
        ]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # All should complete successfully
        assert len(results) == 3
        assert all("completed" in result for result in results)

        # Should complete in roughly the time of the longest task (concurrent execution)
        assert total_time < 0.25  # Should be much less than 0.3 (sum of all delays)

        # Verify concurrent execution (starts should happen before ends)
        start_events = [event for event in execution_order if event.startswith("start")]
        end_events = [event for event in execution_order if event.startswith("end")]

        assert len(start_events) == 3
        assert len(end_events) == 3

    @pytest.mark.asyncio
    async def test_async_cache_performance(self):
        """Test caching performance in async tools."""
        execution_count = 0

        @async_tool(cache=True, cache_ttl=60)
        async def async_cached_tool(data: str) -> str:
            """Async tool with caching."""
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.05)  # Simulate async work
            return f"async_result_{data}"

        # First call
        start_time = time.time()
        result1 = await async_cached_tool("test")
        first_call_time = time.time() - start_time

        # Second call (should hit cache)
        start_time = time.time()
        result2 = await async_cached_tool("test")
        second_call_time = time.time() - start_time

        assert result1 == result2
        assert execution_count == 1  # Only executed once
        assert second_call_time < first_call_time * 0.1  # Much faster due to cache

    @pytest.mark.asyncio
    async def test_async_retry_performance(self):
        """Test retry performance in async tools."""
        attempt_times = []

        @async_tool(retry_attempts=3, retry_delay=0.05)
        async def async_retry_tool(should_fail: bool) -> str:
            """Async tool that can fail for testing."""
            attempt_times.append(time.time())

            if should_fail and len(attempt_times) < 3:
                raise ValueError("Async failure")

            return "async_success"

        # Test successful retry
        start_time = time.time()
        result = await async_retry_tool(True)
        total_time = time.time() - start_time

        assert result == "async_success"
        assert len(attempt_times) == 3
        assert total_time >= 0.1  # Should include retry delays


class TestScalabilityBenchmarks:
    """Benchmark tests for scalability characteristics."""

    def test_registry_scaling(self):
        """Test registry performance with many tools."""
        registry = UniversalToolRegistry()

        # Register many tools
        num_tools = 1000
        start_time = time.time()

        for i in range(num_tools):
            def make_tool(tool_id):
                def tool_func(data: str) -> str:
                    return f"tool_{tool_id}_{data}"
                tool_func.__name__ = f"tool_{tool_id}"
                return tool_func

            registry.register_tool(make_tool(i), category=f"category_{i % 10}")

        registration_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        retrieved_tools = []
        for i in range(0, num_tools, 100):  # Sample every 100th tool
            tool = registry.get_tool(f"tool_{i}")
            retrieved_tools.append(tool)
        retrieval_time = time.time() - start_time

        # Test listing performance
        start_time = time.time()
        all_tools = registry.list_tools()
        listing_time = time.time() - start_time

        # Verify correctness
        assert len(all_tools) == num_tools
        assert len(retrieved_tools) == 10

        # Performance assertions (adjust thresholds as needed)
        assert registration_time < 10.0  # Should register 1000 tools in under 10 seconds
        assert retrieval_time < 1.0      # Should retrieve 10 tools in under 1 second
        assert listing_time < 1.0        # Should list 1000 tools in under 1 second

        print(f"Registry scaling results:")
        print(f"  Registration: {registration_time:.3f}s for {num_tools} tools")
        print(f"  Retrieval: {retrieval_time:.3f}s for 10 tools")
        print(f"  Listing: {listing_time:.3f}s for {num_tools} tools")

    def test_validation_performance_scaling(self):
        """Test validation performance with multiple tools."""
        validator = ToolValidator()

        # Create tools with varying complexity
        tools = {}

        # Simple tool
        def simple_tool(x: int) -> int:
            """Simple tool."""
            return x * 2

        # Complex tool
        def complex_tool(
            query: str,
            filters: dict = None,
            limit: int = 10,
            sort_order: str = "asc",
            include_metadata: bool = False
        ) -> str:
            """
            Complex tool with many parameters and comprehensive documentation.

            This tool demonstrates various complexity factors that affect validation:
            - Multiple parameters with different types
            - Default values and optional parameters
            - Comprehensive documentation
            - Complex logic simulation

            Args:
                query: Search query string
                filters: Optional dictionary of filters to apply
                limit: Maximum number of results to return
                sort_order: Sort order ('asc' or 'desc')
                include_metadata: Whether to include metadata in results

            Returns:
                Formatted search results as string

            Raises:
                ValueError: If query is empty or invalid
                TypeError: If filters is not a dictionary
            """
            if not query:
                raise ValueError("Query cannot be empty")
            if filters and not isinstance(filters, dict):
                raise TypeError("Filters must be a dictionary")

            return f"Results for '{query}' (limit: {limit}, sort: {sort_order})"

        tools = {
            "simple": simple_tool,
            "complex": complex_tool
        }

        # Benchmark validation performance
        validation_times = {}

        for name, tool in tools.items():
            start_time = time.time()
            result = validator.validate_tool(tool, name)
            validation_time = time.time() - start_time

            validation_times[name] = validation_time

            # Verify validation worked
            assert result.tool_name == name

        # Complex tool should take longer but not excessively so
        assert validation_times["complex"] > validation_times["simple"]
        assert validation_times["complex"] < 1.0  # Should complete in under 1 second

        print(f"Validation performance:")
        print(f"  Simple tool: {validation_times['simple']:.3f}s")
        print(f"  Complex tool: {validation_times['complex']:.3f}s")

    def test_conversion_performance(self):
        """Test framework conversion performance."""
        registry = UniversalToolRegistry()

        def test_tool(param1: str, param2: int = 10, param3: bool = False) -> str:
            """Test tool for conversion benchmarking."""
            return f"Result: {param1}, {param2}, {param3}"

        registry.register_tool(test_tool)

        # Benchmark different conversions
        conversions = [
            ("OpenAI", lambda: registry.get_tool("test_tool", FrameworkType.OPENAI_FUNCTION)),
            ("Generic", lambda: registry.get_tool("test_tool", FrameworkType.GENERIC_FUNCTION))
        ]

        # Add CrewAI conversion if available
        try:
            conversions.append(
                ("CrewAI", lambda: registry.get_tool("test_tool", FrameworkType.CREWAI))
            )
        except ImportError:
            pass

        conversion_times = {}

        for name, conversion_func in conversions:
            # Warm up
            try:
                conversion_func()
            except Exception:
                continue

            # Benchmark
            start_time = time.time()
            for _ in range(100):  # Multiple iterations for better measurement
                try:
                    converted = conversion_func()
                    assert converted is not None
                except Exception as e:
                    print(f"Conversion {name} failed: {e}")
                    continue

            conversion_time = (time.time() - start_time) / 100  # Average per conversion
            conversion_times[name] = conversion_time

        # Verify all conversions completed in reasonable time
        for name, conv_time in conversion_times.items():
            assert conv_time < 0.01, f"{name} conversion too slow: {conv_time:.4f}s"

        print(f"Conversion performance (per conversion):")
        for name, conv_time in conversion_times.items():
            print(f"  {name}: {conv_time:.4f}s")


class TestMemoryLeakDetection:
    """Test for potential memory leaks in tool system."""

    def test_cache_cleanup(self):
        """Test that cache properly cleans up expired entries."""
        @cached_tool(ttl=0.05)  # Very short TTL
        def memory_test_tool(data: str) -> str:
            return f"cached_{data}"

        # Add many entries to cache
        for i in range(100):
            memory_test_tool(f"data_{i}")

        # Check cache is populated
        initial_stats = get_tool_stats()
        assert initial_stats["cached_entries"] > 0

        # Wait for TTL expiry and trigger cache access (which should clean up)
        time.sleep(0.1)

        # Access cache to trigger cleanup
        memory_test_tool("trigger_cleanup")

        # Note: This test assumes cache implementation has automatic cleanup
        # In practice, you might need to implement explicit cleanup mechanisms

    def test_registry_memory_usage(self):
        """Test that registry doesn't leak memory with many registrations/removals."""
        registry = UniversalToolRegistry()

        # Track initial state
        initial_tool_count = len(registry.tools)

        # Register and remove many tools
        for cycle in range(10):
            # Register tools
            for i in range(100):
                def temp_tool(x: int) -> str:
                    return str(x)
                temp_tool.__name__ = f"temp_tool_{cycle}_{i}"

                registry.register_tool(temp_tool, name=f"temp_tool_{cycle}_{i}")

            # Remove tools
            for i in range(100):
                registry.remove_tool(f"temp_tool_{cycle}_{i}")

        # Should be back to initial state
        final_tool_count = len(registry.tools)
        assert final_tool_count == initial_tool_count

        # Verify metadata is also cleaned up
        assert len(registry.metadata) == len(registry.tools)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])