# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week13_observability\solution.py
import sys
import os
import codecs
from dotenv import load_dotenv
from typing import List, Dict

# --- Robust UTF-8 Console Output ---
# This is a best practice for ensuring cross-platform compatibility of console output,
# especially on Windows, by forcing the standard output and error streams to use UTF-8.
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
# ------------------------------------

# --- AgentOps Initialization ---
# Note: To use AgentOps, you need to install it (`pip install agentops`)
# and set your AGENTOPS_API_KEY in the .env file.
import agentops

# Add project root to sys.path for consistent imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import all crewai components before initializing agentops
from crewai import Agent, Task, Crew, Process
from src.core.tools.search_tool import TavilySearchTool
from work.labs.week13_observability.custom_handler import CustomToolsHandler

# --- AgentOps Initialization ---
# Load environment variables and initialize AgentOps AFTER crewai imports
load_dotenv()
agentops.init()
# -----------------------------

# --- Agent Definitions ---

# Create an instance of the custom handler to be shared by agents
custom_handler = CustomToolsHandler()

# Define roles as constants for consistency
RESEARCHER_ROLE = 'Senior Research Analyst'
WRITER_ROLE = 'Tech Content Strategist'
EDITOR_ROLE = 'Chief Editor'

# Define agents in dependency order
researcher = Agent(
    role=RESEARCHER_ROLE,
    goal='Uncover cutting-edge developments in AI and data science',
    backstory=(
        "As a Senior Research Analyst at a top-tier technology think tank, your "
        "mission is to provide unbiased, data-driven insights. You are adept at "
        "sifting through research papers, news, and technical blogs to find "
        "verifiable facts and compelling trends."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[TavilySearchTool()]
)

writer = Agent(
    role=WRITER_ROLE,
    goal="Craft compelling content on tech advancements",
    backstory=(
        "As a savvy strategist, your core mission is to write engaging and "
        "accessible blog posts about complex tech topics. You transform dense research "
        "into sharp, cool, and easy-to-understand narratives. "
        "You are the main writer.\n"
        "If you need additional, specific data or a fact-check, you must delegate "
        "the task to the 'Senior Research Analyst'.\n"
        "IMPORTANT: When delegating, your Action Input MUST be a JSON object with the keys "
        "'coworker', 'task', and 'context'. The values for 'task' and 'context' MUST be simple strings. "
        "For example: {\"coworker\": \"Senior Research Analyst\", \"task\": \"Double-check this fact.\", \"context\": \"The fact is...\"}"
    ),
    verbose=True,
    allow_delegation=True,
    coworkers=[researcher],
    tools_handler=custom_handler # Inject the custom handler
)

editor = Agent(
    role=EDITOR_ROLE,
    goal="Produce a polished, publication-ready article",
    backstory=(
        "As the Chief Editor, you are the final gatekeeper of quality. Your primary role is to "
        "review, edit, and polish the content for clarity, grammar, tone, and factual accuracy. \n"
        "If you find a major factual error, delegate a verification task back to the 'Senior Research Analyst'.\n"
        "If the article needs a substantial rewrite, delegate it back to the 'Tech Content Strategist'.\n"
        "IMPORTANT: When delegating, your Action Input MUST be a JSON object with the keys "
        "'coworker', 'task', and 'context'. The values for 'task' and 'context' MUST be simple strings. "
        "For example: {\"coworker\": \"Senior Research Analyst\", \"task\": \"Verify this statistic.\", \"context\": \"The statistic is...\"}"
    ),
    verbose=True,
    allow_delegation=True,
    coworkers=[researcher, writer],
    tools_handler=custom_handler # Inject the custom handler
)

# --- Task Definitions ---
research_task = Task(
    description=(
        "Conduct a comprehensive analysis of the latest advancements in AI in 2024. "
        "Identify key trends, breakthrough technologies, and their potential "
        "impact on various industries. Your final answer must be a detailed "
        "report that includes citations and links to credible sources."
    ),
    expected_output=(
        "A comprehensive report summarizing the latest AI advancements in 2024, "
        "with sections on key trends, new technologies, and industry impact. "
        "The report must include links to all sources."
    ),
    agent=researcher,
)

writing_task = Task(
    description=(
        "Using the research report provided, write a compelling and accessible "
        "blog post titled 'AI in 2024: The Top Breakthroughs Shaping Our Future'. "
        "The post should be engaging, informative, and easy for a general "
        "audience to understand. Focus on clarity, storytelling, and highlighting "
        "the most exciting developments."
    ),
    expected_output=(
        "A well-structured and engaging blog post of approximately 800-1000 words, "
        "written in a clear and accessible style. The post must accurately reflect "
        "the key findings from the research report."
    ),
    agent=writer,
    context=[research_task],
)

editing_task = Task(
    description=(
        "Review the blog post written by the Tech Content Strategist. Check for "
        "clarity, grammar, tone, and factual accuracy. Provide a final, polished "
        "version of the article ready for publication. If you find any major "
        "issues, delegate back to the appropriate agent for corrections."
    ),
    expected_output=(
        "The final, polished, and publication-ready version of the blog post, "
        "free of errors and consistent with the house style. The article should "
        "be ready to be published immediately."
    ),
    agent=editor,
    context=[writing_task],
)

# --- Crew Definition ---
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,
    verbose=True,
)

# --- Execution ---
print("🚀 Kicking off the crew execution...")
result = crew.kickoff()

print("\n\n########################")
print("## Crew Execution Result:")
print("########################\n")
print(result)
