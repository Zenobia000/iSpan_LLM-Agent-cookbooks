
# === 導入設置 === 
# 1. 首先設置導入路徑
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from import_helper import init_labs
init_labs()

# 2. 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
    print(f"✅ 成功啟用 pysqlite3，SQLite 版本: {sqlite3.sqlite_version}")
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")

# 3. 標準庫導入
import os
import io
import logging
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# 4. 第三方庫導入
from crewai import Agent, Task, Crew, Process

# 5. 專案模組導入
from src.core.tools.search_tool import TavilySearchTool
from src.patterns.planning.planner_agent import PlannerAgent


class OutputCapture:
    """捕獲和記錄所有輸出的類別"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 創建帶時間戳的日誌文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"crewai_execution_{timestamp}.txt"
        self.detailed_log_file = self.log_dir / f"crewai_detailed_{timestamp}.log"
        
        # 設置日誌記錄器
        self.setup_logging()
        
        # 創建輸出緩存
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        
    def setup_logging(self):
        """設置詳細的日誌記錄"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(self.detailed_log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("CrewAI_Execution")
        
    def write_header(self):
        """寫入執行標頭資訊"""
        header = f"""
{'='*80}
CrewAI Hierarchical Planning Execution Log
{'='*80}
執行時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Python 版本: {sys.version}
SQLite 版本: {sqlite3.sqlite_version}
工作目錄: {os.getcwd()}
日誌文件: {self.log_file.name}
{'='*80}

"""
        
        # 寫入日誌文件
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
            
        # 同時輸出到控制台
        print(header)
        self.logger.info("開始 CrewAI 執行記錄")
        
    def log_section(self, title: str, content: str = ""):
        """記錄分段資訊"""
        section = f"\n{'='*60}\n{title}\n{'='*60}\n{content}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(section)
            
        print(f"\n📋 {title}")
        if content:
            print(content)
            
        self.logger.info(f"Section: {title}")
        
    def capture_execution(self, func, *args, **kwargs):
        """捕獲函數執行過程中的所有輸出"""
        self.log_section("開始 CrewAI 執行", "正在啟動 hierarchical planning 流程...")
        
        # 創建自定義的輸出處理器
        class TeeOutput:
            def __init__(self, original, log_file, buffer):
                self.original = original
                self.log_file = log_file
                self.buffer = buffer
                
            def write(self, text):
                # 輸出到原始目標（控制台）
                self.original.write(text)
                self.original.flush()
                
                # 同時寫入日誌文件
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(text)
                    
                # 保存到緩存
                self.buffer.write(text)
                
            def flush(self):
                self.original.flush()
                
        # 創建 tee 輸出
        stdout_tee = TeeOutput(sys.stdout, self.log_file, self.stdout_buffer)
        stderr_tee = TeeOutput(sys.stderr, self.log_file, self.stderr_buffer)
        
        try:
            # 重定向輸出
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            sys.stdout = stdout_tee
            sys.stderr = stderr_tee
            
            # 執行函數
            self.logger.info("開始執行 CrewAI kickoff")
            result = func(*args, **kwargs)
            self.logger.info("CrewAI 執行完成")
            
            return result
            
        except Exception as e:
            error_msg = f"執行過程中發生錯誤: {str(e)}"
            self.log_section("執行錯誤", error_msg)
            self.logger.error(error_msg, exc_info=True)
            raise
            
        finally:
            # 恢復原始輸出
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
    def write_summary(self, result):
        """寫入執行摘要"""
        summary = f"""
{'='*80}
執行摘要
{'='*80}
完成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
結果長度: {len(str(result))} 字符
日誌文件大小: {self.log_file.stat().st_size / 1024:.2f} KB

最終結果:
{'-'*40}
{result}
{'-'*40}

執行統計:
- 標準輸出行數: {len(self.stdout_buffer.getvalue().splitlines())}
- 標準錯誤行數: {len(self.stderr_buffer.getvalue().splitlines())}
- 總輸出字符數: {len(self.stdout_buffer.getvalue()) + len(self.stderr_buffer.getvalue())}

{'='*80}
"""
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(summary)
            
        print(summary)
        self.logger.info("執行摘要已生成")
        
        # 創建額外的分析文件
        self.create_analysis_files(result)
        
    def create_analysis_files(self, result):
        """創建分析用的額外文件"""
        # 1. 純文字結果文件
        result_file = self.log_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("CrewAI 執行最終結果\n")
            f.write("="*50 + "\n\n")
            f.write(str(result))
            
        # 2. 輸出統計文件
        stats_file = self.log_dir / f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        stdout_lines = self.stdout_buffer.getvalue().splitlines()
        stderr_lines = self.stderr_buffer.getvalue().splitlines()
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("CrewAI 執行統計分析\n")
            f.write("="*50 + "\n\n")
            f.write(f"標準輸出總行數: {len(stdout_lines)}\n")
            f.write(f"標準錯誤總行數: {len(stderr_lines)}\n")
            f.write(f"包含 'Task' 的行數: {sum(1 for line in stdout_lines if 'Task' in line)}\n")
            f.write(f"包含 'Agent' 的行數: {sum(1 for line in stdout_lines if 'Agent' in line)}\n")
            f.write(f"包含 'Tool' 的行數: {sum(1 for line in stdout_lines if 'Tool' in line)}\n")
            f.write(f"包含 'Error' 的行數: {sum(1 for line in stdout_lines + stderr_lines if 'Error' in line)}\n")
            
        self.logger.info(f"分析文件已創建: {result_file}, {stats_file}")
        
    def get_log_info(self):
        """獲取日誌文件資訊"""
        return {
            "main_log": str(self.log_file),
            "detailed_log": str(self.detailed_log_file),
            "log_size": self.log_file.stat().st_size if self.log_file.exists() else 0,
            "creation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# --- Agents 定義 ---

# 2. 研究員 Agent (Worker)
researcher = Agent(
    role="Tech Research Analyst",
    goal="Gather, analyze, and synthesize the latest technical information and code examples about a given topic.",
    backstory="""You are an expert in navigating complex technical documentation, GitHub repositories, and developer blogs. 
    You excel at finding the most accurate and relevant information. When you receive a research task, you:
    1. Use search tools to gather comprehensive information
    2. Analyze and synthesize findings
    3. Present results in a structured, actionable format""",
    verbose=True,
    allow_delegation=False,
    tools=[TavilySearchTool()],
    max_iter=5  # 限制迭代避免工具使用循環
)

# 3. 撰寫員 Agent (Worker)
writer = Agent(
    role="Technical Content Writer",
    goal="Write a clear, concise, and engaging technical blog post based on provided research and requirements.",
    backstory="""You are a skilled technical writer who can transform complex concepts into easy-to-understand articles. 
    When you receive a writing task, you:
    1. Review all provided research materials and requirements
    2. Structure content logically with clear sections
    3. Write engaging, informative content for developer audiences
    4. Ensure technical accuracy while maintaining readability""",
    verbose=True,
    allow_delegation=False,
    max_iter=3
)

# 4. 審閱員 Agent (Worker)
reviewer = Agent(
    role="Senior Tech Editor",
    goal="Review technical content for accuracy, clarity, and quality. Provide constructive feedback and improvements.",
    backstory="""You are a senior technical editor with deep expertise in software engineering and content quality. 
    When you receive a review task, you:
    1. Analyze content for technical accuracy and clarity
    2. Check for grammatical correctness and flow
    3. Provide specific, actionable feedback
    4. Ensure content meets high publication standards""",
    verbose=True,
    allow_delegation=False,
    max_iter=3
)

# 1. 規劃 Agent (Manager) - 在 Worker Agents 定義後創建
planner_logic = PlannerAgent()
planner = planner_logic.planner

# --- Tasks 定義 ---

# 這是啟動 Hierarchical 流程的初始任務
kickoff_task = Task(
    description="""
    Create a comprehensive technical blog post by coordinating a team of specialists.
    
    **Available Team Members:**
    - Tech Research Analyst: Expert at gathering and analyzing technical information using search tools
    - Technical Content Writer: Skilled at writing clear, engaging technical content  
    - Senior Tech Editor: Expert at reviewing and improving content quality
    
    **High-Level Goal:** {topic}
    
    **Process:**
    1. First, delegate research tasks to Tech Research Analyst to gather comprehensive information
    2. Then, delegate writing tasks to Technical Content Writer using the research findings
    3. Finally, delegate review tasks to Senior Tech Editor to ensure quality
    4. Coordinate and integrate all outputs into a final blog post
    
    **Delegation Instructions:**
    - Use exact role names when delegating: "Tech Research Analyst", "Technical Content Writer", "Senior Tech Editor"
    - Provide clear, specific task descriptions
    - Include all necessary context for each task
    - Ensure proper sequencing of tasks
    """,
    expected_output="A complete and well-structured technical blog post produced through coordinated team effort"
    # 注意：在 hierarchical process 中，不需要指定 agent，manager_llm 會自動處理
)


# --- Crew 組建 ---

# 方法 1: 使用 manager_llm 而不是 manager_agent (推薦)
blog_crew = Crew(
    agents=[researcher, writer, reviewer], # Worker agents 
    tasks=[kickoff_task], # 初始任務
    process=Process.hierarchical,
    manager_llm="gpt-4.1-mini",  # 使用 manager_llm 而不是 manager_agent
    verbose=True,
    max_rpm=10,  # 限制 API 請求速率
    memory=True,  # 啟用記憶功能
    # 添加明確的委派配置
    share_crew=True,  # 確保 agents 之間可以互相看到
)

# --- 執行函數 ---

def execute_blog_creation(topic: str):
    """執行部落格創建任務並記錄所有過程"""
    return blog_crew.kickoff(inputs={'topic': topic})


# --- 主執行區塊 ---

if __name__ == "__main__":
    # 設置輸出捕獲 (使用相對於當前腳本的路徑)
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    output_capture = OutputCapture(log_dir=str(log_dir))
    
    # 寫入執行標頭
    output_capture.write_header()
    
    # 定義高階目標
    high_level_goal = "Write a comprehensive technical blog post about the difference between AI LLM VLM multimodel and single model."
    
    # 記錄執行配置
    config_info = f"""
執行配置:
- 高階目標: {high_level_goal}
- 流程模式: Hierarchical (使用 manager_llm)
- Manager: GPT-4 (manager_llm)
  - 類型: LLM Manager (非自定義 Agent)
  - 委派能力: ✅ 內建支援
- Worker Agents: {len(blog_crew.agents)} 個
  - {researcher.role} (工具: {len(researcher.tools)})
  - {writer.role} (工具: {len(getattr(writer, 'tools', []))})
  - {reviewer.role} (工具: {len(getattr(reviewer, 'tools', []))})
- Crew 配置:
  - Process: {blog_crew.process}
  - Max RPM: {getattr(blog_crew, 'max_rpm', 'default')}
  - Memory: {getattr(blog_crew, 'memory', 'default')}
  - Share Crew: {getattr(blog_crew, 'share_crew', 'default')}

委派功能診斷:
- Manager 類型: ✅ manager_llm (應該能看到所有 Worker Agents)
- Worker Agents 數量: {len(blog_crew.agents)}
- 預期委派流程: GPT-4 Manager → Tech Research Analyst → Technical Content Writer → Senior Tech Editor → Final Result

修復說明:
- 改用 manager_llm 而非 manager_agent 來避免委派工具看不到 Worker Agents 的問題
- manager_llm 會自動獲得正確的委派工具配置
"""
    
    output_capture.log_section("執行配置", config_info)
    
    try:
        # 使用輸出捕獲執行 CrewAI
        output_capture.log_section("CrewAI 啟動", "開始執行 hierarchical planning 流程...")
        
        result = output_capture.capture_execution(
            execute_blog_creation, 
            high_level_goal
        )
        
        # 寫入執行摘要
        output_capture.write_summary(result)
        
        # 顯示日誌文件資訊
        log_info = output_capture.get_log_info()
        final_message = f"""
🎯 CrewAI 執行完成！

📁 生成的文件:
- 主要日誌: {log_info['main_log']}
- 詳細日誌: {log_info['detailed_log']}
- 日誌大小: {log_info['log_size'] / 1024:.2f} KB

💡 用於研究思維過程的完整記錄已保存
可以使用這些文件分析 AI 代理的決策流程和工作模式
"""
        
        print(final_message)
        output_capture.logger.info("所有執行日誌已完成")
        
    except Exception as e:
        error_message = f"執行過程中發生錯誤: {str(e)}"
        output_capture.log_section("執行失敗", error_message)
        print(f"\n❌ {error_message}")
        
        # 即使失敗也要保存已記錄的內容
        partial_result = f"執行未完成，錯誤: {str(e)}"
        output_capture.write_summary(partial_result)
        
        raise
        
    finally:
        # 顯示日誌位置
        print(f"\n📋 完整執行記錄保存在: {output_capture.log_file}")
        print(f"📋 詳細技術日誌保存在: {output_capture.detailed_log_file}")

