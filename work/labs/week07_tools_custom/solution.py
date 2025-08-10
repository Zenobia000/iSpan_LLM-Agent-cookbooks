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
# 修正導入路徑，同時導入 Class-based 和 Function-based 工具
from work.labs.week07_tools_custom.file_reader_tool import FileReaderTool, read_file_content


# 1. 實例化 Class-based 工具
class_based_tool = FileReaderTool()

# 2. Function-based 工具可以直接使用
function_based_tool = read_file_content

# --- Crew 1: 使用 Class-based Tool ---

# 3. 建立使用 Class-based 工具的 Agent
agent_class_based = Agent(
    role="File Reading Specialist (Class-based)",
    goal="Read the content of a specified file and provide a summary in bullet points.",
    backstory="You are an expert at quickly reading and extracting key information from text files using class-based tools.",
    tools=[class_based_tool],
    llm=ChatOpenAI(model_name="gpt-4o"),
    verbose=True
)

# --- Crew 2: 使用 Function-based Tool ---

# 4. 建立使用 Function-based 工具的 Agent
agent_function_based = Agent(
    role="File Reading Specialist (Function-based)",
    goal="Read the content of a specified file and provide a summary in bullet points.",
    backstory="You are an expert at quickly reading and extracting key information from text files using function-based tools.",
    tools=[function_based_tool],
    llm=ChatOpenAI(model_name="gpt-4o"),
    verbose=True
)


# 5. 為兩個 Agent 建立共同的 Task
# 動態構建檔案的絕對路徑以確保可移植性
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sample_data.txt'))

task_template = Task(
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
    expected_output="A concise summary of the file's content, formatted as a professional report with five distinct sections."
)

# 6. 為每個 Agent 指派 Task
task_class_based = task_template
task_class_based.agent = agent_class_based

task_function_based = task_template
task_function_based.agent = agent_function_based


# 7. 建立並執行兩個 Crew
crew_class_based = Crew(
    agents=[agent_class_based],
    tasks=[task_class_based],
    process=Process.sequential,
    verbose=True
)

crew_function_based = Crew(
    agents=[agent_function_based],
    tasks=[task_function_based],
    process=Process.sequential,
    verbose=True
)


if __name__ == "__main__":
    print("--- 🚀 Starting Crew with Class-based Tool ---")
    result_class_based = crew_class_based.kickoff()
    print("\n\n--- ✅ Final Result (Class-based) ---")
    print(result_class_based)

    print("\n" + "="*50 + "\n")

    print("--- 🚀 Starting Crew with Function-based Tool ---")
    result_function_based = crew_function_based.kickoff()
    print("\n\n--- ✅ Final Result (Function-based) ---")
    print(result_function_based)

