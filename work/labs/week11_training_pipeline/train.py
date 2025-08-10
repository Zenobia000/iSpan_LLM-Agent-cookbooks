# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week11_training_pipeline\train.py
import sys
import os
import json

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, Task, Crew, Process

# --- 1. Define the Crew to be Trained ---

researcher = Agent(
    role="Expert AI Researcher",
    goal="Provide up-to-date and accurate information on a given topic.",
    backstory="You are a seasoned researcher with access to a vast amount of information. You are known for your ability to synthesize complex topics into clear, concise summaries.",
    verbose=True
)

writer = Agent(
    role="Engaging Content Writer",
    goal="Write a compelling and easy-to-understand article based on the researcher's findings.",
    backstory="You are a skilled writer who can transform dry research into a captivating story. You excel at making complex subjects accessible to a general audience.",
    verbose=True
)

def create_qa_crew():
    """A factory function to create the Q&A crew."""
    research_task = Task(
        description="Research the provided topic thoroughly. Your final answer must be a detailed summary of your findings.",
        expected_output="A comprehensive summary of the research, including key points and any relevant data.",
        agent=researcher
    )

    write_task = Task(
        description="Using the research summary, write a clear and engaging article. The article should be well-structured and easy for a non-expert to understand.",
        expected_output="A well-written article that is informative and engaging.",
        agent=writer,
        context=[research_task]
    )

    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        human_input=False
    )

# --- 2. Load Training Data ---

def load_training_data(file_path: str):
    """Loads training data from a JSONL file."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        print(f"Successfully loaded {len(data)} records from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: Training data file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None

# --- 3. Run Training and Validation ---

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        # --- 1. Load the generated training data ---
        print("\n--- Loading Generated Training Data ---")
        training_data_path = os.path.join(os.path.dirname(__file__), "training_data.jsonl")
        training_data = load_training_data(training_data_path)
        
        if training_data:
            print("\n--- Using Generated Data for Fine-Tuning ---")
            print(f"The data in '{training_data_path}' is ready for fine-tuning.")
            print("You can now use this JSONL file with standard fine-tuning tools from providers like OpenAI, Hugging Face, or Google AI Platform.")
            print("Example OpenAI CLI command: openai api fine_tunes.create -t {training_data_path} -m <base_model>")

        # --- 2. Demonstrate a Base Crew for Comparison ---
        # This crew represents the baseline performance that you would aim to improve with a fine-tuned model.
        print("\n--- Demonstrating Baseline Crew Performance ---")
        qa_crew = create_qa_crew()
        inputs = {"topic": "The impact of AI on traditional art forms"}
        baseline_result = qa_crew.kickoff(inputs=inputs)
        
        print("\n--- Baseline Crew Result ---")
        print(baseline_result)

