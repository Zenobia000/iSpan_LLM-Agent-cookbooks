import json
from langchain.pydantic_v1 import ValidationError
from crewai.agents.tools_handler import ToolsHandler
from crewai.tools.tool_usage import ToolUsage
from crewai.utilities.printer import Printer
try:
    from .opik_config import log_agent_metrics, log_cost_metrics, OpikTrace
except ImportError:
    # Fallback if opik is not available
    def log_agent_metrics(agent_name: str, metrics: dict):
        print(f"📊 Metrics for {agent_name}: {metrics}")

    def log_cost_metrics(operation: str, cost: float, tokens_used: int = None):
        print(f"💰 Cost for {operation}: ${cost:.4f}")

    class OpikTrace:
        def __init__(self, name: str, tags=None):
            self.name = name
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def log_message(self, message: str, level: str = "info"):
            print(f"📝 {self.name}: {message}")
import time

class CustomToolsHandler(ToolsHandler):
    """
    A custom tools handler that integrates with Opik for observability.
    It catches Pydantic validation errors, provides helpful error messages,
    and tracks tool usage metrics with Opik for monitoring and analysis.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._printer = Printer()
        self._tool_usage_count = 0
        self._total_execution_time = 0.0

    def execute(self, tool_usage: ToolUsage):
        """
        Executes a tool usage with Opik tracking, catching validation errors
        and providing clearer feedback to the agent.
        """
        start_time = time.time()
        tool_name = getattr(tool_usage.tool, 'name', str(type(tool_usage.tool).__name__))

        with OpikTrace(f"tool_execution_{tool_name}", tags=["tool", "crewai"]) as trace:
            try:
                # Track tool usage start
                trace.log_message(f"Starting execution of tool: {tool_name}")
                trace.log_message(f"Tool arguments: {tool_usage.arguments}")

                # Attempt to execute the tool as normal
                result = super().execute(tool_usage)

                # Calculate execution time
                execution_time = time.time() - start_time
                self._tool_usage_count += 1
                self._total_execution_time += execution_time

                # Log success metrics
                log_agent_metrics("tools_handler", {
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "status": "success",
                    "usage_count": self._tool_usage_count
                })

                trace.log_message(f"Tool execution completed successfully in {execution_time:.2f}s")
                self._printer.print(text=f"✅ Tool {tool_name} executed successfully", color="green")

                return result

            except ValidationError as e:
                # Calculate execution time even on error
                execution_time = time.time() - start_time

                # If a validation error occurs, craft a more helpful message
                error_message = (
                    "Error: Your input was invalid. You must provide simple strings for the arguments. "
                    "Please review the tool's arguments and rewrite your Action Input with plain strings."
                    f"\nDetails of the error: {e}"
                )

                # Log error metrics
                log_agent_metrics("tools_handler", {
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "status": "validation_error",
                    "error_type": "ValidationError",
                    "error_message": str(e)
                })

                trace.log_message(f"Validation error in tool {tool_name}: {str(e)}", level="error")

                # Print the helpful error and return it as the observation
                self._printer.print(text=error_message, color="red")
                return error_message

            except Exception as e:
                # Handle other exceptions
                execution_time = time.time() - start_time

                error_message = f"Unexpected error executing tool {tool_name}: {str(e)}"

                # Log error metrics
                log_agent_metrics("tools_handler", {
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })

                trace.log_message(f"Error executing tool {tool_name}: {str(e)}", level="error")
                self._printer.print(text=error_message, color="red")

                raise

    def get_usage_stats(self):
        """
        Get tool usage statistics for monitoring
        """
        return {
            "total_tool_executions": self._tool_usage_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": self._total_execution_time / max(self._tool_usage_count, 1)
        }
