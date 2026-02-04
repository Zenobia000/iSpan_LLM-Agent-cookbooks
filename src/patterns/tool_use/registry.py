# src/patterns/tool_use/registry.py

import inspect
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, Callable, get_type_hints
from pydantic import BaseModel, Field, ValidationError

# Framework imports (with fallbacks)
try:
    from crewai.tools import BaseTool as CrewAITool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAITool = None

try:
    from langchain_core.tools import BaseTool as LangChainTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LangChainTool = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Set up logging
logger = logging.getLogger(__name__)


class FrameworkType(Enum):
    """Supported tool frameworks."""
    CREWAI = "crewai"
    LANGCHAIN = "langchain"
    OPENAI_FUNCTION = "openai_function"
    GENERIC_FUNCTION = "generic_function"


class ToolMetadata(BaseModel):
    """Metadata for registered tools."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    framework: FrameworkType = Field(..., description="Source framework")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    category: Optional[str] = Field(default=None, description="Tool category")
    version: str = Field(default="1.0.0", description="Tool version")
    author: Optional[str] = Field(default=None, description="Tool author")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    requirements: List[str] = Field(default_factory=list, description="Required dependencies")


class BaseToolAdapter(ABC):
    """Abstract base class for tool adapters."""

    @abstractmethod
    def extract_metadata(self, tool: Any) -> ToolMetadata:
        """Extract metadata from a tool."""
        pass

    @abstractmethod
    def convert_to_framework(self, tool: Any, target_framework: FrameworkType) -> Any:
        """Convert tool to target framework format."""
        pass

    @abstractmethod
    def validate_tool(self, tool: Any) -> bool:
        """Validate that the tool is compatible with this adapter."""
        pass


class CrewAIToolAdapter(BaseToolAdapter):
    """Adapter for CrewAI tools."""

    def extract_metadata(self, tool: Any) -> ToolMetadata:
        """Extract metadata from CrewAI tool."""
        if not self.validate_tool(tool):
            raise ValueError(f"Invalid CrewAI tool: {tool}")

        # Extract schema information
        parameters = {}
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.model_json_schema()
            parameters = schema.get('properties', {})

        return ToolMetadata(
            name=getattr(tool, 'name', tool.__class__.__name__),
            description=getattr(tool, 'description', ''),
            framework=FrameworkType.CREWAI,
            parameters=parameters,
            category=getattr(tool, 'category', None),
            tags=getattr(tool, 'tags', [])
        )

    def convert_to_framework(self, tool: Any, target_framework: FrameworkType) -> Any:
        """Convert CrewAI tool to target framework."""
        if target_framework == FrameworkType.CREWAI:
            return tool

        elif target_framework == FrameworkType.OPENAI_FUNCTION:
            return self._convert_to_openai_function(tool)

        elif target_framework == FrameworkType.GENERIC_FUNCTION:
            return self._convert_to_generic_function(tool)

        else:
            raise NotImplementedError(f"Conversion to {target_framework} not implemented")

    def validate_tool(self, tool: Any) -> bool:
        """Validate CrewAI tool."""
        if not CREWAI_AVAILABLE:
            return False
        return isinstance(tool, CrewAITool) or hasattr(tool, '_run')

    def _convert_to_openai_function(self, tool: Any) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        metadata = self.extract_metadata(tool)

        function_spec = {
            "name": metadata.name.replace(' ', '_').lower(),
            "description": metadata.description,
            "parameters": {
                "type": "object",
                "properties": metadata.parameters,
                "required": []
            }
        }

        # Extract required parameters
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.model_json_schema()
            function_spec["parameters"]["required"] = schema.get('required', [])

        return function_spec

    def _convert_to_generic_function(self, tool: Any) -> Callable:
        """Convert to generic Python function."""
        def generic_function(**kwargs):
            return tool._run(**kwargs)

        generic_function.__name__ = tool.name.replace(' ', '_').lower()
        generic_function.__doc__ = tool.description
        return generic_function


class LangChainToolAdapter(BaseToolAdapter):
    """Adapter for LangChain tools."""

    def extract_metadata(self, tool: Any) -> ToolMetadata:
        """Extract metadata from LangChain tool."""
        if not self.validate_tool(tool):
            raise ValueError(f"Invalid LangChain tool: {tool}")

        # Extract schema information
        parameters = {}
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.model_json_schema()
            parameters = schema.get('properties', {})

        return ToolMetadata(
            name=getattr(tool, 'name', tool.__class__.__name__),
            description=getattr(tool, 'description', ''),
            framework=FrameworkType.LANGCHAIN,
            parameters=parameters
        )

    def convert_to_framework(self, tool: Any, target_framework: FrameworkType) -> Any:
        """Convert LangChain tool to target framework."""
        if target_framework == FrameworkType.LANGCHAIN:
            return tool

        elif target_framework == FrameworkType.CREWAI and CREWAI_AVAILABLE:
            return self._convert_to_crewai(tool)

        elif target_framework == FrameworkType.GENERIC_FUNCTION:
            return self._convert_to_generic_function(tool)

        else:
            raise NotImplementedError(f"Conversion to {target_framework} not implemented")

    def validate_tool(self, tool: Any) -> bool:
        """Validate LangChain tool."""
        if not LANGCHAIN_AVAILABLE:
            return False
        return isinstance(tool, LangChainTool) or hasattr(tool, '_run')

    def _convert_to_crewai(self, tool: Any) -> Any:
        """Convert to CrewAI tool format."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available for conversion")

        class ConvertedCrewAITool(CrewAITool):
            name: str = tool.name
            description: str = tool.description
            args_schema: Type[BaseModel] = tool.args_schema

            def _run(self, **kwargs) -> str:
                return tool._run(**kwargs)

        return ConvertedCrewAITool()

    def _convert_to_generic_function(self, tool: Any) -> Callable:
        """Convert to generic Python function."""
        def generic_function(**kwargs):
            return tool._run(**kwargs)

        generic_function.__name__ = tool.name.replace(' ', '_').lower()
        generic_function.__doc__ = tool.description
        return generic_function


