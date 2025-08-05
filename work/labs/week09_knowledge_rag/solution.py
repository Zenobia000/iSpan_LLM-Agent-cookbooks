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
from crewai.knowledge.knowledge import Knowledge

# 1. Create the Knowledge Base
knowledge_base = Knowledge(collection_name="crewai_features_collection", sources=['/home/os-sunnie.gd.weng/python_workstation/side_project/crewai_system/work/labs/week09_knowledge_rag/crewai_features.txt'])

# 2. Create an Agent with the Knowledge Base
rag_agent = Agent(
    role="CrewAI Expert",
    goal="Answer questions about CrewAI's features based on the provided knowledge base.",
    backstory="You are an AI assistant with deep knowledge of the CrewAI framework.",
    knowledge_base=knowledge_base,
    verbose=True
)

# 3. Create a Task for the Agent
task = Task(
    description="What is the process control feature in CrewAI?",
    expected_output="A clear explanation of the process control feature.",
    agent=rag_agent
)

# 4. Create and run the Crew
crew = Crew(
    agents=[rag_agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n--- Final Result ---")
    print(result)
