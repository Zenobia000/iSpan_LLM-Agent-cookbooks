#!/usr/bin/env python3
"""
Opik Setup Test Script
测试 Opik 集成是否正确配置
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_opik_import():
    """测试 Opik 是否可以正确导入"""
    try:
        import opik
        print("✅ Opik 导入成功")
        return True
    except ImportError as e:
        print(f"❌ Opik 导入失败: {e}")
        print("请运行: uv add opik 或 pip install opik")
        return False

def test_opik_config():
    """测试我们的 Opik 配置"""
    try:
        from opik_config import config, track_agent_execution, log_agent_metrics
        print("✅ Opik 配置模块加载成功")

        # 测试装饰器
        @track_agent_execution("test_agent")
        def test_function():
            return "Hello, Opik!"

        result = test_function()
        print(f"✅ 追踪装饰器测试成功: {result}")

        # 测试指标记录
        log_agent_metrics("test_agent", {"test_metric": 1.0})
        print("✅ 指标记录测试成功")

        return True
    except Exception as e:
        print(f"❌ Opik 配置测试失败: {e}")
        return False

def test_custom_handler():
    """测试自定义工具处理器"""
    try:
        from custom_handler import CustomToolsHandler
        handler = CustomToolsHandler()
        stats = handler.get_usage_stats()
        print(f"✅ 自定义处理器测试成功: {stats}")
        return True
    except Exception as e:
        print(f"❌ 自定义处理器测试失败: {e}")
        return False

def test_environment():
    """测试环境配置"""
    api_key = os.getenv("OPIK_API_KEY")
    if api_key:
        print(f"✅ 找到 OPIK_API_KEY: {api_key[:10]}...")
    else:
        print("⚠️  未找到 OPIK_API_KEY，将使用默认配置")

    workspace = os.getenv("OPIK_WORKSPACE", "default")
    project = os.getenv("OPIK_PROJECT_NAME", "week13-observability")
    print(f"📊 工作区: {workspace}, 项目: {project}")

    return True

def main():
    """运行所有测试"""
    print("🚀 开始 Opik 设置验证测试...\n")

    tests = [
        ("Opik 导入测试", test_opik_import),
        ("环境配置测试", test_environment),
        ("Opik 配置测试", test_opik_config),
        ("自定义处理器测试", test_custom_handler),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} 异常: {e}")

    print(f"\n{'='*50}")
    print(f"测试完成: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！Week 13 Opik 集成配置正确。")
        print("\n下一步:")
        print("1. 设置 OPIK_API_KEY 环境变量")
        print("2. 运行完整示例: uv run python solution.py")
    else:
        print("⚠️  部分测试失败，请检查配置。")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)