class FunctionToolAdapter(BaseToolAdapter):
    """Adapter for generic Python functions."""

    def extract_metadata(self, tool: Callable) -> ToolMetadata:
        """Extract metadata from Python function."""
        if not self.validate_tool(tool):
            raise ValueError(f"Invalid function tool: {tool}")

        # Extract parameter information from function signature
        sig = inspect.signature(tool)
        parameters = {}

        type_hints = get_type_hints(tool)

        for param_name, param in sig.parameters.items():
            param_info = {
                "type": "string",  # Default type
                "description": f"Parameter {param_name}"
            }

            # Add type information if available
            if param_name in type_hints:
                param_type = type_hints[param_name]
                if param_type == int:
                    param_info["type"] = "integer"
                elif param_type == float:
                    param_info["type"] = "number"
                elif param_type == bool:
                    param_info["type"] = "boolean"
                elif param_type == list:
                    param_info["type"] = "array"
                elif param_type == dict:
                    param_info["type"] = "object"

            # Add default value info
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default

            parameters[param_name] = param_info

        return ToolMetadata(
            name=getattr(tool, '__name__', 'unnamed_function'),
            description=getattr(tool, '__doc__', '') or f"Function {tool.__name__}",
            framework=FrameworkType.GENERIC_FUNCTION,
            parameters=parameters
        )

    def convert_to_framework(self, tool: Callable, target_framework: FrameworkType) -> Any:
        """Convert function to target framework."""
        if target_framework == FrameworkType.GENERIC_FUNCTION:
            return tool

        elif target_framework == FrameworkType.CREWAI and CREWAI_AVAILABLE:
            return self._convert_to_crewai(tool)

        elif target_framework == FrameworkType.OPENAI_FUNCTION:
            return self._convert_to_openai_function(tool)

        else:
            raise NotImplementedError(f"Conversion to {target_framework} not implemented")

    def validate_tool(self, tool: Any) -> bool:
        """Validate function tool."""
        return callable(tool)

    def _convert_to_crewai(self, func: Callable) -> Any:
        """Convert function to CrewAI tool."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available for conversion")

        metadata = self.extract_metadata(func)

        # Create dynamic input schema
        fields = {}
        for param_name, param_info in metadata.parameters.items():
            param_type = str
            if param_info.get("type") == "integer":
                param_type = int
            elif param_info.get("type") == "number":
                param_type = float
            elif param_info.get("type") == "boolean":
                param_type = bool

            default_value = param_info.get("default", ...)
            fields[param_name] = (param_type, Field(default=default_value, description=param_info["description"]))

        InputSchema = type(f"{func.__name__}_Input", (BaseModel,), {"__annotations__": {k: v[0] for k, v in fields.items()}})

        for name, (_, field) in fields.items():
            setattr(InputSchema, name, field)

        class ConvertedCrewAITool(CrewAITool):
            name: str = metadata.name
            description: str = metadata.description
            args_schema: Type[BaseModel] = InputSchema

            def _run(self, **kwargs) -> str:
                try:
                    result = func(**kwargs)
                    return str(result)
                except Exception as e:
                    return f"Error executing {metadata.name}: {str(e)}"

        return ConvertedCrewAITool()

    def _convert_to_openai_function(self, func: Callable) -> Dict[str, Any]:
        """Convert function to OpenAI function calling format."""
        metadata = self.extract_metadata(func)

        return {
            "name": metadata.name,
            "description": metadata.description,
            "parameters": {
                "type": "object",
                "properties": metadata.parameters,
                "required": [name for name, param in metadata.parameters.items()
                           if param.get("default") is None]
            }
        }


class UniversalToolRegistry:
    """Universal tool registry supporting multiple frameworks."""

    def __init__(self):
        """Initialize the registry."""
        self.tools: Dict[str, Any] = {}
        self.metadata: Dict[str, ToolMetadata] = {}
        self.adapters: Dict[FrameworkType, BaseToolAdapter] = {
            FrameworkType.CREWAI: CrewAIToolAdapter(),
            FrameworkType.LANGCHAIN: LangChainToolAdapter(),
            FrameworkType.GENERIC_FUNCTION: FunctionToolAdapter()
        }

    def register_tool(self, tool: Any, name: Optional[str] = None,
                     category: Optional[str] = None, tags: List[str] = None,
                     force: bool = False) -> str:
        """
        Register a tool in the registry.

        Args:
            tool: The tool to register
            name: Optional custom name for the tool
            category: Tool category
            tags: Tool tags
            force: Whether to overwrite existing tool

        Returns:
            The registered tool name

        Raises:
            ValueError: If tool is invalid or name conflicts
        """
        # Detect framework and get appropriate adapter
        adapter = self._detect_adapter(tool)
        if not adapter:
            raise ValueError(f"No suitable adapter found for tool: {tool}")

        # Extract metadata
        metadata = adapter.extract_metadata(tool)

        # Override with custom values if provided
        if name:
            metadata.name = name
        if category:
            metadata.category = category
        if tags:
            metadata.tags = tags

        # Check for conflicts
        if metadata.name in self.tools and not force:
            raise ValueError(f"Tool '{metadata.name}' already registered. Use force=True to overwrite.")

        # Register tool
        self.tools[metadata.name] = tool
        self.metadata[metadata.name] = metadata

        logger.info(f"Registered tool '{metadata.name}' from framework {metadata.framework.value}")
        return metadata.name

    def get_tool(self, name: str, target_framework: Optional[FrameworkType] = None) -> Any:
        """
        Get a tool by name, optionally converting to target framework.

        Args:
            name: Tool name
            target_framework: Target framework for conversion

        Returns:
            The tool instance

        Raises:
            KeyError: If tool not found
            NotImplementedError: If conversion not supported
        """
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found in registry")

        tool = self.tools[name]

        if target_framework is None:
            return tool

        # Convert to target framework
        source_framework = self.metadata[name].framework
        source_adapter = self.adapters[source_framework]

        return source_adapter.convert_to_framework(tool, target_framework)

    def list_tools(self, framework: Optional[FrameworkType] = None,
                   category: Optional[str] = None) -> List[ToolMetadata]:
        """
        List registered tools with optional filtering.

        Args:
            framework: Filter by framework type
            category: Filter by category

        Returns:
            List of tool metadata
        """
        tools = list(self.metadata.values())

        if framework:
            tools = [t for t in tools if t.framework == framework]

        if category:
            tools = [t for t in tools if t.category == category]

        return tools

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            name: Tool name

        Returns:
            True if removed, False if not found
        """
        if name in self.tools:
            del self.tools[name]
            del self.metadata[name]
            logger.info(f"Removed tool '{name}' from registry")
            return True
        return False

    def export_for_framework(self, framework: FrameworkType,
                           category: Optional[str] = None) -> List[Any]:
        """
        Export all tools for a specific framework.

        Args:
            framework: Target framework
            category: Optional category filter

        Returns:
            List of tools converted to target framework
        """
        tools = []
        for name, tool in self.tools.items():
            metadata = self.metadata[name]

            # Apply category filter
            if category and metadata.category != category:
                continue

            try:
                converted_tool = self.get_tool(name, framework)
                tools.append(converted_tool)
            except Exception as e:
                logger.warning(f"Failed to convert tool '{name}' to {framework.value}: {e}")

        return tools

    def _detect_adapter(self, tool: Any) -> Optional[BaseToolAdapter]:
        """Detect the appropriate adapter for a tool."""
        for adapter in self.adapters.values():
            if adapter.validate_tool(tool):
                return adapter
        return None

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        framework_counts = {}
        category_counts = {}

        for metadata in self.metadata.values():
            framework = metadata.framework.value
            framework_counts[framework] = framework_counts.get(framework, 0) + 1

            category = metadata.category or "uncategorized"
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_tools": len(self.tools),
            "frameworks": framework_counts,
            "categories": category_counts,
            "available_frameworks": {
                "crewai": CREWAI_AVAILABLE,
                "langchain": LANGCHAIN_AVAILABLE,
                "openai": OPENAI_AVAILABLE
            }
        }


# Global registry instance
global_tool_registry = UniversalToolRegistry()


# Convenience functions for registration
def register_tool(tool: Any, name: Optional[str] = None,
                 category: Optional[str] = None, tags: List[str] = None,
                 force: bool = False) -> str:
    """Register a tool in the global registry."""
    return global_tool_registry.register_tool(tool, name, category, tags, force)


def get_tool(name: str, target_framework: Optional[FrameworkType] = None) -> Any:
    """Get a tool from the global registry."""
    return global_tool_registry.get_tool(name, target_framework)


def list_tools(framework: Optional[FrameworkType] = None,
               category: Optional[str] = None) -> List[ToolMetadata]:
    """List tools in the global registry."""
    return global_tool_registry.list_tools(framework, category)