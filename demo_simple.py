#!/usr/bin/env python3
"""
CrewAI × Agentic Design Patterns 簡化演示

展示已完成的核心邏輯和設計模式（無外部依賴）：
1. Reflection Pattern 自我批評機制
2. Planning Pattern WBS 規劃邏輯
3. 代碼解釋器安全檢查
4. 工具註冊表機制

運行方式: python demo_simple.py
"""

import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any


def print_banner(title: str):
    """打印橫幅"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def demo_reflection_pattern():
    """演示 Reflection Pattern 自我批評機制"""
    print_banner("Reflection Pattern 演示")
    
    # 簡化的自我批評邏輯
    class SimpleCritic:
        def analyze_content(self, content: str) -> Dict[str, Any]:
            issues = []
            score = 1.0
            
            # 長度檢查
            if len(content) < 100:
                issues.append("內容長度過短，需要更詳細的說明")
                score -= 0.3
            
            # 關鍵詞檢查
            if "AI" in content and "人工智慧" in content and "機器學習" not in content:
                issues.append("缺少 '機器學習' 相關內容")
                score -= 0.2
            
            # 結構檢查
            if not any(marker in content for marker in ["。", "？", "！"]):
                issues.append("缺少適當的句子結構")
                score -= 0.2
            
            # 專業術語密度
            tech_terms = ["AI", "人工智慧", "機器學習", "深度學習", "神經網絡"]
            term_count = sum(1 for term in tech_terms if term in content)
            if term_count / len(content.split()) > 0.3:
                issues.append("專業術語密度過高，可能影響可讀性")
                score -= 0.1
            
            return {
                "score": max(0.0, score),
                "issues": issues,
                "analysis_time": time.time()
            }
    
    # 測試內容
    test_content = """
    人工智慧正在快速發展。AI 技術包括機器學習和深度學習。
    這些技術在很多領域都有應用。醫療、金融、教育等行業都在使用 AI。
    AI 的發展會改變我們的生活和工作方式。
    """
    
    print("原始內容:")
    print(test_content.strip())
    
    # 執行批評分析
    critic = SimpleCritic()
    start_time = time.time()
    result = critic.analyze_content(test_content)
    analysis_time = time.time() - start_time
    
    print(f"\n反思結果:")
    print(f"  內容評分: {result['score']:.2f}/1.0")
    print(f"  分析耗時: {analysis_time:.3f}秒")
    print(f"  需要改進: {'是' if result['score'] < 0.8 else '否'}")
    
    if result['issues']:
        print(f"\n發現的問題:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"  {i}. {issue}")
    
    return result


def demo_planning_pattern():
    """演示 Planning Pattern WBS 規劃邏輯"""
    print_banner("Planning Pattern 演示")
    
    # 簡化的 WBS 規劃邏輯
    class SimpleWBSPlanner:
        def create_project_plan(self, description: str, weeks: int = 4) -> Dict[str, Any]:
            # 基於項目類型的模板
            if "軟體" in description or "開發" in description:
                phases = [
                    ("需求分析", 1.0, ["分析師"]),
                    ("系統設計", 1.5, ["架構師", "設計師"]),
                    ("開發實作", 2.0, ["開發者"]),
                    ("測試驗證", 1.0, ["測試工程師"]),
                    ("部署上線", 0.5, ["運維工程師"])
                ]
            elif "研究" in description:
                phases = [
                    ("文獻回顧", 1.0, ["研究員"]),
                    ("研究設計", 0.5, ["研究員"]),
                    ("數據收集", 1.5, ["研究員", "助理"]),
                    ("數據分析", 1.0, ["數據分析師"]),
                    ("報告撰寫", 1.0, ["研究員"])
                ]
            else:
                phases = [
                    ("項目啟動", 0.5, ["項目經理"]),
                    ("計劃制定", 0.5, ["項目經理"]),
                    ("執行實施", 2.0, ["團隊成員"]),
                    ("監控控制", 1.0, ["項目經理"]),
                    ("項目收尾", 0.5, ["項目經理"])
                ]
            
            # 計算時程
            total_weeks = sum(duration for _, duration, _ in phases)
            scale_factor = weeks / total_weeks if total_weeks > 0 else 1
            
            tasks = []
            current_week = 0
            
            for i, (name, duration, roles) in enumerate(phases):
                scaled_duration = duration * scale_factor
                tasks.append({
                    "id": f"task_{i+1}",
                    "name": name,
                    "duration_weeks": scaled_duration,
                    "start_week": current_week,
                    "end_week": current_week + scaled_duration,
                    "required_roles": roles,
                    "dependencies": [f"task_{i}"] if i > 0 else []
                })
                current_week += scaled_duration
            
            # 風險評估
            risks = []
            if weeks < 4:
                risks.append("時程較緊，可能需要加班或簡化功能")
            if any(len(task["required_roles"]) > 2 for task in tasks):
                risks.append("部分任務需要多種技能，可能存在資源衝突")
            
            return {
                "project_id": f"proj_{int(time.time())}",
                "description": description,
                "total_weeks": weeks,
                "tasks": tasks,
                "risks": risks,
                "created_at": datetime.now().isoformat()
            }
    
    # 創建項目計劃
    planner = SimpleWBSPlanner()
    project_plan = planner.create_project_plan(
        "開發一個多代理 AI 助手系統", 
        weeks=6
    )
    
    print("項目計劃:")
    print(f"  項目ID: {project_plan['project_id']}")
    print(f"  描述: {project_plan['description']}")
    print(f"  總時長: {project_plan['total_weeks']} 週")
    
    print(f"\n任務分解:")
    for task in project_plan['tasks']:
        print(f"  • {task['name']}")
        print(f"    時長: {task['duration_weeks']:.1f} 週")
        print(f"    所需角色: {', '.join(task['required_roles'])}")
        if task['dependencies']:
            print(f"    依賴: {', '.join(task['dependencies'])}")
        print()
    
    print(f"風險評估:")
    for risk in project_plan['risks']:
        print(f"  ⚠️  {risk}")
    
    return project_plan


def demo_code_security():
    """演示代碼安全檢查機制"""
    print_banner("代碼安全檢查演示")
    
    # 簡化的安全檢查邏輯
    class CodeSecurityChecker:
        def __init__(self):
            self.dangerous_patterns = [
                r'import\s+os',
                r'import\s+sys', 
                r'import\s+subprocess',
                r'open\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\('
            ]
        
        def check_safety(self, code: str) -> Dict[str, Any]:
            violations = []
            
            for pattern in self.dangerous_patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    violations.append(f"發現危險模式: {pattern}")
            
            # 檢查代碼複雜度
            lines = code.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            complexity_score = 0
            if len(non_empty_lines) > 50:
                complexity_score += 1
            
            # 檢查嵌套深度
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)
            
            if max_indent > 4:
                violations.append("代碼嵌套過深，可能難以維護")
            
            return {
                "is_safe": len(violations) == 0,
                "violations": violations,
                "complexity_score": complexity_score,
                "max_nesting_level": max_indent,
                "line_count": len(non_empty_lines)
            }
    
    # 測試代碼範例
    test_codes = [
        # 安全代碼
        """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(8)]
