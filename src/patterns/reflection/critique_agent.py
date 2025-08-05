# src/patterns/reflection/critique_agent.py

import json
from typing import List, Optional
from pydantic import BaseModel, Field

from crewai import Agent, Task

# --- Data Models for Critique Results ---
# These models define the structured output we expect from the critique agent.

class CritiqueScore(BaseModel):
    """Represents a single score for a specific evaluation criterion."""
    category: str = Field(..., description="The evaluation criterion being scored, e.g., 'Clarity' or 'Technical Accuracy'.")
    score: float = Field(..., description="The numerical score on a scale of 1-10.", ge=1, le=10)
    reasoning: str = Field(..., description="A brief justification for the given score.")

class CritiqueResult(BaseModel):
    """Represents the complete critique result for a piece of content."""
    overall_score: float = Field(..., description="The overall quality score, weighted average of all categories.", ge=1, le=10)
    should_iterate: bool = Field(..., description="A boolean flag indicating if the content needs further refinement.")
    scores: List[CritiqueScore] = Field(..., description="A list of scores for each evaluation criterion.")

    def get_critique_summary(self) -> str:
        """Generates a human-readable summary of the critique."""
        summary = f"Overall Score: {self.overall_score:.1f}/10. "
        summary += "Needs Improvement." if self.should_iterate else "Quality target met."
        for item in self.scores:
            summary += f"\n- {item.category}: {item.score:.1f}/10. Reasoning: {item.reasoning}"
        return summary

# --- Configuration for the Critique Agent ---

class CritiqueConfig(BaseModel):
    """
    Configuration object for the ReflectionCritiqueAgent.
    This is where you define HOW a piece of content should be evaluated.
    """
    quality_threshold: float = Field(
        default=8.0,
        description="The minimum overall score required to stop the refinement process.",
        ge=1, le=10
    )
    evaluation_criteria: List[str] = Field(
        ...,
        description="A list of criteria to evaluate the content against. E.g., ['Clarity', 'Conciseness']."
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional, additional instructions to guide the critique agent's evaluation process."
    )

# --- The Critique Agent Logic ---

class ReflectionCritiqueAgent:
    """
    A factory for creating a specialized CrewAI agent and task for critiquing content.
    Its primary role is to take a configuration (CritiqueConfig) and use it to
    evaluate content based on a set of rules.
    """

    # This is the prompt template for the critique task.
    # It's designed to be clear and to instruct the LLM to return a JSON object
    # that matches our Pydantic models (CritiqueScore, CritiqueResult).
    #
    # DEVELOPER NOTE: You can customize this prompt to change the evaluation style,
    # but ensure the output format instructions remain clear to get a parsable JSON.
    _CRITIQUE_PROMPT_TEMPLATE = '''
    As a professional quality analyst, your task is to provide a rigorous and objective critique of the following content.

    **Content to Review:**
    ---
    {content_to_review}
    ---

    **Evaluation Instructions:**
    1.  **Analyze Thoroughly**: Carefully read and understand the provided content.
    2.  **Evaluate Against Criteria**: Assess the content based on the following criteria:
        {evaluation_criteria}
    3.  **Score Each Criterion**: For each criterion, provide a score from 1 (poor) to 10 (excellent) and a brief, clear reasoning for your score.
    4.  **Calculate Overall Score**: Compute a weighted overall score that reflects the content's quality.
    5.  **Determine Next Steps**: Based on your calculated overall score and the quality threshold of {quality_threshold}/10, decide if the content `should_iterate` (True) for further improvement or if it meets the quality standard (False).
    {custom_instructions_section}
    **Output Format:**
    You MUST provide your response as a single, valid JSON object. Do not include any text or formatting outside of this JSON.
    The JSON object must conform to the following structure:
    {{
      "overall_score": <float>,
      "should_iterate": <boolean>,
      "scores": [
        {{
          "category": "<name_of_criterion>",
          "score": <float>,
          "reasoning": "<your_reasoning>"
        }},
        ...
      ]
    }}
    '''

    def __init__(self, config: CritiqueConfig):
        """
        Initializes the critique agent factory with a specific configuration.

        Args:
            config: A CritiqueConfig object defining the evaluation rules.
        """
        self.config = config

    def create_agent(self, role: str, goal: str, backstory: Optional[str] = None) -> Agent:
        """
        Creates a CrewAI Agent configured for critique tasks.

        Args:
            role: The specific role for the agent (e.g., "Technical Documentation Reviewer").
            goal: The primary goal of this agent.
            backstory: The backstory to give the agent context.

        Returns:
            A CrewAI Agent instance.
        """
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory or "You are a meticulous and objective quality analyst.",
            verbose=True,
            allow_delegation=False,
            memory=False # Critique agents are typically stateless.
        )

    def create_critique_task(self, content_to_review: str, agent: Agent) -> Task:
        """
        Creates a CrewAI Task that instructs the agent to perform the critique.

        Args:
            content_to_review: The actual text content to be evaluated.
            agent: The CrewAI agent that will execute this task.

        Returns:
            A CrewAI Task instance.
        """
        custom_instructions_section = ""
        if self.config.custom_instructions:
            custom_instructions_section = f"\n**Additional Instructions:**\n{self.config.custom_instructions}"

        formatted_prompt = self._CRITIQUE_PROMPT_TEMPLATE.format(
            content_to_review=content_to_review,
            evaluation_criteria="\n".join([f"- {c}" for c in self.config.evaluation_criteria]),
            quality_threshold=self.config.quality_threshold,
            custom_instructions_section=custom_instructions_section
        )

        return Task(
            description=formatted_prompt,
            expected_output="A single, valid JSON object containing the full critique.",
            agent=agent
        )

    def parse_critique_result(self, llm_output: str) -> CritiqueResult:
        """
        Parses the JSON output from the LLM into a structured CritiqueResult object.

        Args:
            llm_output: The raw string output from the critique task execution.

        Returns:
            A CritiqueResult object.

        Raises:
            ValueError: If the output is not valid JSON or doesn't match the model.
        """
        try:
            # The LLM output might contain markdown code blocks (```json ... ```)
            if "```json" in llm_output:
                json_str = llm_output.split("```json")[1].split("```")[0].strip()
            else:
                json_str = llm_output

            data = json.loads(json_str)
            return CritiqueResult.model_validate(data)
        except (json.JSONDecodeError, IndexError) as e:
            raise ValueError(f"Failed to parse critique JSON. Error: {e}\nRaw output: {llm_output}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred during critique parsing: {e}\nRaw output: {llm_output}")
