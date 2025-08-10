# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week11_training_pipeline\agent_definitions.py
from crewai import Agent

content_creator_agent = Agent(
    role="Expert Content Creator",
    goal="Generate high-quality, engaging content based on a given topic.",
    backstory="You are a renowned content creator, known for your ability to craft compelling narratives and clear explanations on complex subjects.",
    verbose=True,
    allow_delegation=False
)

critique_agent = Agent(
    role="Insightful Content Critic",
    goal="Provide a critical review of a given piece of content, offering a score and actionable suggestions for improvement.",
    backstory="You are a sharp-eyed editor with a knack for identifying weaknesses in writing. Your feedback is always constructive and aimed at elevating the content to its highest potential.",
    verbose=True,
    allow_delegation=False
)
