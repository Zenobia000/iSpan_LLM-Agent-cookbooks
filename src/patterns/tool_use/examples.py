# src/patterns/tool_use/examples.py

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel, Field

# Import our tool framework
from .decorators import tool, async_tool, robust_tool, cached_tool, quick_tool, ToolBuilder
from .registry import register_tool, get_tool, FrameworkType, global_tool_registry


# ========================================
# Example 1: Simple Function Tools
# ========================================

@quick_tool(name="calculator", description="Perform basic mathematical calculations")
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

    Returns:
        String containing the result
    """
    try:
        # Simple eval - in production, use a safer expression evaluator
        allowed_chars = set('0123456789+-*/().,= ')
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"Result: {result}"
        else:
            return "Error: Expression contains invalid characters"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@cached_tool(ttl=600, category="utilities")
def current_time(timezone: str = "UTC") -> str:
    """
    Get current time in specified timezone.

    Args:
        timezone: Timezone (e.g., "UTC", "EST", "PST")

    Returns:
        Current time string
    """
    import datetime

    # Simplified timezone handling
    time_obj = datetime.datetime.now()
    return f"Current time ({timezone}): {time_obj.strftime('%Y-%m-%d %H:%M:%S')}"


# ========================================
# Example 2: API Integration Tools
# ========================================

class WeatherToolInput(BaseModel):
    """Input schema for weather tool."""
    city: str = Field(..., description="City name to get weather for")
    country_code: Optional[str] = Field(default=None, description="Optional country code (e.g., 'US', 'UK')")


@robust_tool(retries=3, delay=1.0, timeout=10.0, category="api")
def weather_lookup(city: str, country_code: Optional[str] = None) -> str:
    """
    Get weather information for a city using a weather API.

    Args:
        city: City name
        country_code: Optional country code

    Returns:
        Weather information string
    """
    # This is a mock implementation - replace with actual API
    location = f"{city}, {country_code}" if country_code else city

    # Simulate API delay and potential failure
    time.sleep(0.5)

    # Mock response
    mock_weather = {
        "temperature": "22°C",
        "condition": "Sunny",
        "humidity": "65%",
        "wind": "10 km/h"
    }

    return f"Weather in {location}: {mock_weather['temperature']}, {mock_weather['condition']}, Humidity: {mock_weather['humidity']}, Wind: {mock_weather['wind']}"


# ========================================
# Example 3: File Operations Tools
# ========================================

@tool(name="read_file", description="Read contents of a text file", category="file_operations")
def read_file(filepath: str, encoding: str = "utf-8") -> str:
    """
    Read contents of a text file.

    Args:
        filepath: Path to the file
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' does not exist"

        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()

        return f"File content:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool(name="write_file",
      description="Write content to a text file",
      category="file_operations",
      tags=["file", "write", "io"],
      retry_attempts=2)
