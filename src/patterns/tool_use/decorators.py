# src/patterns/tool_use/decorators.py

import functools
import time
import asyncio
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass, field

from .registry import register_tool


@dataclass
class ToolConfig:
    """Configuration for tool decorators."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    auto_register: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    cache: bool = False
    cache_ttl: int = 300  # 5 minutes


class ToolCache:
    """Simple in-memory cache for tool results."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached result."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < entry['ttl']:
                return entry['value']
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int):
        """Set cached result."""
        self._cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }

    def clear(self):
        """Clear all cached results."""
        self._cache.clear()


# Global cache instance
_tool_cache = ToolCache()


def tool(config: Optional[ToolConfig] = None, **kwargs) -> Callable:
    """
    Decorator to enhance functions with tool capabilities.

    This decorator provides:
    - Automatic tool registration
    - Retry mechanisms
    - Caching
    - Timeout handling
    - Error handling improvements

    Args:
        config: ToolConfig instance or None
        **kwargs: Direct configuration parameters

    Returns:
        Decorated function with enhanced capabilities
    """
    # Handle both ToolConfig object and direct kwargs
    if config is None:
        config = ToolConfig(**kwargs)
    else:
        # Override config with any additional kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    def decorator(func: Callable) -> Callable:
        # Set default values from function if not provided
        if config.name is None:
            config.name = func.__name__
        if config.description is None:
            config.description = func.__doc__ or f"Tool function {func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key if caching is enabled
            cache_key = None
            if config.cache:
                cache_key = f"{config.name}:{hash(str(args) + str(sorted(kwargs.items())))}"
                cached_result = _tool_cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

            # Execute with retry logic
            last_exception = None
            for attempt in range(config.retry_attempts):
                try:
                    # Apply timeout if specified
                    if config.timeout:
                        result = _execute_with_timeout(func, config.timeout, *args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    # Cache result if caching is enabled
                    if config.cache and cache_key:
                        _tool_cache.set(cache_key, result, config.cache_ttl)

                    return result

                except Exception as e:
                    last_exception = e
                    if attempt < config.retry_attempts - 1:
                        time.sleep(config.retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        break

            # If we get here, all retries failed
            raise RuntimeError(f"Tool '{config.name}' failed after {config.retry_attempts} attempts. Last error: {last_exception}")

        # Enhance the wrapper with metadata
        wrapper.tool_config = config
        wrapper.clear_cache = lambda: _tool_cache.clear() if config.cache else None

        # Auto-register if enabled
        if config.auto_register:
            try:
                register_tool(
                    wrapper,
                    name=config.name,
                    category=config.category,
                    tags=config.tags
                )
            except Exception as e:
                print(f"Warning: Failed to auto-register tool '{config.name}': {e}")

        return wrapper

    return decorator


def _execute_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
    """Execute function with timeout."""
    import signal

    class TimeoutError(Exception):
        pass

    def timeout_handler(_signum, _frame):
        raise TimeoutError(f"Function execution timed out after {timeout} seconds")

    # Set up timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))

    try:
        result = func(*args, **kwargs)
        return result
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def async_tool(config: Optional[ToolConfig] = None, **kwargs) -> Callable:
    """
    Decorator for async tool functions.

    Args:
        config: ToolConfig instance or None
        **kwargs: Direct configuration parameters

    Returns:
        Decorated async function with enhanced capabilities
    """
    if config is None:
        config = ToolConfig(**kwargs)

    def decorator(func: Callable) -> Callable:
        if config.name is None:
            config.name = func.__name__
        if config.description is None:
            config.description = func.__doc__ or f"Async tool function {func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key if caching is enabled
            cache_key = None
            if config.cache:
                cache_key = f"{config.name}:{hash(str(args) + str(sorted(kwargs.items())))}"
                cached_result = _tool_cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

            # Execute with retry logic
            last_exception = None
            for attempt in range(config.retry_attempts):
                try:
                    # Apply timeout if specified
                    if config.timeout:
                        result = await asyncio.wait_for(func(*args, **kwargs), timeout=config.timeout)
                    else:
                        result = await func(*args, **kwargs)

                    # Cache result if caching is enabled
                    if config.cache and cache_key:
                        _tool_cache.set(cache_key, result, config.cache_ttl)

                    return result

                except Exception as e:
                    last_exception = e
                    if attempt < config.retry_attempts - 1:
                        await asyncio.sleep(config.retry_delay * (attempt + 1))
                    else:
                        break

            raise RuntimeError(f"Async tool '{config.name}' failed after {config.retry_attempts} attempts. Last error: {last_exception}")

        # Enhance the wrapper with metadata
        async_wrapper.tool_config = config
        async_wrapper.clear_cache = lambda: _tool_cache.clear() if config.cache else None

        # Auto-register if enabled
        if config.auto_register:
            try:
                register_tool(
                    async_wrapper,
                    name=config.name,
                    category=config.category,
                    tags=config.tags
                )
            except Exception as e:
                print(f"Warning: Failed to auto-register async tool '{config.name}': {e}")

        return async_wrapper

    return decorator


def robust_tool(retries: int = 3, delay: float = 1.0, timeout: Optional[float] = None,
                cache: bool = False, category: Optional[str] = None,
                tags: List[str] = None) -> Callable:
    """
    Convenience decorator for creating robust tools with common patterns.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries
        timeout: Execution timeout in seconds
        cache: Whether to enable caching
        category: Tool category
        tags: Tool tags

    Returns:
        Tool decorator
    """
    config = ToolConfig(
        retry_attempts=retries,
        retry_delay=delay,
        timeout=timeout,
        cache=cache,
        category=category,
        tags=tags or []
    )
    return tool(config)


def cached_tool(ttl: int = 300, category: Optional[str] = None,
                tags: List[str] = None) -> Callable:
    """
    Convenience decorator for creating cached tools.

    Args:
        ttl: Cache time-to-live in seconds
        category: Tool category
        tags: Tool tags

    Returns:
        Tool decorator with caching enabled
    """
    config = ToolConfig(
        cache=True,
        cache_ttl=ttl,
        category=category,
        tags=tags or []
    )
    return tool(config)


def quick_tool(name: Optional[str] = None, description: Optional[str] = None,
               category: Optional[str] = None) -> Callable:
    """
    Simple decorator for quick tool creation with minimal configuration.

    Args:
        name: Tool name
        description: Tool description
        category: Tool category

    Returns:
        Simple tool decorator
    """
    config = ToolConfig(
        name=name,
        description=description,
        category=category,
        retry_attempts=1,  # No retries for quick tools
        cache=False
    )
    return tool(config)


class ToolBuilder:
    """Builder class for creating tools with complex configurations."""

    def __init__(self):
        self.config = ToolConfig()

    def name(self, name: str) -> 'ToolBuilder':
        """Set tool name."""
        self.config.name = name
        return self

    def description(self, description: str) -> 'ToolBuilder':
        """Set tool description."""
        self.config.description = description
        return self

    def category(self, category: str) -> 'ToolBuilder':
        """Set tool category."""
        self.config.category = category
        return self

    def tags(self, *tags: str) -> 'ToolBuilder':
        """Add tags to tool."""
        self.config.tags.extend(tags)
        return self

    def retry(self, attempts: int, delay: float = 1.0) -> 'ToolBuilder':
        """Configure retry behavior."""
        self.config.retry_attempts = attempts
        self.config.retry_delay = delay
        return self

    def timeout(self, seconds: float) -> 'ToolBuilder':
        """Set execution timeout."""
        self.config.timeout = seconds
        return self

    def cache(self, enabled: bool = True, ttl: int = 300) -> 'ToolBuilder':
        """Configure caching."""
        self.config.cache = enabled
        self.config.cache_ttl = ttl
        return self

    def auto_register(self, enabled: bool = True) -> 'ToolBuilder':
        """Configure auto-registration."""
        self.config.auto_register = enabled
        return self

    def build(self) -> Callable:
        """Build the tool decorator."""
        return tool(self.config)


# Utility functions for working with decorated tools
def clear_tool_cache():
    """Clear the global tool cache."""
    _tool_cache.clear()


def get_tool_stats() -> Dict[str, Any]:
    """Get statistics about cached tools."""
    cache_entries = len(_tool_cache._cache)
    total_size = sum(len(str(entry['value'])) for entry in _tool_cache._cache.values())

    return {
        "cached_entries": cache_entries,
        "estimated_cache_size_bytes": total_size,
        "cache_hits": getattr(_tool_cache, '_hits', 0),
        "cache_misses": getattr(_tool_cache, '_misses', 0)
    }