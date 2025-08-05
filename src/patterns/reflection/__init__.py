#!/usr/bin/env python3
"""
Reflection Pattern

實作 Self-Refine 論文中的反思機制，支援：
- 自我評估與批評
- 迭代式品質改進
- 可配置的評估標準
- 自動品質閾值檢查

主要組件：
- ReflectionCritiqueAgent: 評估與批評 Agent
- SelfRefineWorkflow: 完整的反思循環工作流程
- SelfRefineCrewBuilder: 便捷的 Crew 建構器

使用範例：
```python
from src.patterns.reflection import create_weather_critique_agent, SelfRefineWorkflow

# 創建評估 Agent
critique_agent = create_weather_critique_agent(quality_threshold=8.0)

# 創建工作流程
workflow = SelfRefineWorkflow(critique_agent, max_iterations=3)

# 創建 Crew 並執行
crew = workflow.create_refine_crew(generator_agent, refiner_agent, initial_task)
result = crew.kickoff(inputs={"topic": "weather"})
```
"""

from .critique_agent import (
    ReflectionCritiqueAgent,
    CritiqueConfig,
    CritiqueResult,
    CritiqueScore
)

from .self_refine import (
    SelfRefineWorkflow,
    RefineIteration
)

__all__ = [
    # Core classes
    "ReflectionCritiqueAgent",
    "SelfRefineWorkflow",
    
    # Data structures
    "CritiqueConfig",
    "CritiqueResult", 
    "CritiqueScore",
    "RefineIteration",
]

# 版本資訊
__version__ = "0.1.0"
__author__ = "CrewAI Course"
__description__ = "Reflection Pattern implementation for iterative self-improvement"