def write_file(filepath: str, content: str, encoding: str = "utf-8") -> str:
    """
    Write content to a text file.

    Args:
        filepath: Path where to write the file
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        Success or error message
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

        return f"Successfully wrote {len(content)} characters to '{filepath}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


# ========================================
# Example 4: Data Processing Tools
# ========================================

@(ToolBuilder()
  .name("json_processor")
  .description("Process and validate JSON data")
  .category("data")
  .tags("json", "validation", "processing")
  .retry(2, 0.5)
  .cache(True, 300)
  .build())
def process_json(json_string: str, operation: str = "validate") -> str:
    """
    Process JSON data with various operations.

    Args:
        json_string: JSON string to process
        operation: Operation to perform ("validate", "prettify", "minify", "keys")

    Returns:
        Processed result
    """
    try:
        data = json.loads(json_string)

        if operation == "validate":
            return "JSON is valid"
        elif operation == "prettify":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif operation == "minify":
            return json.dumps(data, separators=(',', ':'))
        elif operation == "keys":
            if isinstance(data, dict):
                return f"Keys: {list(data.keys())}"
            else:
                return "Not a JSON object - no keys available"
        else:
            return f"Unknown operation: {operation}"

    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"Error processing JSON: {str(e)}"


# ========================================
# Example 5: Custom CrewAI Tool
# ========================================

try:
    from crewai.tools import BaseTool

    class TextAnalyzerInput(BaseModel):
        text: str = Field(..., description="Text to analyze")
        analysis_type: str = Field(default="summary", description="Type of analysis: summary, sentiment, keywords")

    class TextAnalyzerTool(BaseTool):
        name: str = "text_analyzer"
        description: str = "Analyze text for various insights including sentiment, keywords, and summary"
        args_schema: Type[BaseModel] = TextAnalyzerInput

        def _run(self, text: str, analysis_type: str = "summary") -> str:
            """Analyze text and return insights."""
            try:
                word_count = len(text.split())
                char_count = len(text)

                if analysis_type == "summary":
                    return f"Text Analysis Summary:\n- Word count: {word_count}\n- Character count: {char_count}\n- First 100 chars: {text[:100]}..."

                elif analysis_type == "sentiment":
                    # Mock sentiment analysis
                    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
                    negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]

                    text_lower = text.lower()
                    positive_count = sum(1 for word in positive_words if word in text_lower)
                    negative_count = sum(1 for word in negative_words if word in text_lower)

                    if positive_count > negative_count:
                        sentiment = "Positive"
                    elif negative_count > positive_count:
                        sentiment = "Negative"
                    else:
                        sentiment = "Neutral"

                    return f"Sentiment Analysis: {sentiment} (Positive words: {positive_count}, Negative words: {negative_count})"

                elif analysis_type == "keywords":
                    # Simple keyword extraction
                    words = text.lower().split()
                    word_freq = {}
                    for word in words:
                        word = word.strip('.,!?";')
                        if len(word) > 3:  # Only words longer than 3 characters
                            word_freq[word] = word_freq.get(word, 0) + 1

                    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                    keywords = [word for word, _ in top_words]

                    return f"Top Keywords: {', '.join(keywords)}"

                else:
                    return f"Unknown analysis type: {analysis_type}"

            except Exception as e:
                return f"Error analyzing text: {str(e)}"

except ImportError:
    # CrewAI not available
    print("CrewAI not available - skipping CrewAI tool example")


# ========================================
# Tool Registration Examples
# ========================================

def register_example_tools():
    """Register all example tools in the global registry."""

    # The decorated tools are already auto-registered
    print("Auto-registered tools:")
    tools = global_tool_registry.list_tools()
    for tool_meta in tools:
        print(f"- {tool_meta.name} ({tool_meta.framework.value})")

    # Manually register the CrewAI tool if available
    try:
        if 'TextAnalyzerTool' in locals():
            text_analyzer = TextAnalyzerTool()
            register_tool(text_analyzer, category="text_processing", tags=["nlp", "analysis"])
            print(f"Manually registered: TextAnalyzerTool")
    except Exception as e:
        print(f"Failed to register TextAnalyzerTool: {e}")


def demonstrate_framework_conversion():
    """Demonstrate cross-framework tool conversion."""
    print("\n" + "="*50)
    print("FRAMEWORK CONVERSION DEMONSTRATION")
    print("="*50)

    # Get a tool in different framework formats
    calculator_tool = get_tool("calculator")
    print(f"Original tool: {type(calculator_tool).__name__}")

    # Convert to OpenAI function format
    try:
        openai_format = get_tool("calculator", FrameworkType.OPENAI_FUNCTION)
        print(f"OpenAI format: {json.dumps(openai_format, indent=2)}")
    except Exception as e:
        print(f"OpenAI conversion failed: {e}")

    # Convert to CrewAI format (if available)
    try:
        crewai_format = get_tool("calculator", FrameworkType.CREWAI)
        print(f"CrewAI format: {type(crewai_format).__name__}")
    except Exception as e:
        print(f"CrewAI conversion failed: {e}")


def tool_performance_demo():
    """Demonstrate tool performance features."""
    print("\n" + "="*50)
    print("TOOL PERFORMANCE DEMONSTRATION")
    print("="*50)

    # Test caching
    print("Testing cached tool (should be fast on second call):")

    start_time = time.time()
    result1 = current_time("UTC")
    time1 = time.time() - start_time
    print(f"First call: {result1} (took {time1:.3f}s)")

    start_time = time.time()
    result2 = current_time("UTC")
    time2 = time.time() - start_time
    print(f"Second call: {result2} (took {time2:.3f}s)")

    # Test robust tool with retries
    print("\nTesting robust tool with error handling:")
    try:
        result = weather_lookup("TestCity", "XX")
        print(f"Weather result: {result}")
    except Exception as e:
        print(f"Weather tool error: {e}")


def main():
    """Main demonstration function."""
    print("Universal Tool Registry - Examples and Demonstrations")
    print("="*60)

    # Register all example tools
    register_example_tools()

    # Show registry statistics
    print(f"\nRegistry Stats: {global_tool_registry.get_registry_stats()}")

    # Test some tools
    print("\n" + "="*50)
    print("TOOL EXECUTION EXAMPLES")
    print("="*50)

    # Test calculator
    calc_result = calculator("2 + 3 * 4")
    print(f"Calculator: {calc_result}")

    # Test JSON processor
    json_result = process_json('{"name": "test", "value": 123}', "prettify")
    print(f"JSON Processor: {json_result}")

    # Test file operations
    file_result = write_file("/tmp/test.txt", "Hello, World!")
    print(f"File Write: {file_result}")

    read_result = read_file("/tmp/test.txt")
    print(f"File Read: {read_result}")

    # Demonstrate conversions
    demonstrate_framework_conversion()

    # Performance demonstrations
    tool_performance_demo()


if __name__ == "__main__":
    main()