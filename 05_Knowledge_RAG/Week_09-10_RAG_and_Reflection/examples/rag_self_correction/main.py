import os
from crewai import Agent, Task, Crew, Process
from crewai.knowledge import KnowledgeBase
from crewai_tools import FileReadTool

# --- Setup ---
# Create the knowledge base file if it doesn't exist
if not os.path.exists("company_policy.md"):
    with open("company_policy.md", "w") as f:
        f.write(
"""# Company Leave Policy

## Annual Leave
All full-time employees are entitled to 15 days of paid annual leave.

## Sick Leave
Employees can take up to 5 days of paid sick leave per year.
"""
        )

# Set your API Key
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# --- Knowledge Base and Tools ---
# Create a FileReadTool to read our knowledge base file
file_tool = FileReadTool(file_path='company_policy.md')

# Create the KnowledgeBase
knowledge_base = KnowledgeBase(
    source='company_policy.md',
    # You can specify an embedder for the knowledge base
    # embedder={'provider': 'openai', 'config': {'model': 'text-embedding-3-small'}}
)


# --- Agent Definition ---
policy_expert = Agent(
    role="HR Policy Expert",
    goal="Provide clear and accurate information about the company's leave policy.",
    backstory="You are an HR specialist with deep knowledge of the company's internal policies. "
              "You use the official company policy document as your single source of truth.",
    verbose=True,
    knowledge_base=knowledge_base, # Assign the knowledge base to the agent
    # Note: By assigning the knowledge base, CrewAI automatically equips the agent
    # with a 'Knowledge Base Search' tool. You don't need to add it to the `tools` list.
    tools=[file_tool] # We can still provide other tools if needed
)

# --- Task Definition with Guardrail ---
policy_question_task = Task(
    description="I need to take some time off for personal reasons. What is the company policy on personal leave?",
    expected_output="A clear explanation of the options available for personal leave, referencing the annual leave policy if necessary.",
    agent=policy_expert,
    # The guardrail checks if the output mentions "annual leave".
    # If the agent's first attempt doesn't find a direct answer for "personal leave",
    # it might give a vague response. The guardrail forces it to retry and
    # find the most relevant policy (annual leave) to answer the user's intent.
    guardrail=lambda out: "annual leave" in out.lower()
)

# --- Crew Definition ---
policy_crew = Crew(
    agents=[policy_expert],
    tasks=[policy_question_task],
    process=Process.sequential,
    verbose=2
)

# --- Execution ---
if __name__ == "__main__":
    print("## Welcome to the RAG Self-Correction Crew")
    print("------------------------------------------")
    
    result = policy_crew.kickoff()

    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################\n")
    print(result)



