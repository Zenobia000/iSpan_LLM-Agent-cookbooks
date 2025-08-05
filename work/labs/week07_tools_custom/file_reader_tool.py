import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class FileReaderInput(BaseModel):
    """Input schema for FileReaderTool."""
    file_path: str = Field(..., description="The absolute path to the file to be read.")

class FileReaderTool(BaseTool):
    name: str = "FileReaderTool"
    description: str = "Reads the content of a local file. Use this when you need to access information stored in a file."
    args_schema: Type[BaseModel] = FileReaderInput

    def _run(self, file_path: str) -> str:
        try:
            # Ensure the path is absolute, as relative paths can be ambiguous.
            if not os.path.isabs(file_path):
                return f"Error: Please provide an absolute file path. '{file_path}' is not an absolute path."

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content

        except FileNotFoundError:
            return f"Error: The file '{file_path}' was not found."
        except PermissionError:
            return f"Error: Permission denied to read the file '{file_path}'."
        except Exception as e:
            return f"An unexpected error occurred while reading the file: {e}"