print("結果:", result)
""",
        # 不安全代碼
        """
import os
import sys

def dangerous_function():
    os.system("rm -rf /")
    eval("print('dangerous')")
    
dangerous_function()
"""
    ]
    
    checker = CodeSecurityChecker()
    
    for i, code in enumerate(test_codes, 1):
        print(f"測試代碼 {i}:")
        print("```python")
        print(code.strip())
        print("```")
        
        result = checker.check_safety(code)
        
        safety_icon = "✅" if result['is_safe'] else "❌"
        print(f"\n安全檢查結果: {safety_icon}")
        print(f"  安全性: {'通過' if result['is_safe'] else '不通過'}")
        print(f"  代碼行數: {result['line_count']}")
        print(f"  最大嵌套層級: {result['max_nesting_level']}")
        
        if result['violations']:
            print(f"  安全問題:")
            for violation in result['violations']:
                print(f"    • {violation}")
        print()
    
    return checker


def demo_tool_registry():
    """演示工具註冊表機制"""
    print_banner("工具註冊表演示")
    
    # 簡化的工具註冊表
    class SimpleToolRegistry:
        def __init__(self):
            self.tools = {}
            self.categories = {}
        
        def register_tool(self, name: str, description: str, category: str = "general"):
            self.tools[name] = {
                "name": name,
                "description": description,
                "category": category,
                "registered_at": datetime.now().isoformat()
            }
            
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(name)
        
        def list_tools(self) -> List[str]:
            return list(self.tools.keys())
        
        def get_tool_info(self, name: str) -> Dict[str, Any]:
            return self.tools.get(name, {})
        
        def get_tools_by_category(self, category: str) -> List[str]:
            return self.categories.get(category, [])
        
        def get_statistics(self) -> Dict[str, Any]:
            return {
                "total_tools": len(self.tools),
                "categories": list(self.categories.keys()),
                "tools_per_category": {cat: len(tools) for cat, tools in self.categories.items()}
            }
    
    # 創建並註冊工具
    registry = SimpleToolRegistry()
    
    # 註冊一些示例工具
    tools_to_register = [
        ("web_search", "網路搜索工具，支援多個搜索引擎", "data_retrieval"),
        ("code_interpreter", "安全的代碼執行環境", "data_processing"),
        ("text_analyzer", "文本分析和處理工具", "data_processing"),
        ("file_manager", "文件操作和管理工具", "file_operations"),
        ("api_client", "REST API 調用工具", "networking")
    ]
    
    for name, desc, category in tools_to_register:
        registry.register_tool(name, desc, category)
        print(f"✓ 註冊工具: {name}")
    
    print(f"\n工具統計:")
    stats = registry.get_statistics()
    print(f"  總工具數: {stats['total_tools']}")
    print(f"  類別數: {len(stats['categories'])}")
    
    print(f"\n按類別分組:")
    for category, tools in stats['tools_per_category'].items():
        print(f"  {category}: {tools} 個工具")
        for tool_name in registry.get_tools_by_category(category):
            tool_info = registry.get_tool_info(tool_name)
            print(f"    - {tool_name}: {tool_info['description']}")
    
    return registry


def main():
    """主演示函數"""
    print("🤖 CrewAI × Agentic Design Patterns 簡化演示")
    print("=" * 80)
    print("本演示展示核心邏輯和設計模式（無外部依賴）")
    
    try:
        # 1. Reflection Pattern 演示
        reflection_result = demo_reflection_pattern()
        
        # 2. Planning Pattern 演示  
        project_plan = demo_planning_pattern()
        
        # 3. 代碼安全檢查演示
        security_checker = demo_code_security()
        
        # 4. 工具註冊表演示
        tool_registry = demo_tool_registry()
        
        # 總結
        print_banner("演示總結")
        print("✅ 已驗證的核心邏輯:")
        print("  • Reflection Pattern 自我批評機制")
        print("  • Planning Pattern WBS 任務分解")
        print("  • 代碼安全檢查和驗證")
        print("  • 工具註冊表和分類管理")
        
        print("\n📊 演示統計:")
        print(f"  • 反思分析評分: {reflection_result['score']:.2f}")
        print(f"  • 項目計劃任務數: {len(project_plan['tasks'])}")
        print(f"  • 安全檢查完成: 2 個代碼樣本")
        print(f"  • 工具註冊數量: {tool_registry.get_statistics()['total_tools']}")
        
        print("\n🎯 核心特色:")
        print("  • 基於 First Principles 的設計模式")
        print("  • 理論與實務結合的教學方法")
        print("  • 模組化和可擴展的架構")
        print("  • 完整的安全檢查機制")
        
        print("\n🌟 這只是一個簡化演示！")
        print("完整版本包含:")
        print("  - CrewAI 框架整合")
        print("  - 多層次記憶系統")
        print("  - 真實的網路搜索功能")
        print("  - 實際的代碼執行沙盒")
        print("  - 複雜的多代理協作")
        
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 