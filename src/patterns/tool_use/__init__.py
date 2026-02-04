# src/patterns/tool_use/__init__.py

"""
Universal Tool Framework for Multi-Agent Systems

This package provides a comprehensive framework for creating, registering, and managing
tools across different AI frameworks (CrewAI, LangChain, OpenAI Functions, etc.).

Key Features:
- Cross-framework tool compatibility
- Automatic tool registration and discovery
- Advanced decorators for tool enhancement (caching, retries, timeouts)
- Comprehensive validation and testing
- Performance monitoring and optimization

Main Components:
- registry: Universal tool registry and adapters
- decorators: Tool enhancement decorators
- validation: Tool validation and testing framework
- examples: Comprehensive usage examples
"""

# Core registry functionality
from .registry import (
    # Main registry
    UniversalToolRegistry,
    global_tool_registry,

    # Metadata and configuration
    ToolMetadata,
    FrameworkType,

    # Adapters
    BaseToolAdapter,
    CrewAIToolAdapter,
    LangChainToolAdapter,
    FunctionToolAdapter,

    # Convenience functions
    register_tool,
    get_tool,
    list_tools
)

# Tool decorators and builders
from .decorators import (
    # Core decorators
    tool,
    async_tool,

    # Convenience decorators
    robust_tool,
    cached_tool,
    quick_tool,

    # Configuration
    ToolConfig,
    ToolBuilder,

    # Utility functions
    clear_tool_cache,
    get_tool_stats
)

# Validation and testing
from .validation import (
    # Validation classes
    ToolValidator,
    ToolTestSuite,

    # Result types
    ValidationResult,
    PerformanceMetrics
)

# Re-export commonly used items
__all__ = [
    # Registry
    "UniversalToolRegistry",
    "global_tool_registry",
    "ToolMetadata",
    "FrameworkType",
    "BaseToolAdapter",
    "CrewAIToolAdapter",
    "LangChainToolAdapter",
    "FunctionToolAdapter",
    "register_tool",
    "get_tool",
    "list_tools",

    # Decorators
    "tool",
    "async_tool",
    "robust_tool",
    "cached_tool",
    "quick_tool",
    "ToolConfig",
    "ToolBuilder",
    "clear_tool_cache",
    "get_tool_stats",

    # Validation
    "ToolValidator",
    "ToolTestSuite",
    "ValidationResult",
    "PerformanceMetrics"
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "CrewAI Course Framework"
__description__ = "Universal tool framework for multi-agent systems"