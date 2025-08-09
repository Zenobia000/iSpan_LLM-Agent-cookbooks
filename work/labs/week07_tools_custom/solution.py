import sys

from langchain_openai import ChatOpenAI
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")

import os
from dotenv import load_dotenv

# To handle imports from the root of the project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from work.labs.week07_tools_custom.file_reader_tool import FileReaderTool


# 1. Instantiate the custom tool
file_reader_tool = FileReaderTool()

# 2. Create an Agent that uses the tool
file_reading_agent = Agent(
    role="File Reading Specialist",
    goal="Read the content of a specified file and provide a summary in bullet points with TOFEL format.",
    backstory="You are an expert at quickly reading and extracting key information from text files.",
    tools=[file_reader_tool],
    llm=ChatOpenAI(model_name="gpt-4o"),
    verbose=True
)

# 3. Create a Task for the Agent
# Note: We construct the absolute path to the file dynamically to ensure portability.
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sample_data.txt'))

read_file_task = Task(
    description=f"""Please assume the role of a senior professional writer and read the document located at “{file_path}.” Then, produce a structured, clear, and concise summary report following the five-section framework below:

1. **Introduction**  
   – Briefly state the document’s topic and purpose  
   – Highlight the core question or angle the summary will address

2. **Background & Context**  
   – Describe relevant history or background information  
   – Identify the key factors influencing the topic

3. **Key Points**  
   – List and elaborate on the document’s main arguments  
   – Use subheadings for each point and provide a concise explanation

4. **In-Depth Analysis**  
   – Offer insights on the significance and impact of each point  
   – Integrate any data, case studies, or citations as appropriate

5. **Conclusion & Recommendations**  
   – Recap the main findings  
   – Offer actionable suggestions or directions for further consideration
""",
    expected_output="A concise summary of the file's content in bullet points with TOFEL format.",
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
