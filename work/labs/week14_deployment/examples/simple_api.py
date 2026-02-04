#!/usr/bin/env python3
"""
Simple FastAPI application for deployment demonstration
展示如何将 CrewAI 应用部署到生产环境
"""

import sys
import os
import time
from typing import Dict, Any
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: uv add fastapi uvicorn prometheus-client")
    sys.exit(1)

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew, Process
    from src.core.tools.search_tool import TavilySearchTool
except ImportError:
    print("CrewAI components not found. Using mock implementations.")

    class MockAgent:
        def __init__(self, **kwargs):
            self.role = kwargs.get('role', 'Mock Agent')

    class MockTask:
        def __init__(self, **kwargs):
            self.description = kwargs.get('description', 'Mock Task')

    class MockCrew:
        def __init__(self, **kwargs):
            self.agents = kwargs.get('agents', [])

        def kickoff(self):
            return "Mock crew execution completed"

    Agent = MockAgent
    Task = MockTask
    Crew = MockCrew

# Prometheus metrics
REQUEST_COUNT = Counter('crewai_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('crewai_request_duration_seconds', 'Request duration')
CREW_EXECUTIONS = Counter('crewai_crew_executions_total', 'Total crew executions', ['status'])
CREW_DURATION = Histogram('crewai_crew_duration_seconds', 'Crew execution duration')

# FastAPI app
app = FastAPI(
    title="CrewAI Deployment Demo",
    description="A simple CrewAI application for deployment demonstration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class CrewRequest(BaseModel):
    topic: str
    max_iterations: int = 3

class CrewResponse(BaseModel):
    status: str
    result: str
    execution_time: float
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, str]

# Global state
app_start_time = time.time()

# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers"""
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()

    components = {
        "database": "healthy",  # In real app, check DB connection
        "redis": "healthy",     # In real app, check Redis connection
        "external_apis": "healthy"  # In real app, check external APIs
    }

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        components=components
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ready").inc()

    # In a real application, check if all dependencies are ready
    uptime = time.time() - app_start_time

    if uptime < 10:  # Still starting up
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready", "uptime_seconds": uptime}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Main application endpoints
@app.post("/crew/execute", response_model=CrewResponse)
async def execute_crew(request: CrewRequest, background_tasks: BackgroundTasks):
    """Execute a CrewAI crew with the given topic"""
    start_time = time.time()

    with REQUEST_DURATION.time():
        REQUEST_COUNT.labels(method="POST", endpoint="/crew/execute").inc()

        try:
            # Create a simple crew for demonstration
            researcher = Agent(
                role='Research Analyst',
                goal=f'Research and analyze information about {request.topic}',
                backstory='You are an expert research analyst with years of experience.',
                verbose=True
            )

            research_task = Task(
                description=f'Conduct comprehensive research on {request.topic} and provide key insights.',
                expected_output='A detailed research report with key findings and insights.',
                agent=researcher
            )

            crew = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute the crew
            result = crew.kickoff()
            execution_time = time.time() - start_time

            CREW_EXECUTIONS.labels(status="success").inc()
            CREW_DURATION.observe(execution_time)

            return CrewResponse(
                status="completed",
                result=str(result),
                execution_time=execution_time,
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            execution_time = time.time() - start_time
            CREW_EXECUTIONS.labels(status="error").inc()
            CREW_DURATION.observe(execution_time)

            raise HTTPException(
                status_code=500,
                detail=f"Crew execution failed: {str(e)}"
            )

@app.get("/crew/status/{task_id}")
async def get_crew_status(task_id: str):
    """Get the status of a crew execution (mock implementation)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/crew/status").inc()

    # In a real implementation, this would check the actual task status
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def app_info():
    """Get application information"""
    REQUEST_COUNT.labels(method="GET", endpoint="/info").inc()

    return {
        "name": "CrewAI Deployment Demo",
        "version": "1.0.0",
        "uptime_seconds": time.time() - app_start_time,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": sys.version,
        "features": [
            "CrewAI Integration",
            "Prometheus Metrics",
            "Health Checks",
            "Docker Ready",
            "Kubernetes Ready"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    REQUEST_COUNT.labels(method=request.method, endpoint="404").inc()
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    REQUEST_COUNT.labels(method=request.method, endpoint="500").inc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print("🚀 CrewAI Deployment Demo starting up...")
    print(f"📊 Metrics available at: /metrics")
    print(f"🏥 Health check available at: /health")
    print(f"📖 API documentation available at: /docs")

if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )