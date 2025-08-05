# src/patterns/reflection/self_refine.py

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process

# Import the necessary components from the critique_agent module.
# This highlights the dependency: SelfRefineWorkflow USES a ReflectionCritiqueAgent.
from .critique_agent import ReflectionCritiqueAgent, CritiqueResult

# --- Data Models for Tracking the Refinement Process ---

class RefineIteration(BaseModel):
    """
A record of a single iteration in the self-refine workflow.
    This helps in tracking the progress and quality improvements over time.
    """
    iteration_count: int = Field(..., description="The sequence number of this iteration (starting from 1).")
    content: str = Field(..., description="The version of the content produced in this iteration.")
    critique: CritiqueResult = Field(..., description="The critique received for this version of the content.")
    improvement_score: float = Field(..., description="The overall quality score for this iteration.")

# --- The Self-Refine Workflow Coordinator ---

class SelfRefineWorkflow:
    """
    Coordinates the iterative self-refinement process.
    This class orchestrates the core "Generate -> Critique -> Refine" loop.
    """

    # This is the prompt template for the refinement task.
    # It guides the `refiner_agent` on how to improve the content based on feedback.
    #
    # DEVELOPER NOTE: This is a key area for customization.
    # You can modify this prompt to change how the agent refines the content.
    # For example, you could ask it to focus on specific areas, adopt a different tone,
    # or completely rewrite sections.
    _REFINE_PROMPT_TEMPLATE = '''
    Your task is to refine the following content based on the provided critique.
    Analyze the feedback carefully and apply the necessary improvements to enhance the content's quality.

    **Original Content:**
    ---
    {original_content}
    ---

    **Critique and Suggestions for Improvement:**
    ---
    {critique_summary}
    ---

    **Your Goal:**
    Produce a new, improved version of the content that directly addresses the critique.
    Focus on the areas highlighted as needing improvement while preserving the strengths of the original.

    Return only the full, refined content. Do not include any other commentary.
    '''

    def __init__(self, critique_agent: ReflectionCritiqueAgent, max_iterations: int = 3, verbose: bool = True):
        """
        Initializes the self-refine workflow coordinator.

        Args:
            critique_agent: An instance of ReflectionCritiqueAgent. This is the "expert"
                            that will evaluate the content at each step. It must be
                            pre-configured with the desired evaluation criteria.
            max_iterations: The maximum number of refinement loops to perform.
            verbose: Whether to print detailed progress during the workflow.
        """
        if not isinstance(critique_agent, ReflectionCritiqueAgent):
            raise TypeError("critique_agent must be an instance of ReflectionCritiqueAgent")
        self.critique_agent = critique_agent
        self.max_iterations = max_iterations
        self.verbose = verbose

    def run_iterative_refine(
        self,
        generator_agent: Agent,
        refiner_agent: Agent,
        initial_task_description: str,
        expected_output: str,
        inputs: Dict[str, Any],
        topic: str
    ) -> Tuple[str, List[RefineIteration]]:
        """
        Executes the full "Generate -> Critique -> Refine" loop.

        Args:
            generator_agent: The agent responsible for creating the initial content.
            refiner_agent: The agent responsible for improving the content based on critique.
            initial_task_description: The prompt for the initial content generation task.
            expected_output: The expected output description for CrewAI tasks.
            inputs: A dictionary of inputs for the initial task.
            topic: A short description of the content's topic (e.g., "API documentation").

        Returns:
            A tuple containing the final, refined content and a list of all refinement iterations.
        """
        iterations_history: List[RefineIteration] = []
        current_content = ""

        for i in range(self.max_iterations):
            iteration_num = i + 1
            if self.verbose:
                print(f"\n===== Iteration {iteration_num}/{self.max_iterations} =====")

            # --- Step 1: Generate or Refine Content ---
            if iteration_num == 1:
                # First iteration: Generate the initial draft.
                if self.verbose: print("Step 1: Generating initial content...")
                task = Task(description=initial_task_description, expected_output=expected_output, agent=generator_agent)
                crew = Crew(agents=[generator_agent], tasks=[task], process=Process.sequential)
                current_content = crew.kickoff(inputs=inputs)
            else:
                # Subsequent iterations: Refine the existing content.
                if self.verbose: print("Step 1: Refining content based on feedback...")
                critique_summary = iterations_history[-1].critique.get_critique_summary()
                refine_prompt = self._REFINE_PROMPT_TEMPLATE.format(
                    original_content=current_content,
                    critique_summary=critique_summary
                )
                task = Task(description=refine_prompt, expected_output=expected_output, agent=refiner_agent)
                crew = Crew(agents=[refiner_agent], tasks=[task], process=Process.sequential)
                current_content = crew.kickoff()

            # --- Step 2: Critique the Content ---
            if self.verbose: print("Step 2: Critiquing the generated content...")
            critique_task_agent = self.critique_agent.create_agent(
                role=f"{topic.title()} Quality Analyst",
                goal=f"Provide an objective, detailed critique of the {topic}."
            )
            critique_task = self.critique_agent.create_critique_task(
                content_to_review=current_content,
                agent=critique_task_agent
            )
            critique_crew = Crew(agents=[critique_task_agent], tasks=[critique_task], process=Process.sequential)
            critique_output = critique_crew.kickoff()
            critique_result = self.critique_agent.parse_critique_result(str(critique_output))

            # --- Step 3: Record the Iteration and Decide Next Steps ---
            if self.verbose: print("Step 3: Recording iteration and checking quality threshold...")
            iteration_record = RefineIteration(
                iteration_count=iteration_num,
                content=str(current_content),
                critique=critique_result,
                improvement_score=critique_result.overall_score
            )
            iterations_history.append(iteration_record)

            if self.verbose:
                print(f"Critique Result: Overall Score = {critique_result.overall_score:.1f}/10")
                print(f"Needs Further Iteration: {critique_result.should_iterate}")

            if not critique_result.should_iterate:
                if self.verbose: print("\nQuality threshold met. Concluding refinement process.")
                break
            elif iteration_num == self.max_iterations:
                if self.verbose: print("\nMaximum iterations reached. Concluding refinement process.")

        return current_content, iterations_history
