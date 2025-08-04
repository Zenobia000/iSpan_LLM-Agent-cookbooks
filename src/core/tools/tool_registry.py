"""
CrewAI 工具註冊表模組

提供工具的統一管理、動態載入和運行時註冊功能
基於設計模式：註冊表模式 + 工廠模式 + 裝飾器模式

參考文檔: docs/core/tools_fundamentals.md
"""
# 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    
from typing import Dict, List, Any, Optional, Type, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import inspect
import importlib
import json
import asyncio
from pathlib import Path
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ToolStatus(Enum):
    """工具狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class ToolCategory(Enum):
    """工具分類"""
    DATA_RETRIEVAL = "data_retrieval"      # 資料檢索
    DATA_PROCESSING = "data_processing"     # 資料處理
    COMMUNICATION = "communication"         # 通訊協作
    CONTENT_CREATION = "content_creation"   # 內容創作
    SYSTEM_INTEGRATION = "system_integration"  # 系統整合
    UTILITY = "utility"                     # 實用工具
    CUSTOM = "custom"                       # 自訂工具


@dataclass
class ToolMetadata:
    """工具元數據"""
    name: str
    version: str = "1.0.0"
    category: ToolCategory = ToolCategory.CUSTOM
    status: ToolStatus = ToolStatus.ACTIVE
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "status": self.status.value,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


class ToolWrapper:
    """工具包裝器，提供額外功能"""
    
    def __init__(self, tool: BaseTool, metadata: ToolMetadata):
        self.tool = tool
        self.metadata = metadata
        self.is_async = asyncio.iscoroutinefunction(tool._run)
        
    async def execute(self, *args, **kwargs) -> Any:
        """執行工具並更新統計"""
        try:
            # 更新使用統計
            self.metadata.usage_count += 1
            self.metadata.last_used = datetime.now()
            
            # 執行工具
            if self.is_async:
                result = await self.tool._run(*args, **kwargs)
            else:
                result = self.tool._run(*args, **kwargs)
            
            return result
        except Exception as e:
            # 記錄錯誤但不中斷
            print(f"工具 {self.metadata.name} 執行失敗: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        """獲取工具資訊"""
        return {
            "name": self.tool.name,
            "description": self.tool.description,
            "metadata": self.metadata.to_dict(),
            "is_async": self.is_async
        }


class ToolRegistry:
    """
    工具註冊表
    
    管理所有可用工具的註冊、發現和載入
    """
    
    _instance = None
    _tools: Dict[str, ToolWrapper] = {}
    _categories: Dict[ToolCategory, List[str]] = {}
    _aliases: Dict[str, str] = {}  # 工具別名映射
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化註冊表"""
        for category in ToolCategory:
            self._categories[category] = []
    
    def register_tool(self, tool: BaseTool, metadata: Optional[ToolMetadata] = None,
                     aliases: Optional[List[str]] = None) -> bool:
        """
        註冊工具
        
        Args:
            tool: 工具實例
            metadata: 工具元數據
            aliases: 工具別名列表
            
        Returns:
            註冊是否成功
        """
        try:
            # 創建或使用提供的元數據
            if metadata is None:
                metadata = ToolMetadata(
                    name=tool.name,
                    description=tool.description or "無描述"
                )
            
            # 檢查工具是否已存在
            if tool.name in self._tools:
                print(f"警告: 工具 '{tool.name}' 已存在，將被覆蓋")
            
            # 包裝工具
            wrapper = ToolWrapper(tool, metadata)
            
            # 註冊工具
            self._tools[tool.name] = wrapper
            
            # 分類管理
            if metadata.category not in self._categories:
                self._categories[metadata.category] = []
            if tool.name not in self._categories[metadata.category]:
                self._categories[metadata.category].append(tool.name)
            
            # 註冊別名
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = tool.name
            
            print(f"成功註冊工具: {tool.name}")
            return True
            
        except Exception as e:
            print(f"註冊工具失敗: {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """註銷工具"""
        try:
            if tool_name not in self._tools:
                return False
            
            # 從主註冊表移除
            wrapper = self._tools.pop(tool_name)
            
            # 從分類中移除
            category = wrapper.metadata.category
            if tool_name in self._categories[category]:
                self._categories[category].remove(tool_name)
            
            # 移除別名
            aliases_to_remove = [alias for alias, name in self._aliases.items() if name == tool_name]
            for alias in aliases_to_remove:
                del self._aliases[alias]
            
            print(f"成功註銷工具: {tool_name}")
            return True
            
        except Exception as e:
            print(f"註銷工具失敗: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[ToolWrapper]:
        """獲取工具包裝器"""
        # 先嘗試直接名稱
        if tool_name in self._tools:
            return self._tools[tool_name]
        
        # 再嘗試別名
        if tool_name in self._aliases:
            actual_name = self._aliases[tool_name]
            return self._tools.get(actual_name)
        
        return None
    
    def get_tool_instance(self, tool_name: str) -> Optional[BaseTool]:
        """獲取原始工具實例"""
        wrapper = self.get_tool(tool_name)
        return wrapper.tool if wrapper else None
    
    def list_tools(self, category: Optional[ToolCategory] = None,
                  status: Optional[ToolStatus] = None) -> List[str]:
        """
        列出工具
        
        Args:
            category: 按分類過濾
            status: 按狀態過濾
            
        Returns:
            工具名稱列表
        """
        tools = []
        
        for name, wrapper in self._tools.items():
            # 分類過濾
            if category and wrapper.metadata.category != category:
                continue
            
            # 狀態過濾
            if status and wrapper.metadata.status != status:
                continue
            
            tools.append(name)
        
        return sorted(tools)
    
    def search_tools(self, query: str) -> List[str]:
        """搜索工具"""
        query = query.lower()
        results = []
        
        for name, wrapper in self._tools.items():
            # 搜索名稱、描述和標籤
            searchable_text = " ".join([
                name,
                wrapper.metadata.description,
                " ".join(wrapper.metadata.tags)
            ]).lower()
            
            if query in searchable_text:
                results.append(name)
        
        return sorted(results)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """按分類獲取工具"""
        return self._categories.get(category, []).copy()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """獲取工具詳細資訊"""
        wrapper = self.get_tool(tool_name)
        return wrapper.get_info() if wrapper else None
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """獲取工具統計資訊"""
        stats = {
            "total_tools": len(self._tools),
            "by_category": {},
            "by_status": {},
            "most_used": [],
            "recently_used": []
        }
        
        # 按分類統計
        for category, tools in self._categories.items():
            stats["by_category"][category.value] = len(tools)
        
        # 按狀態統計
        status_count = {}
        usage_data = []
        
        for wrapper in self._tools.values():
            status = wrapper.metadata.status.value
            status_count[status] = status_count.get(status, 0) + 1
            
            usage_data.append({
                "name": wrapper.metadata.name,
                "usage_count": wrapper.metadata.usage_count,
                "last_used": wrapper.metadata.last_used
            })
        
        stats["by_status"] = status_count
        
        # 最常用工具
        usage_data.sort(key=lambda x: x["usage_count"], reverse=True)
        stats["most_used"] = usage_data[:5]
        
        # 最近使用工具
        recent_usage = [item for item in usage_data if item["last_used"]]
        recent_usage.sort(key=lambda x: x["last_used"], reverse=True)
        stats["recently_used"] = recent_usage[:5]
        
        return stats
    
    def export_registry(self, file_path: str) -> bool:
        """匯出註冊表"""
        try:
            export_data = {
                "tools": {},
                "categories": {},
                "aliases": self._aliases,
                "exported_at": datetime.now().isoformat()
            }
            
            # 匯出工具資訊
            for name, wrapper in self._tools.items():
                export_data["tools"][name] = wrapper.metadata.to_dict()
            
            # 匯出分類資訊
            for category, tools in self._categories.items():
                export_data["categories"][category.value] = tools
            
            # 寫入檔案
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"註冊表已匯出到: {file_path}")
            return True
            
        except Exception as e:
            print(f"匯出註冊表失敗: {e}")
            return False
    
    def clear_registry(self):
        """清空註冊表"""
        self._tools.clear()
        self._aliases.clear()
        for category in self._categories:
            self._categories[category].clear()
        print("註冊表已清空")
    
    @classmethod
    def get_tool_by_name(cls, tool_name: str) -> Optional[BaseTool]:
        """類方法：根據名稱獲取工具實例"""
        instance = cls()
        return instance.get_tool_instance(tool_name)


class ToolLoader:
    """工具載入器"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def load_from_module(self, module_path: str) -> List[str]:
        """從模組載入工具"""
        loaded_tools = []
        
        try:
            module = importlib.import_module(module_path)
            
            # 查找工具類別
            for name in dir(module):
                obj = getattr(module, name)
                
                # 檢查是否為 BaseTool 子類別
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTool) and 
                    obj != BaseTool):
                    
                    try:
                        # 實例化工具
                        tool_instance = obj()
                        
                        # 註冊工具
                        if self.registry.register_tool(tool_instance):
                            loaded_tools.append(tool_instance.name)
                    except Exception as e:
                        print(f"載入工具 {name} 失敗: {e}")
            
            print(f"從 {module_path} 載入了 {len(loaded_tools)} 個工具")
            
        except Exception as e:
            print(f"載入模組 {module_path} 失敗: {e}")
        
        return loaded_tools
    
    def load_from_directory(self, directory_path: str, pattern: str = "*.py") -> List[str]:
        """從目錄載入工具"""
        loaded_tools = []
        directory = Path(directory_path)
        
        if not directory.exists():
            print(f"目錄不存在: {directory_path}")
            return loaded_tools
        
        # 查找Python檔案
        for file_path in directory.glob(pattern):
            if file_path.name.startswith('__'):
                continue
            
            try:
                # 構建模組路徑
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找並載入工具
                for name in dir(module):
                    obj = getattr(module, name)
                    
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool):
                        
                        try:
                            tool_instance = obj()
                            if self.registry.register_tool(tool_instance):
                                loaded_tools.append(tool_instance.name)
                        except Exception as e:
                            print(f"載入工具 {name} 失敗: {e}")
                            
            except Exception as e:
                print(f"處理檔案 {file_path} 失敗: {e}")
        
        return loaded_tools


# 裝飾器：工具註冊
def register_tool(category: ToolCategory = ToolCategory.CUSTOM,
                 aliases: Optional[List[str]] = None,
                 **metadata_kwargs):
    """
    工具註冊裝飾器
    
    使用方式:
    @register_tool(category=ToolCategory.DATA_PROCESSING, aliases=["calc"])
    class CalculatorTool(BaseTool):
        ...
    """
    def decorator(tool_class):
        # 在類別上添加註冊資訊
        tool_class._registry_category = category
        tool_class._registry_aliases = aliases or []
        tool_class._registry_metadata = metadata_kwargs
        
        # 自動註冊（如果需要）
        def auto_register():
            try:
                instance = tool_class()
                metadata = ToolMetadata(
                    name=instance.name,
                    category=category,
                    description=instance.description or "",
                    **metadata_kwargs
                )
                
                registry = ToolRegistry()
                registry.register_tool(instance, metadata, aliases)
            except Exception as e:
                print(f"自動註冊工具失敗: {e}")
        
        # 可以選擇是否立即註冊
        if metadata_kwargs.get("auto_register", False):
            auto_register()
        
        return tool_class
    
    return decorator


# 工具工廠
class ToolFactory:
    """工具工廠"""
    
    @staticmethod
    def create_tool(tool_type: str, **kwargs) -> Optional[BaseTool]:
        """創建工具實例"""
        # 這裡可以實作動態工具創建邏輯
        # 根據配置創建不同類型的工具
        pass


# 使用範例
if __name__ == "__main__":
    # 創建註冊表
    registry = ToolRegistry()
    
    # 模擬註冊一些工具
    from crewai.tools import tool
    
    @tool("範例計算器")
    def calculator(expression: str) -> str:
        """執行基本數學計算"""
        try:
            result = eval(expression)
            return f"計算結果: {result}"
        except:
            return "計算錯誤"
    
    # 手動註冊
    metadata = ToolMetadata(
        name="calculator",
        category=ToolCategory.DATA_PROCESSING,
        description="基本數學計算工具",
        tags=["數學", "計算"]
    )
    
    registry.register_tool(calculator, metadata, aliases=["calc", "數學"])
    
    # 測試功能
    print("=== 工具註冊表測試 ===")
    print(f"已註冊工具: {registry.list_tools()}")
    print(f"工具資訊: {registry.get_tool_info('calculator')}")
    print(f"搜索結果: {registry.search_tools('計算')}")
    print(f"統計資訊: {registry.get_tool_statistics()}") 