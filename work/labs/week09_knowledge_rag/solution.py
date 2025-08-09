import sys
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool

# --- 環境設定 ---
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    print(f"⚠️  警告：未找到 pysqlite3，將使用系統內建的 SQLite 版本: {sqlite3.sqlite_version}。")

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

def run_rag_query(question: str):
    """
    接收一個問題，並驅動 RAG Agent 來尋找答案。

    Args:
        question (str): 使用者輸入的問題。

    Returns:
        str: Agent 執行的最終結果。
    """
    # --- RAG 工具設定 ---
    # 建立一個 FileReadTool，讓 Agent 能夠直接讀取指定的檔案
    knowledge_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'crewai_features.txt'))
    file_read_tool = FileReadTool(file_path=knowledge_file_path)

    # --- Agent 定義 ---
    rag_agent = Agent(
        role="CrewAI 專家",
        goal="根據提供的文件，準確回答關於 CrewAI 功能的問題。",
        backstory="你是一位 AI 助理，唯一的工作就是深入理解並解釋你工具中的文件內容。絕不使用外部知識。",
        tools=[file_read_tool],  # 將 FileReadTool 賦予 Agent
        verbose=True
    )

    # --- Task 定義 (動態生成) ---
    # 將使用者的問題動態地整合進 description 中
    task = Task(
        description=f"""你擁有一個可以讀取 '{knowledge_file_path}' 內容的工具。
        請使用這個工具來回答以下使用者問題：

        ---
        使用者問題: "{question}"
        ---

        你的回答必須完全基於所提供文件的內容。""",
        expected_output=f"針對 '{question}' 的清晰、準確、完全基於文件的回答。",
        agent=rag_agent
    )

    # --- Crew 建立與執行 ---
    crew = Crew(
        agents=[rag_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return result

if __name__ == "__main__":
    # 模擬第一次聊天輸入
    user_question_1 = "What is the process control feature in CrewAI?"
    print(f"--- 正在查詢問題 1: {user_question_1} ---")
    final_result_1 = run_rag_query(user_question_1)
    print("\n--- 最終結果 1 ---")
    print(final_result_1)

    print("\n" + "="*50 + "\n")

    # 模擬第二次聊天輸入
    user_question_2 = "Tell me about Tool Integration."
    print(f"--- 正在查詢問題 2: {user_question_2} ---")
    final_result_2 = run_rag_query(user_question_2)
    print("\n--- 最終結果 2 ---")
    print(final_result_2)
