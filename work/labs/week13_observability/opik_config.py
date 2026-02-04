"""
Opik Configuration and Utilities for CrewAI Observability

This module provides configuration and utility functions for integrating
Opik observability framework with CrewAI agents and crews.

Opik is a modern observability framework that provides:
- End-to-end tracing of agent workflows
- Performance monitoring and analytics
- Cost tracking and optimization insights
- Real-time debugging capabilities
"""

import os
import functools
from typing import Dict, Any, Optional, Callable
from dotenv import load_dotenv

# Import opik with proper error handling
try:
    import opik
except ImportError:
    print("Opik not installed. Please run: pip install opik")
    raise

# Load environment variables
load_dotenv()

class OpikConfig:
    """Configuration manager for Opik integration"""

    def __init__(self):
        self.api_key = os.getenv("OPIK_API_KEY")
        self.workspace = os.getenv("OPIK_WORKSPACE", "crewai-observability")
        self.project_name = os.getenv("OPIK_PROJECT_NAME", "week13-observability")
        self.local_deployment = os.getenv("OPIK_LOCAL", "false").lower() == "true"

    def get_client(self):
        """Get configured Opik client"""
        # Configure Opik based on official documentation
        if self.local_deployment:
            # For local Opik deployment (self-hosted)
            return opik.configure(
                use_local=True,
                url="http://localhost:5173"  # Default local URL
            )
        else:
            # For cloud deployment - configure with API key if available
            if self.api_key:
                return opik.configure(api_key=self.api_key)
            else:
                # Use default configuration (will prompt for setup)
                return opik.configure()

# Global configuration instance
config = OpikConfig()

# Initialize Opik client
try:
    client = config.get_client()
    print("✅ Opik client configured successfully")
except Exception as e:
    print(f"⚠️ Opik configuration failed: {e}")
    print("Continuing without Opik tracking...")
    client = None

def track_agent_execution(agent_name: str, task_description: str = ""):
    """
    Decorator to track agent execution with Opik

    Args:
        agent_name: Name of the agent being tracked
        task_description: Optional description of the task
    """
    def decorator(func: Callable) -> Callable:
        @opik.track(name=f"agent_execution_{agent_name}")
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log execution start
            print(f"🔍 Tracking agent execution: {agent_name}")

            try:
                result = func(*args, **kwargs)
                # Log successful execution
                print(f"✅ Agent {agent_name} completed successfully")
                return result
            except Exception as e:
                # Log error details
                print(f"❌ Agent {agent_name} failed: {str(e)}")
                raise

        return wrapper
    return decorator

def track_tool_usage(tool_name: str):
    """
    Decorator to track tool usage with Opik

    Args:
        tool_name: Name of the tool being tracked
    """
    def decorator(func: Callable) -> Callable:
        @opik.track(name=f"tool_usage_{tool_name}")
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"🔧 Tracking tool usage: {tool_name}")

            try:
                result = func(*args, **kwargs)
                print(f"✅ Tool {tool_name} executed successfully")
                return result
            except Exception as e:
                print(f"❌ Tool {tool_name} failed: {str(e)}")
                raise

        return wrapper
    return decorator

def track_crew_workflow(crew_name: str = "default_crew"):
    """
    Decorator to track entire crew workflow with Opik

    Args:
        crew_name: Name of the crew being tracked
    """
    def decorator(func: Callable) -> Callable:
        @opik.track(name=f"crew_workflow_{crew_name}")
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"🚀 Tracking crew workflow: {crew_name}")

            try:
                result = func(*args, **kwargs)
                print(f"✅ Crew workflow {crew_name} completed successfully")
                return result
            except Exception as e:
                print(f"❌ Crew workflow {crew_name} failed: {str(e)}")
                raise

        return wrapper
    return decorator

def log_agent_metrics(agent_name: str, metrics: Dict[str, Any]):
    """
    Log custom metrics for an agent

    Args:
        agent_name: Name of the agent
        metrics: Dictionary of metrics to log
    """
    print(f"📊 Logging metrics for {agent_name}: {metrics}")
    # In a real implementation, this would use Opik's scoring/feedback API
    # For now, we'll log to console as a placeholder

def log_cost_metrics(operation: str, cost: float, tokens_used: int = None):
    """
    Log cost and usage metrics

    Args:
        operation: Name of the operation
        cost: Cost in USD
        tokens_used: Number of tokens used (optional)
    """
    metrics = {
        "operation": operation,
        "cost_usd": cost,
        "metric_type": "cost_tracking"
    }

    if tokens_used is not None:
        metrics["tokens_used"] = tokens_used
        metrics["cost_per_token"] = cost / tokens_used if tokens_used > 0 else 0

    print(f"💰 Cost metrics for {operation}: ${cost:.4f}, tokens: {tokens_used}")

# Context manager for manual trace creation
class OpikTrace:
    """Context manager for creating manual traces"""

    def __init__(self, name: str, tags: Optional[list] = None):
        self.name = name
        self.tags = tags or ["crewai", "manual_trace"]
        self.trace_started = False

    def __enter__(self):
        print(f"🔍 Starting trace: {self.name}")
        self.trace_started = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"❌ Trace {self.name} failed: {exc_val}")
        else:
            print(f"✅ Trace {self.name} completed successfully")
        self.trace_started = False

    def log_message(self, message: str, level: str = "info"):
        """Log a message within the trace"""
        print(f"📝 [{level.upper()}] {self.name}: {message}")