# src/templates/tool_template.py

import os
import requests
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# --- 1. Input Schema (Pydantic Model) ---
# Define the expected inputs for your tool. This ensures data validation.
class MyToolInput(BaseModel):
    """Input schema for MyTool. Provides validation and clear descriptions for the Agent."""
    required_parameter: str = Field(..., description="A parameter that is absolutely necessary for the tool to function.")
    optional_parameter: Optional[int] = Field(default=None, description="An optional parameter that can modify the tool's behavior.")

# --- 2. Tool Implementation (BaseTool) ---
class MyCustomTool(BaseTool):
    """
    A template for creating robust and reliable custom tools for CrewAI.
    This template incorporates best practices for input validation, error handling,
    and providing clear feedback to the Agent.
    """
    name: str = "My Custom Tool"
    description: str = "A brief, clear description of what this tool does and when an Agent should use it."
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, required_parameter: str, optional_parameter: Optional[int] = None) -> str:
        """
        The main execution logic of the tool.
        It uses the validated parameters to perform its task.
        """
        try:
            # --- Main Tool Logic ---
            # Replace this with your actual tool's functionality.
            # For example, making an API call, reading a file, or performing a calculation.
            print(f"Executing MyCustomTool with:")
            print(f"  Required Parameter: {required_parameter}")
            print(f"  Optional Parameter: {optional_parameter}")

            # Simulating an API call
            # api_key = os.getenv("MY_API_KEY")
            # if not api_key:
            #     return "Error: MY_API_KEY not found in environment variables."
            # 
            # response = requests.get(
            #     f"https://api.example.com/data?param={required_parameter}",
            #     headers={"Authorization": f"Bearer {api_key}"}
            # )
            # response.raise_for_status() # Raises an exception for 4xx/5xx errors
            # data = response.json()

            # --- Success Case ---
            # Return a clear, informative result to the Agent.
            return f"Successfully executed the tool with '{required_parameter}'. Result: [Simulated Data]"

        # --- Error Handling ---
        # Catch specific, expected errors first.
        # except requests.exceptions.HTTPError as http_err:
        #     response = http_err.response
        #     if response.status_code == 401:
        #         return "Error: Authentication failed. Please check your API key."
        #     elif response.status_code == 404:
        #         return f"Error: Resource not found for parameter '{required_parameter}'."
        #     elif response.status_code == 429:
        #         return "Error: API rate limit exceeded. Please try again later."
        #     else:
        #         return f"Error: An HTTP error occurred: {http_err}"
        # 
        # except requests.exceptions.RequestException as req_err:
        #     return f"Error: A network error occurred: {req_err}. Please check your connection and try again."

        # Catch any other unexpected errors.
        except Exception as e:
            # Provide a general but informative error message to the Agent.
            return f"An unexpected error occurred while executing the tool: {e}. Please review the inputs or try a different approach."

# --- 3. Example Usage (for testing) ---
if __name__ == "__main__":
    # This block allows you to test the tool directly.
    tool = MyCustomTool()

    # Test Case 1: Successful execution
    print("--- Test Case 1: Successful Execution ---")
    result1 = tool._run(
        required_parameter="test_value",
        optional_parameter=123
    )
    print(f"Result: {result1}\n")

    # Test Case 2: Missing required parameter (will be caught by Pydantic before _run is called)
    print("--- Test Case 2: Missing Required Parameter ---")
    try:
        # In a real Crew, the Agent would get this validation error.
        MyToolInput(optional_parameter=456) # Missing required_parameter
    except Exception as e:
        print(f"Caught expected validation error: {e}\n")
