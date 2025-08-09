import sys
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.knowledge_config import KnowledgeConfig

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

# --- 進階微調 Crew-Level Knowledge 範例 ---

def run_tuned_rag_query(question: str):
    """
    使用 crewai 最新的 Crew-Level Knowledge 功能，並展示如何微調各項參數。

    Args:
        question (str): 使用者輸入的問題。

    Returns:
        str: Agent 執行的最終結果。
    """
    # 1. 建立知識源 (Source) 並微調 Chunking 參數
    text_file_source = TextFileKnowledgeSource(
        file_paths=['crewai_features.txt'],
        chunk_size=200,      # 微調參數：設定每個文本區塊的最大長度為 200 字元
        chunk_overlap=50     # 微調參數：設定區塊之間的重疊為 50 字元，以保持上下文連貫
    )

    # 2. 定義檢索參數 (Retrieval)
    knowledge_config = KnowledgeConfig(
        results_limit=2,     # 微調參數：限制只返回最相關的 2 個文本區塊
        score_threshold=0.5, # 微調參數：設定相似度分數門檻為 0.5
    )

    # 3. 建立 Agent
    knowledge_agent = Agent(
        role="CrewAI 框架專家",
        goal="根據你所屬 Crew 提供的知識庫，精確地回答關於 CrewAI 功能的問題。",
        backstory="你是一位 AI 助理，能存取整個團隊共享的知識。絕不使用外部知識或進行猜測。",
        verbose=True
    )

    # 4. 定義任務
    task = Task(
        description=f"""請利用你 Crew 的共享知識庫來回答以下使用者問題：

        ---
        使用者問題: "{question}"
        ---

        你的回答必須完全基於所提供知識庫的內容。""",
        expected_output=f"針對 '{question}' 的清晰、準確、完全基於知識庫的回答。",
        agent=knowledge_agent
    )

    # 5. 建立 Crew 並賦予知識與微調參數
    crew = Crew(
        agents=[knowledge_agent],
        tasks=[task],
        process=Process.sequential,
        knowledge_sources=[text_file_source],
        knowledge_config=knowledge_config, # 傳入檢索參數
        # embedder={ # 微調參數：指定嵌入模型提供者 (此處為範例，需有對應環境)
        #     "provider": "ollama",
        #     "config": {
        #         "model": "mxbai-embed-large",
        #         "url": "http://localhost:11434/api/embeddings"
        #     }
        # },
        verbose=True
    )

    result = crew.kickoff()
    return result

if __name__ == "__main__":
    user_question = "Explain the Role-Based Agent Design and its purpose."
    print(f"--- 正在查詢問題: {user_question} ---")
    final_result = run_tuned_rag_query(user_question)
    print("\n--- 最終結果 ---")
    print(final_result)

