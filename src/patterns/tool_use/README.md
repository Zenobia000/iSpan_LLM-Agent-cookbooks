# Universal Tool Framework for Multi-Agent Systems

## 🎯 Overview

This framework provides a comprehensive solution for creating, registering, and managing tools across different AI frameworks. It enables seamless interoperability between CrewAI, LangChain, OpenAI Functions, and custom Python functions.

## 🚀 Key Features

### 🔄 Cross-Framework Compatibility
- **Universal Registry**: Central registry supporting multiple frameworks
- **Automatic Conversion**: Convert tools between frameworks automatically
- **Framework Detection**: Intelligent framework detection and adapter selection

### 🛠️ Enhanced Tool Creation
- **Decorators**: Rich set of decorators for tool enhancement
- **Validation**: Comprehensive tool validation and testing
- **Performance**: Built-in caching, retries, and timeout handling

### 📊 Monitoring & Analytics
- **Performance Metrics**: Execution time, success rate, error tracking
- **Validation Reports**: Detailed tool quality assessment
- **Testing Framework**: Automated tool testing and validation

## 📦 Quick Start

### Basic Tool Creation

```python
from src.patterns.tool_use import tool, register_tool

@tool(name="calculator", description="Perform calculations", category="math")
def calculator(expression: str) -> str:
    """Calculate mathematical expressions."""
    try:
        result = eval(expression)  # Use safer eval in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Tool is automatically registered
```

### Advanced Tool with Features

```python
from src.patterns.tool_use import robust_tool, ToolBuilder

# Using decorator
@robust_tool(retries=3, delay=1.0, cache=True, timeout=10.0)
def weather_api(city: str) -> str:
    """Get weather information for a city."""
    # Your implementation here
    pass

# Using builder pattern
advanced_tool = (ToolBuilder()
    .name("data_processor")
    .description("Process and analyze data")
    .category("data")
    .tags("processing", "analysis")
    .retry(3, 0.5)
    .cache(True, 300)
    .timeout(30.0)
    .build())

@advanced_tool
def process_data(data: str, format: str = "json") -> str:
    """Process data in various formats."""
    # Your implementation here
    pass
```

## 🔧 Framework Integration

### CrewAI Integration

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from src.patterns.tool_use import register_tool

class MyToolInput(BaseModel):
    query: str = Field(..., description="Search query")

class MyCrewAITool(BaseTool):
    name: str = "search_tool"
    description: str = "Search for information"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, query: str) -> str:
        return f"Search results for: {query}"

# Register the CrewAI tool
tool_instance = MyCrewAITool()
register_tool(tool_instance, category="search")
```

### Cross-Framework Conversion

```python
from src.patterns.tool_use import get_tool, FrameworkType

# Get tool in different formats
original_tool = get_tool("calculator")  # Original format
openai_format = get_tool("calculator", FrameworkType.OPENAI_FUNCTION)
crewai_format = get_tool("calculator", FrameworkType.CREWAI)

# OpenAI format example
print(openai_format)
# Output:
# {
#   "name": "calculator",
#   "description": "Perform calculations",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "expression": {"type": "string", "description": "Mathematical expression"}
#     },
#     "required": ["expression"]
#   }
# }
```

## 🧪 Testing & Validation

### Tool Validation

```python
from src.patterns.tool_use import ToolValidator

validator = ToolValidator()

# Validate a tool
result = validator.validate_tool(calculator, "calculator")
print(f"Valid: {result.is_valid}")
print(f"Score: {result.score}/10")
print(f"Issues: {result.issues}")
print(f"Warnings: {result.warnings}")

# Get improvement recommendations
recommendations = validator.get_recommendations("calculator")
for rec in recommendations:
    print(f"- {rec}")
```

## 🎯 Best Practices

### 1. Tool Design
- **Single Responsibility**: Each tool should have a clear, single purpose
- **Clear Documentation**: Provide comprehensive docstrings
- **Type Hints**: Use type hints for all parameters
- **Error Handling**: Implement proper error handling and return informative messages

### 2. Performance
- **Use Caching**: Enable caching for expensive operations
- **Set Timeouts**: Always set reasonable timeouts for external calls
- **Implement Retries**: Use robust_tool for unreliable operations

### 3. Testing
- **Validate All Tools**: Use ToolValidator for quality assurance
- **Performance Test**: Test tools under load
- **Integration Test**: Test framework conversions

## 📚 Examples

See `examples.py` for comprehensive usage examples including:
- Basic function tools
- API integration tools
- File operation tools
- Data processing tools
- CrewAI tool integration
- Performance demonstrations