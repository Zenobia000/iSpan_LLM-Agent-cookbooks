#!/usr/bin/env python3
"""
導入輔助模組

解決 work/labs 目錄中腳本無法導入 src 模組的問題
用法：在每個實驗腳本開頭導入此模組
"""

import sys
import os
from pathlib import Path

def setup_imports():
    """設置導入路徑，讓腳本可以導入 src 模組"""
    # 找到專案根目錄 (包含 src 目錄的位置)
    current_file = Path(__file__).resolve()
    
    # 從當前文件向上查找直到找到包含 src 目錄的根目錄
    project_root = current_file.parent
    while project_root != project_root.parent:
        if (project_root / "src").exists():
            break
        project_root = project_root.parent
    else:
        raise RuntimeError("無法找到專案根目錄 (包含 src 目錄)")
    
    # 將專案根目錄添加到 Python 路徑
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 驗證 src 模組可以導入
    try:
        import src
        print(f"✅ 成功設置導入路徑: {project_root}")
        return project_root
    except ImportError as e:
        raise RuntimeError(f"設置導入路徑後仍無法導入 src 模組: {e}")

def ensure_env_loaded(project_root: Path = None):
    """確保環境變數已載入"""
    if project_root is None:
        project_root = setup_imports()
    
    env_file = project_root / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ 已載入環境變數: {env_file}")
    else:
        print(f"⚠️ 未找到 .env 文件: {env_file}")

def init_labs():
    """完整的實驗室初始化"""
    project_root = setup_imports()
    ensure_env_loaded(project_root)
    return project_root

# 自動初始化 (當此模組被導入時)
if __name__ != "__main__":
    init_labs()

# 測試功能
if __name__ == "__main__":
    print("🧪 測試導入輔助模組")
    print("=" * 50)
    
    try:
        project_root = init_labs()
        print(f"專案根目錄: {project_root}")
        
        # 測試導入核心模組
        from src.core.tools import OpenWeatherMapTool, TavilySearchTool
        print("✅ 成功導入 src.core.tools")
        
        from src.patterns.planning.planner_agent import PlannerAgent
        print("✅ 成功導入 src.patterns.planning")
        
        print("\n🎯 導入輔助模組運作正常！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()