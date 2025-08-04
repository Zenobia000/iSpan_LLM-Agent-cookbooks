import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Set your API Key
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# You can use a local model through Ollama, for example.
# Make sure you have a running Ollama instance.
# For this example, we will use the default (OpenAI).
#
# from langchain_community.chat_models import ChatOllama
# llm = ChatOllama(model="openhermes")

# Using a dedicated model for the manager is a recommended practice.
# It helps to avoid issues with the manager trying to delegate tasks to itself.
manager_llm = ChatOpenAI(model="gpt-4o")

# Define the Agents
planner = Agent(
    role="Content Planner",
    goal="Plan engaging and factually accurate content on a given topic.",
    backstory="You're working on planning a blog post about a chosen topic. "
              "You collect information that helps the Content Writer to write an amazing blog post.",
    allow_delegation=True,
    verbose=True
)

researcher = Agent(
    role="Researcher",
    goal="Be the best researcher in the world. Find facts and details about any given topic.",
    backstory="You are a master of search and information gathering. "
              "You know how to find the most relevant and accurate information on any subject.",
    allow_delegation=False,
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Write insightful and engaging blog posts.",
    backstory="You are a renowned Content Writer, known for your insightful and engaging articles. "
              "You can transform complex concepts into compelling narratives.",
    allow_delegation=False,
    verbose=True
)

# Define the Task
# This is the high-level task that will be decomposed by the manager.
plan_and_write_task = Task(
    description="Craft a blog post about the importance of AI in modern education. "
                "The post should be engaging, informative, and around 500 words.",
    expected_output="A well-structured blog post with an introduction, main body, and conclusion.",
    agent=planner  # Assign the task to the planner agent
)

# Create the Crew with a Hierarchical Process
project_crew = Crew(
    agents=[planner, researcher, writer],
    tasks=[plan_and_write_task],
    process=Process.hierarchical,  # Enable hierarchical process
    manager_llm=manager_llm,      # Assign the manager LLM
    verbose=2
)

# Execute the Crew
if __name__ == "__main__":
    print("## Welcome to the AI Content Creation Crew")
    print("------------------------------------------")
    result = project_crew.kickoff()

    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################\n")
    print(result)


