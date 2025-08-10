# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week11_training_pipeline\main.py
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from textwrap import dedent
from crewai import Task, Crew, Process
from agent_definitions import content_creator_agent, critique_agent
from training_data_collector import TrainingDataCollector

class SelfRefineCrew:
    def __init__(self, topic: str, max_iterations: int = 3):
        self.topic = topic
        self.max_iterations = max_iterations
        self.data_collector = TrainingDataCollector(os.path.join(os.path.dirname(__file__), "training_data.jsonl"))

    def run(self):
        # Initial content creation
        initial_task = Task(
            description=f"Create a detailed and engaging piece of content about: {self.topic}",
            expected_output="A well-structured and informative article.",
            agent=content_creator_agent
        )

        creation_crew = Crew(agents=[content_creator_agent], tasks=[initial_task], process=Process.sequential, verbose=True)
        current_content = str(creation_crew.kickoff())

        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1} of {self.max_iterations} ---")

            # Critique task
            critique_task = Task(
                description=dedent(f"""
                    Critically review the following content. Provide a score from 1-10 and detailed, actionable suggestions for improvement.

                    Content to review:
                    ---
                    {current_content}
                    ---
                """),
                expected_output="A score (e.g., 7/10) and a bulleted list of specific suggestions.",
                agent=critique_agent
            )

            critique_crew = Crew(agents=[critique_agent], tasks=[critique_task], process=Process.sequential, verbose=True)
            critique = str(critique_crew.kickoff())

            # Refinement task
            refinement_task = Task(
                description=dedent(f"""
                    Improve the following content based on the provided critique.

                    Original Content:
                    ---
                    {current_content}
                    ---

                    Critique and Suggestions:
                    ---
                    {critique}
                    ---
                """),
                expected_output="A new, improved version of the content that directly addresses the critique.",
                agent=content_creator_agent
            )

            refinement_crew = Crew(agents=[content_creator_agent], tasks=[refinement_task], process=Process.sequential, verbose=True)
            refined_content = str(refinement_crew.kickoff())

            # Collect data
            self.data_collector.collect(original_prompt=f"Improve this content based on the critique: \n\n{current_content}\n\nCritique: {critique}", refined_content=refined_content)
            
            current_content = refined_content

        self.data_collector.save()
        print("\n--- Self-Refine process completed. ---")
        return current_content

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        topic = "The Role of AI in Modern Software Development"
        self_refine_process = SelfRefineCrew(topic=topic, max_iterations=2) # Using 2 iterations for demonstration
        final_content = self_refine_process.run()
        print("\n--- Final Content ---")
        print(final_content)
