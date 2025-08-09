# week10_rag_reflection/solution_advanced.py
import sys
import os
import json
from textwrap import dedent
from typing import List

from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from datasets import Dataset
from dotenv import find_dotenv, load_dotenv
from ragas import evaluate
from ragas.metrics import (
    AnswerRelevancy,
    ContextRelevance,
    Faithfulness,
)
from langchain_openai import ChatOpenAI

# Load .env file and ensure project root is in path
load_dotenv(find_dotenv())
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Knowledge Source Setup (The Modern Way) ---
# crewai will look for this file in the `knowledge` directory at the project root.
text_file_source = TextFileKnowledgeSource(file_paths=['advanced_rag_concepts.txt'])


# --- Agent Definitions for the Advanced RAG Pipeline ---

class AdvancedRagAgents:
    """Manages the agents for the 4-stage advanced RAG pipeline."""

    def query_expansion_agent(self) -> Agent:
        return Agent(
            role="Query Expansion Specialist",
            goal="Rewrite a user's query into 3 distinct, more specific sub-queries to ensure comprehensive context retrieval.",
            backstory="An expert in search engine optimization, you know how to break down a question to cover all its angles.",
            verbose=True,
        )

    def information_retriever_agent(self) -> Agent:
        return Agent(
            role="Information Retrieval Specialist",
            goal="Retrieve relevant information from the knowledge base for a given set of queries.",
            backstory="A master of document retrieval, you can always find the needle in the haystack.",
            # knowledge_base is now provided at the Crew level, not here.
            verbose=True,
        )

    def answer_generator_agent(self) -> Agent:
        return Agent(
            role="Answer Generation Specialist",
            goal="Generate a comprehensive and high-quality answer based on the provided context and original query.",
            backstory="A skilled communicator, you can synthesize complex information into clear, concise answers.",
            verbose=True,
        )

    def ragas_evaluation_agent(self) -> Agent:
        return Agent(
            role="RAG Quality Assurance Analyst",
            goal="Evaluate the quality of the RAG pipeline's output using the Ragas framework.",
            backstory="A meticulous QA analyst, you ensure that every answer is relevant, faithful, and of the highest quality.",
            verbose=True,
        )

# --- Task Definitions ---

class AdvancedRagTasks:
    """Defines the tasks for each stage of the advanced RAG pipeline."""

    def expand_query_task(self, agent: Agent, query: str) -> Task:
        return Task(
            description=f"Expand the user query '{query}' into 3 distinct sub-queries. Return them as a JSON list of strings.",
            expected_output='A JSON object containing a list of 3 strings, like: `{"queries": ["query1", "query2", "query3"]}`',
            agent=agent,
        )

    def retrieve_info_task(self, agent: Agent, context: List[str]) -> Task:
        # The context here is the list of expanded queries
        queries_str = "\n".join(context)
        return Task(
            description=f"Retrieve documents for the following queries:\n{queries_str}",
            expected_output="A single block of text containing the merged and deduplicated context from all queries.",
            agent=agent,
        )

    def generate_answer_task(self, agent: Agent, query: str, context: str) -> Task:
        return Task(
            description=f"Generate a final answer to the original query '{query}' based on the following context:\n{context}",
            expected_output="A comprehensive and well-written final answer.",
            agent=agent,
        )

    def evaluate_rag_task(self, agent: Agent, query: str, context: str, answer: str) -> Task:
        # This task is now conceptual, as ragas evaluation is done directly in the script.
        # We keep the agent definition for completeness of the conceptual flow.
        return Task(
            description=f"Evaluate the RAG triad (query, context, answer) using the Ragas framework. " \
                        f"Calculate faithfulness, answer_relevancy, and context_relevancy.",
            expected_output="A JSON object containing the evaluation scores and a final quality assessment.",
            agent=agent,
        )

# --- Main Execution Controller ---

def main():
    """Runs the 4-stage advanced RAG pipeline."""
    agents = AdvancedRagAgents()
    tasks = AdvancedRagTasks()

    # Instantiate agents
    query_expander = agents.query_expansion_agent()
    retriever = agents.information_retriever_agent()
    generator = agents.answer_generator_agent()
    evaluator = agents.ragas_evaluation_agent()

    original_query = "Tell me about advanced RAG techniques in CrewAI."
    print(f"🎯 Original Query: {original_query}\n---")

    # --- Stage 1: Query Expansion ---
    print("### Stage 1: Query Expansion ###")
    expand_task = tasks.expand_query_task(query_expander, original_query)
    expansion_crew = Crew(agents=[query_expander], tasks=[expand_task], verbose=False)
    raw_expansion_output = expansion_crew.kickoff()
    
    # Robust JSON parsing
    try:
        # Convert CrewOutput to string before processing
        expanded_queries_json = str(raw_expansion_output)

        # Clean up potential markdown code blocks
        if expanded_queries_json.strip().startswith("```json"):
            expanded_queries_json = expanded_queries_json.strip()[7:-4].strip()
        expanded_queries = json.loads(expanded_queries_json)["queries"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing expanded queries: {e}")
        print(f"Raw output: {expanded_queries_json}")
        return # Exit if we can't get the queries

    print(f"Expanded Queries: {expanded_queries}\n")

    # --- Stage 2: Multi-path Retrieval ---
    print("### Stage 2: Multi-path Retrieval ###")
    retrieve_task = tasks.retrieve_info_task(retriever, expanded_queries)
    retrieval_crew = Crew(
        agents=[retriever], 
        tasks=[retrieve_task],
        knowledge_sources=[text_file_source], # <-- Modern knowledge injection
        verbose=False
    )
    comprehensive_context_output = retrieval_crew.kickoff()
    comprehensive_context = str(comprehensive_context_output) # Convert to string
    print(f"Comprehensive Context Retrieved.\n")

    # --- Stage 3: Answer Generation ---
    print("### Stage 3: Answer Generation ###")
    generate_task = tasks.generate_answer_task(generator, original_query, comprehensive_context)
    generation_crew = Crew(agents=[generator], tasks=[generate_task], verbose=False)
    final_answer_output = generation_crew.kickoff()
    final_answer = str(final_answer_output) # Convert to string
    print(f"Final Answer Generated:\n{final_answer}\n")

    # --- Stage 4: Ragas Quality Evaluation ---
    print("### Stage 4: Ragas Quality Evaluation ###")
    # Ragas requires the data in a specific format (huggingface dataset)
    rag_dataset = Dataset.from_dict({
        "question": [original_query],
        "contexts": [[comprehensive_context]],
        "answer": [final_answer]
    })

    # Perform the evaluation
    result = evaluate(
        dataset=rag_dataset,
        metrics=[
            ContextRelevance(),
            Faithfulness(),
            AnswerRelevancy(),
        ],
        llm=ChatOpenAI(model_name="gpt-4o") # Explicitly provide the LLM for evaluation
    )
    
    # Convert result to a more readable format
    result_df = result.to_pandas()
    print("Ragas Evaluation Results:")
    print(result_df)


if __name__ == "__main__":
    main()
