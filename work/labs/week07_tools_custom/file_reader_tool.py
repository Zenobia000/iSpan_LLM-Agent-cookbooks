import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool, tool

class FileReaderInput(BaseModel):
    """Input schema for FileReaderTool."""
    file_path: str = Field(..., description="The absolute path to the file to be read.")

class FileReaderTool(BaseTool):
    name: str = "FileReaderTool (Class-based)"
    description: str = "Reads the content of a local file using a class-based approach. Use this when you need to access information stored in a file."
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

@tool("FileReaderTool (Decorator-based)")
def read_file_content(file_path: str) -> str:
    """
    Reads the content of a local file using a decorator-based approach.
    Use this when you need to access information stored in a file.
    The input MUST be an absolute file path.
    """
    try:
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
