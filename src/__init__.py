#!/usr/bin/env python3
"""
CrewAI × Agentic Design Patterns Core Module
自動修正 SQLite 版本相容性問題
"""

import sys
import os

def _fix_sqlite():
    """自動修正 SQLite 版本問題"""
    try:
        # 嘗試導入 pysqlite3，如果可用就替代內建 sqlite3
        import pysqlite3.dbapi2 as sqlite3
        
        # 將 pysqlite3 註冊為 sqlite3 模組
        sys.modules['sqlite3'] = sqlite3
        sys.modules['sqlite3.dbapi2'] = sqlite3
        
        # 靜默修正，不輸出訊息
        return True
        
    except ImportError:
        # 如果無法導入 pysqlite3，繼續使用內建版本
        return False

# 在模組載入時自動執行修正
_fix_sqlite()

# 模組版本資訊
__version__ = "2.0.0"
__author__ = "iSpan Team"
__description__ = "CrewAI × Agentic Design Patterns - 完整的 AI Agent 教學與實作平台"

# 導出主要模組
from . import core
from . import patterns

__all__ = ['core', 'patterns'] 