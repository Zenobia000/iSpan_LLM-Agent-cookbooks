# week10_rag_reflection/solution.py
import sys
import json
import os
from textwrap import dedent
from typing import Dict, Any

from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

# Load .env file
load_dotenv(find_dotenv())

# --- Pydantic Model for Structured Critique Output ---

class CritiqueResult(BaseModel):
    """A model for the structured output of the CritiqueAgent."""
    score: int = Field(..., description="A score from 1 to 5, where 1 is not relevant and 5 is highly relevant.")
    reasoning: str = Field(..., description="A brief justification for the score.")
    is_sufficient: bool = Field(..., description="Whether the context is sufficient to answer the original query.")

# --- Knowledge Source Setup (The Correct Way from Week09) ---
# crewai will look for this file in the `knowledge` directory at the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
text_file_source = TextFileKnowledgeSource(file_paths=['crewai_features.txt'])


# --- Agent Definitions ---

class RagReflectionAgents:
    """Manages the three core agents for the Reflective RAG process."""

    def retriever_agent(self) -> Agent:
        """Agent responsible for initial information retrieval."""
        return Agent(
            role="Information Retriever",
            goal="Retrieve the most relevant information from the knowledge base for a given query.",
            backstory="An expert in searching and extracting information from documents.",
            # The agent itself doesn't need the knowledge parameter.
            # It will be provided at the Crew level.
            verbose=True,
        )

    def critique_agent(self) -> Agent:
        """Agent responsible for evaluating the retrieved context."""
        return Agent(
            role="Retrieval Quality Analyst",
            goal=f"Evaluate the relevance and sufficiency of the retrieved context against the original query. " 
                 f"Provide a score from 1 to 5 and a brief justification. " 
                 f"The output MUST be a valid JSON object conforming to this Pydantic schema: {CritiqueResult.model_json_schema()}",
            backstory="A meticulous analyst with a keen eye for detail and relevance.",
            verbose=True,
        )

    def query_optimizer_agent(self) -> Agent:
        """Agent responsible for refining the search query."""
        return Agent(
            role="Search Query Optimizer",
            goal="Rewrite a search query to be more effective, based on the critique of previous failed attempts.",
            backstory="A master of search-fu, you know exactly how to rephrase a query to get the best results.",
            verbose=True,
        )

# --- Task Definitions ---

class RagReflectionTasks:
    """Defines the tasks for each agent in the Reflective RAG process."""

    def retrieval_task(self, agent: Agent, query: str) -> Task:
        return Task(
            description=f"Retrieve information relevant to the query: '{query}'",
            expected_output="A block of text containing the retrieved context.",
            agent=agent,
        )

    def critique_task(self, agent: Agent, query: str, context: str) -> Task:
        return Task(
            description=f"Evaluate the following context based on the original query.\n\n" 
                        f"Original Query: {query}\n" 
                        f"Retrieved Context: {context}",
            expected_output=f"A valid JSON object with score, reasoning, and sufficiency, conforming to the specified schema.",
            agent=agent,
        )

    def optimization_task(self, agent: Agent, query: str, context: str, critique: str) -> Task:
        return Task(
            description=f"The previous attempt to answer '{query}' failed. " 
                        f"The retrieved context was: '{context}'.\n"
                        f"The critique was: '{critique}'.\n\n" 
                        f"Your task is to rewrite the original query to be more specific and effective.",
            expected_output="A new, optimized search query as a single string.",
            agent=agent,
        )

# --- Main Execution Loop (The Reflective RAG Controller) ---

def main(max_retries: int = 2):
    """Runs the Reflective RAG loop."""
    
    agents = RagReflectionAgents()
    tasks = RagReflectionTasks()

    retriever = agents.retriever_agent()
    critique = agents.critique_agent()
    optimizer = agents.query_optimizer_agent()

    original_query = "Tell me about CrewAI's new features."
    current_query = original_query

    for i in range(max_retries):
        print(f"\n--- Iteration {i + 1} ---")
        print(f"🔍 Current Query: {current_query}")

        # 1. Retrieve Context using a Crew with knowledge
        retrieval_crew = Crew(
            agents=[retriever], 
            tasks=[tasks.retrieval_task(retriever, current_query)], 
            knowledge_sources=[text_file_source], # Provide knowledge at the Crew level
            verbose=False
        )
        retrieved_context = retrieval_crew.kickoff()
        print(f"📄 Retrieved Context: \n{retrieved_context}\n")

        # 2. Critique the Context
        critique_crew = Crew(
            agents=[critique], 
            tasks=[tasks.critique_task(critique, original_query, retrieved_context)], 
            verbose=False
        )
        raw_critique_output = critique_crew.kickoff()
        critique_json_str = str(raw_critique_output) # Convert CrewOutput to string
        
        try:
            # Clean up potential markdown code blocks from the LLM output
            if critique_json_str.strip().startswith("```json"):
                critique_json_str = critique_json_str.strip()[7:-4].strip()
            
            critique_result = CritiqueResult.model_validate_json(critique_json_str)
            print(f"🧐 Critique: Score {critique_result.score}/5 - {critique_result.reasoning}")
        except Exception as e:
            print(f"❌ Error parsing critique: {e}. Raw output: '{critique_json_str}'. Aborting.")
            break

        # 3. Decide whether to end or retry
        if critique_result.is_sufficient:
            print("\n✅ Context is sufficient. Final Answer:")
            print(retrieved_context)
            return
        elif i < max_retries - 1:
            print("\n🤔 Context is not sufficient. Optimizing query...")
            # 4. Optimize the Query
            optimization_crew = Crew(
                agents=[optimizer], 
                tasks=[tasks.optimization_task(optimizer, original_query, retrieved_context, critique_result.model_dump_json())], 
                verbose=False
            )
            new_query = optimization_crew.kickoff()
            current_query = new_query
        else:
            print("\n❌ Max retries reached. Failed to find a sufficient answer.")
            break
    
if __name__ == "__main__":
    main()
