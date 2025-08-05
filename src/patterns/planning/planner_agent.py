from crewai import Agent, Task

class PlannerAgent:
    """
    A specialized agent responsible for breaking down complex goals into a series of
    executable tasks. This agent embodies the Planning Pattern for Hierarchical workflows.
    """
    def __init__(self):
        self.planner = Agent(
            role="Master Planner",
            goal="Analyze complex goals and delegate specific tasks to appropriate team members. Coordinate the workflow to ensure all tasks are completed efficiently.",
            backstory=(
                "You are a strategic project manager and team coordinator with extensive experience in hierarchical planning. "
                "Your expertise lies in analyzing complex objectives, identifying the right team members for specific tasks, "
                "and orchestrating collaborative workflows. You understand each team member's strengths and can efficiently "
                "delegate work while maintaining oversight of the entire project. Your delegation style is clear, specific, "
                "and includes all necessary context for successful task completion."
            ),
            allow_delegation=True,  # 關鍵：啟用委派功能
            verbose=True,
            max_iter=10,  # 限制迭代次數避免無限循環
            memory=True   # 啟用記憶功能以跟蹤委派的任務
        )

    def plan_workflow(self, high_level_goal: str) -> Task:
        """
        Creates a planning task for the PlannerAgent to decompose a high-level goal.
        """
        return Task(
            description=f"""
                Break down the following high-level goal into a series of actionable, sequential tasks.
                
                **High-Level Goal:**
                {high_level_goal}

                **Your Output MUST be a numbered list of tasks.**
                Each task should be a clear, concise instruction for another agent to follow.
                Focus on creating a logical flow of actions. Do not add any introductory or concluding remarks.
                
                Example:
                1. Research the target audience for a new coffee brand.
                2. Analyze the top 3 competitors in the premium coffee market.
                3. Develop a unique selling proposition (USP) for the new brand.
                4. Create a marketing slogan based on the USP.
            """,
            expected_output="A numbered list of tasks that logically break down the high-level goal.",
            agent=self.planner
        )

# Example usage (for testing or direct instantiation)
if __name__ == '__main__':
    planner_agent_logic = PlannerAgent()
    
    goal = "Create a successful marketing campaign for a new brand of sustainable sneakers."
    planning_task = planner_agent_logic.plan_workflow(goal)
    
    # This is a conceptual test. In a real scenario, this task would be
    # the first step in a hierarchical Crew process.
    print("--- Planner Agent ---")
    print(f"Role: {planner_agent_logic.planner.role}")
    print(f"Goal: {planner_agent_logic.planner.goal}")
    print("\n--- Planning Task ---")
    print(f"Description:\n{planning_task.description}")
    print(f"\nExpected Output:\n{planning_task.expected_output}")

