import json
from langchain.pydantic_v1 import ValidationError
from crewai.agents.tools_handler import ToolsHandler
from crewai.tools.tool_usage import ToolUsage
from crewai.utilities.printer import Printer

class CustomToolsHandler(ToolsHandler):
    """
    A custom tools handler that catches Pydantic validation errors
    and returns a more helpful, human-readable error message to the agent,
    guiding it to correct its own mistakes.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._printer = Printer()

    def execute(self, tool_usage: ToolUsage):
        """
        Executes a tool usage, catching validation errors and providing
        clearer feedback to the agent.
        """
        try:
            # Attempt to execute the tool as normal
            return super().execute(tool_usage)
        except ValidationError as e:
            # If a validation error occurs, craft a more helpful message
            error_message = (
                "Error: Your input was invalid. You must provide simple strings for the arguments. "
                "Please review the tool's arguments and rewrite your Action Input with plain strings."
                f"\nDetails of the error: {e}"
            )
            # Print the helpful error and return it as the observation
            self._printer.print(text=error_message, color="red")
            return error_message
