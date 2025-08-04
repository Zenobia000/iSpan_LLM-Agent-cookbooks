import os
from crewai import Agent, Task, Crew, Process

# Set your API Key
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# Agent 1: Weather Reporter
weather_reporter = Agent(
  role='Weather Reporter',
  goal='Provide a concise summary of the weather in a given city.',
  backstory='An experienced meteorologist who excels at delivering clear and easy-to-understand weather reports.',
  verbose=True,
  allow_delegation=False,
  # llm=OpenAI(temperature=0) # You can optionally specify the LLM to be used by this agent
)

# Agent 2: Summary Reviewer (implements Reflection)
summary_reviewer = Agent(
  role='Summary Reviewer',
  goal='Critique a weather summary, rating it from 1 to 10 and providing actionable feedback for improvement.',
  backstory='A meticulous editor with a keen eye for detail and clarity, ensuring every report is flawless.',
  verbose=True,
  allow_delegation=False,
)

# Task 1: Generate Weather Summary
report_task = Task(
  description='Create a weather summary for New York City for today. Include temperature, humidity, and wind speed.',
  expected_output='A paragraph summarizing the weather, formatted for a general audience.',
  agent=weather_reporter
)

# Task 2: Review and Critique (The Reflection Task)
review_task = Task(
  description='Review the weather summary. Provide a rating from 1-10 and list three specific suggestions for making it better. The critique should be constructive and clear.',
  expected_output='A numbered list containing a rating and three concrete suggestions for improvement.',
  agent=summary_reviewer,
  context=[report_task] # Critical: The output of the report_task is the context for this task.
)

# Task 3: Revise Summary Based on Feedback
revision_task = Task(
  description='Revise the original weather summary based on the feedback provided. You must incorporate all suggestions to improve the report.',
  expected_output='An improved, final version of the weather summary that addresses all the feedback from the reviewer.',
  agent=weather_reporter,
  context=[report_task, review_task] # Critical: Context includes both the original report and the review.
)

# Create the Crew
weather_crew = Crew(
  agents=[weather_reporter, summary_reviewer],
  tasks=[report_task, review_task, revision_task],
  process=Process.sequential, # Tasks will be executed one after another
  verbose=2 # Enables detailed logging of the execution process
)

# Execute the Crew
if __name__ == "__main__":
    print("## Welcome to the Weather Report Self-Critique Crew")
    print("-------------------------------------------------")
    # You can set the inputs for the crew here
    # result = weather_crew.kickoff(inputs={'city': 'San Francisco'})
    
    result = weather_crew.kickoff()

    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################\n")
    print(result)


