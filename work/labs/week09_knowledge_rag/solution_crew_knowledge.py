import sys
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

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

# --- 最新 Crew-Level Knowledge 範例 ---

def run_crew_level_rag(question: str):
    """
    使用 crewai 最新的 Crew-Level Knowledge 功能來執行 RAG 查詢。

    Args:
        question (str): 使用者輸入的問題。

    Returns:
        str: Agent 執行的最終結果。
    """
    # 1. 建立知識源 (Source)
    #    根據官方文件建議，直接提供相對於根目錄/knowledge 的檔案名稱。
    #    crewai 會自動在 `./knowledge/` 資料夾下尋找此檔案。
    text_file_source = TextFileKnowledgeSource(file_paths=['crewai_features.txt'])

    # 2. 建立 Agent
    #    Agent 不需要任何 knowledge 參數。
    knowledge_agent = Agent(
        role="CrewAI 框架專家",
        goal="根據你所屬 Crew 提供的知識庫，精確地回答關於 CrewAI 功能的問題。",
        backstory="你是一位 AI 助理，能存取整個團隊共享的知識。絕不使用外部知識或進行猜測。",
        verbose=True
    )

    # 3. 定義任務
    #    Prompt 引導 Agent 使用其團隊的知識庫。
    task = Task(
        description=f"""請利用你 Crew 的共享知識庫來回答以下使用者問題：

        ---
        使用者問題: "{question}"
        ---

        你的回答必須完全基於所提供知識庫的內容。""",
        expected_output=f"針對 '{question}' 的清晰、準確、完全基於知識庫的回答。",
        agent=knowledge_agent
    )

    # 4. 建立 Crew 並賦予知識
    #    在 Crew 初始化時，透過 `knowledge_sources` 參數傳入知識源。
    crew = Crew(
        agents=[knowledge_agent],
        tasks=[task],
        process=Process.sequential,
        knowledge_sources=[text_file_source], # 在此處賦予 Crew 知識
        verbose=True
    )

    result = crew.kickoff()
    return result

if __name__ == "__main__":
    user_question = "According to the document, what is the 'Crew Composition' feature?"
    print(f"--- 正在查詢問題: {user_question} ---")
    final_result = run_crew_level_rag(user_question)
    print("\n--- 最終結果 ---")
    print(final_result)
