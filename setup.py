#!/usr/bin/env python3
"""
CrewAI Agentic Course Setup
讓 src 模組可作為 Python 包安裝和導入
"""

from setuptools import setup, find_packages
from pathlib import Path

# 讀取 README
README_PATH = Path(__file__).parent / "README.md"
long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

# 讀取版本信息
VERSION = "0.1.0"

setup(
    name="crewai-agentic-course",
    version=VERSION,
    description="CrewAI × Agentic Design Patterns 完整教案",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CrewAI Course",
    author_email="course@example.com",
    url="https://github.com/your-org/crewai-agentic-course",
    
    # 包配置
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Python 版本要求
    python_requires=">=3.10,<3.13",
    
    # 依賴管理 (與 pyproject.toml 保持一致)
    install_requires=[
        "crewai>=0.83.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "pysqlite3-binary>=0.5.0",
    ],
    
    # 開發依賴
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "llama": [
            "llama-index>=0.13.0",
            "llama-index-embeddings-cohere>=0.6.0",
            "llama-index-readers-web>=0.5.0",
            "llama-index-readers-file",
            "llama-index-readers-oxylabs",
            "llama-index-readers-docling",
            "llama-index-tools-scrapegraphai",
            "llama-index-tools-brightdata",
        ],
        "tools": [
            "beautifulsoup4>=4.13.4",
            "trafilatura>=2.0.0",
            "html2text",
        ]
    },
    
    # 分類標籤
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    
    # 命令行工具 (可選)
    entry_points={
        "console_scripts": [
            "crewai-course=core.cli:main",
        ],
    },
    
    # 包含額外文件
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yaml", "*.yml"],
    },
    
    # 關鍵詞
    keywords="crewai, ai, agent, multi-agent, agentic-patterns, llm",
    
    # 專案 URLs
    project_urls={
        "Bug Reports": "https://github.com/your-org/crewai-agentic-course/issues",
        "Source": "https://github.com/your-org/crewai-agentic-course",
        "Documentation": "https://your-org.github.io/crewai-agentic-course/",
    },
)