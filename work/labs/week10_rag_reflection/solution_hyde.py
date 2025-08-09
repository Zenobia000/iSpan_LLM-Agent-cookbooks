# week10_rag_reflection/solution_hyde.py
import sys
import os
import json
from textwrap import dedent
from typing import List

from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from datasets import Dataset
from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    AnswerRelevancy,
    ContextRelevance,
    Faithfulness,
)

# Load .env file and ensure project root is in path
load_dotenv(find_dotenv())
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Knowledge Source Setup ---
# We use the same knowledge file as the advanced solution.
text_file_source = TextFileKnowledgeSource(file_paths=['advanced_rag_concepts.txt'])


# --- Agent Definitions for the HyDE Pipeline ---

class HydeRagAgents:
    """Manages the agents for the 4-stage HyDE RAG pipeline."""

    def hypothetical_document_generator_agent(self) -> Agent:
        """Agent that generates a hypothetical document based on the query."""
        return Agent(
            role="Hypothetical Document Creator",
            goal="Generate a detailed, plausible document that hypothetically answers the user's query. "
                 "This document will be used for similarity search, not as a final answer.",
            backstory="An expert creative writer who can quickly synthesize information and "
                      "construct a comprehensive, albeit fictional, answer on any topic.",
            verbose=True,
        )

    def information_retriever_agent(self) -> Agent:
        """Agent that retrieves information using the hypothetical document."""
        return Agent(
            role="Information Retrieval Specialist",
            goal="Use the provided hypothetical document to find the most relevant real documents from the knowledge base.",
            backstory="A master of vector-based document retrieval, you can always find the needle in the haystack.",
            verbose=True,
        )

    def answer_generator_agent(self) -> Agent:
        """Agent that generates the final answer."""
        return Agent(
            role="Answer Generation Specialist",
            goal="Generate a final, fact-based answer to the original user query based on the retrieved context.",
            backstory="A skilled communicator, you can synthesize complex information into clear, concise, and accurate answers.",
            verbose=True,
        )

# --- Task Definitions ---

class HydeRagTasks:
    """Defines the tasks for each stage of the HyDE RAG pipeline."""

    def generate_hyde_document_task(self, agent: Agent, query: str) -> Task:
        return Task(
            description=f"Generate a hypothetical document that comprehensively answers the following query: '{query}'.",
            expected_output="A single, detailed text document that reads like a perfect answer to the query.",
            agent=agent,
        )

    def retrieve_info_task(self, agent: Agent, hypothetical_document: str) -> Task:
        return Task(
            description=f"Use the following hypothetical document to perform a similarity search in the knowledge base:\n\n---\n{hypothetical_document}\n---",
            expected_output="A single block of text containing the most relevant real documents found.",
            agent=agent,
        )

    def generate_answer_task(self, agent: Agent, query: str, context: str) -> Task:
        return Task(
            description=f"Generate a final, fact-based answer to the original query: '{query}' based on the following retrieved context:\n\n---\n{context}\n---",
            expected_output="A comprehensive and well-written final answer, strictly based on the provided context.",
            agent=agent,
        )

# --- Main Execution Controller ---

def main():
    """Runs the 4-stage HyDE RAG pipeline."""
    agents = HydeRagAgents()
    tasks = HydeRagTasks()

    # Instantiate agents
    hyde_generator = agents.hypothetical_document_generator_agent()
    retriever = agents.information_retriever_agent()
    generator = agents.answer_generator_agent()

    original_query = "Tell me about advanced RAG techniques in CrewAI."
    print(f"🎯 Original Query: {original_query}\n---")

    # --- Stage 1: HyDE Generation ---
    print("### Stage 1: Hypothetical Document Generation (HyDE) ###")
    hyde_task = tasks.generate_hyde_document_task(hyde_generator, original_query)
    hyde_crew = Crew(agents=[hyde_generator], tasks=[hyde_task], verbose=False)
    hypothetical_document = str(hyde_crew.kickoff())
    print(f"📄 Hypothetical Document Generated:\n{hypothetical_document}\n")

    # --- Stage 2: HyDE-based Retrieval ---
    print("### Stage 2: HyDE-based Retrieval ###")
    retrieve_task = tasks.retrieve_info_task(retriever, hypothetical_document)
    retrieval_crew = Crew(
        agents=[retriever],
        tasks=[retrieve_task],
        knowledge_sources=[text_file_source],
        verbose=False
    )
    retrieved_context = str(retrieval_crew.kickoff())
    print(f"✅ Real Context Retrieved.\n")

    # --- Stage 3: Answer Generation ---
    print("### Stage 3: Answer Generation ###")
    generate_task = tasks.generate_answer_task(generator, original_query, retrieved_context)
    generation_crew = Crew(agents=[generator], tasks=[generate_task], verbose=False)
    final_answer = str(generation_crew.kickoff())
    print(f"📝 Final Answer Generated:\n{final_answer}\n")

    # --- Stage 4: Ragas Quality Evaluation ---
    print("### Stage 4: Ragas Quality Evaluation ###")
    rag_dataset = Dataset.from_dict({
        "question": [original_query],
        "contexts": [[retrieved_context]],
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
        llm=ChatOpenAI(model_name="gpt-4o")
    )
    
    result_df = result.to_pandas()
    print("Ragas Evaluation Results:")
    print(result_df)

if __name__ == "__main__":
    main()
