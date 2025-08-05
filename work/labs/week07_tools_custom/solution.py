import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")
sys.path.append('/home/os-sunnie.gd.weng/python_workstation/side_project/crewai_system')

import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, Task, Crew, Process
from work.labs.week07_tools_custom.file_reader_tool import FileReaderTool

# 1. Instantiate the custom tool
file_reader_tool = FileReaderTool()

# 2. Create an Agent that uses the tool
file_reading_agent = Agent(
    role="File Reading Specialist",
    goal="Read the content of a specified file and provide a summary.",
    backstory="You are an expert at quickly reading and extracting key information from text files.",
    tools=[file_reader_tool],
    verbose=True
)

# 3. Create a Task for the Agent
# Note: We provide the absolute path to the file in the task description.
file_path = "/home/os-sunnie.gd.weng/python_workstation/side_project/crewai_system/work/labs/week07_tools_custom/sample_data.txt"

read_file_task = Task(
    description=f"Read the content of the file located at '{file_path}' and summarize its main points.",
    expected_output="A concise summary of the file's content.",
    agent=file_reading_agent
)

# 4. Create and run the Crew
crew = Crew(
    agents=[file_reading_agent],
    tasks=[read_file_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n--- Final Result ---")
    print(result)
