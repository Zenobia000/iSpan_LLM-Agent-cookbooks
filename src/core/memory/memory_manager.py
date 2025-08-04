"""
CrewAI 記憶系統管理模組

基於認知科學的記憶架構設計：
1. 工作記憶 (Working Memory): 短期活躍資訊
2. 長期記憶 (Long-term Memory): 持久化知識和經驗
3. 情境記憶 (Episodic Memory): 特定場景的記憶片段

參考文檔: docs/core/memory_fundamentals.md
"""

# 修復 SQLite 版本兼容性
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import uuid
from pathlib import Path
import asyncio
from abc import ABC, abstractmethod

import chromadb
from chromadb.config import Settings
import numpy as np
from pydantic import BaseModel, Field


class MemoryType(Enum):
    """記憶類型枚舉"""
    WORKING = "working"        # 工作記憶
    LONG_TERM = "long_term"    # 長期記憶
    EPISODIC = "episodic"      # 情境記憶
    PROCEDURAL = "procedural"  # 程序記憶
    SEMANTIC = "semantic"      # 語義記憶


class MemoryPriority(Enum):
    """記憶優先級"""
    CRITICAL = "critical"      # 關鍵記憶，永不刪除
    HIGH = "high"             # 高優先級
    MEDIUM = "medium"         # 中等優先級
    LOW = "low"               # 低優先級
    TEMPORARY = "temporary"    # 臨時記憶


@dataclass
class MemoryItem:
    """記憶項目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Any = None
    memory_type: MemoryType = MemoryType.WORKING
    priority: MemoryPriority = MemoryPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    expiry: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """從字典創建記憶項目"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            priority=MemoryPriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expiry=datetime.fromisoformat(data["expiry"]) if data["expiry"] else None,
            access_count=data["access_count"],
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            tags=data["tags"],
            metadata=data["metadata"]
        )


class MemoryStorage(ABC):
    """記憶存儲抽象基類"""
    
    @abstractmethod
    async def store(self, item: MemoryItem) -> bool:
        """存儲記憶項目"""
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """檢索特定記憶"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索記憶"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """刪除記憶"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """清理過期記憶"""
        pass


class InMemoryStorage(MemoryStorage):
    """內存存儲實作"""
    
    def __init__(self):
        self.storage: Dict[str, MemoryItem] = {}
    
    async def store(self, item: MemoryItem) -> bool:
        """存儲記憶項目"""
        self.storage[item.id] = item
        return True
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """檢索特定記憶"""
        item = self.storage.get(memory_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.now()
        return item
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """簡單的文本匹配搜索"""
        results = []
        for item in self.storage.values():
            if query.lower() in str(item.content).lower():
                results.append(item)
                if len(results) >= limit:
                    break
        return results
    
    async def delete(self, memory_id: str) -> bool:
        """刪除記憶"""
        if memory_id in self.storage:
            del self.storage[memory_id]
            return True
        return False
    
    async def cleanup_expired(self) -> int:
        """清理過期記憶"""
        current_time = datetime.now()
        expired_ids = []
        
        for memory_id, item in self.storage.items():
            if item.expiry and current_time > item.expiry:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            del self.storage[memory_id]
        
        return len(expired_ids)


class SQLiteStorage(MemoryStorage):
    """SQLite 持久化存儲"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    memory_type TEXT,
                    priority TEXT,
                    timestamp TEXT,
                    expiry TEXT,
                    access_count INTEGER,
                    last_accessed TEXT,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
            """)
    
    async def store(self, item: MemoryItem) -> bool:
        """存儲記憶項目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, content, memory_type, priority, timestamp, expiry, 
                     access_count, last_accessed, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.id,
                    json.dumps(item.content),
                    item.memory_type.value,
                    item.priority.value,
                    item.timestamp.isoformat(),
                    item.expiry.isoformat() if item.expiry else None,
                    item.access_count,
                    item.last_accessed.isoformat(),
                    json.dumps(item.tags),
                    json.dumps(item.metadata)
                ))
            return True
        except Exception as e:
            print(f"存儲記憶失敗: {e}")
            return False
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """檢索特定記憶"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM memories WHERE id = ?", (memory_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    # 更新訪問統計
                    conn.execute("""
                        UPDATE memories 
                        SET access_count = access_count + 1, 
                            last_accessed = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), memory_id))
                    
                    return self._row_to_memory_item(row)
        except Exception as e:
            print(f"檢索記憶失敗: {e}")
        return None
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索記憶"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM memories 
                    WHERE content LIKE ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (f"%{query}%", limit))
                
                return [self._row_to_memory_item(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"搜索記憶失敗: {e}")
            return []
    
    async def delete(self, memory_id: str) -> bool:
        """刪除記憶"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM memories WHERE id = ?", (memory_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"刪除記憶失敗: {e}")
            return False
    
    async def cleanup_expired(self) -> int:
        """清理過期記憶"""
        try:
            current_time = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM memories 
                    WHERE expiry IS NOT NULL AND expiry < ?
                """, (current_time,))
                return cursor.rowcount
        except Exception as e:
            print(f"清理過期記憶失敗: {e}")
            return 0
    
    def _row_to_memory_item(self, row) -> MemoryItem:
        """將資料庫行轉換為記憶項目"""
        return MemoryItem(
            id=row[0],
            content=json.loads(row[1]),
            memory_type=MemoryType(row[2]),
            priority=MemoryPriority(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            expiry=datetime.fromisoformat(row[5]) if row[5] else None,
            access_count=row[6],
            last_accessed=datetime.fromisoformat(row[7]),
            tags=json.loads(row[8]),
            metadata=json.loads(row[9])
        )


class VectorStorage(MemoryStorage):
    """向量存儲（用於語義搜索）"""
    
    def __init__(self, collection_name: str = "agent_memories"):
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Agent 記憶向量存儲"}
        )
        self.fallback_storage = InMemoryStorage()
    
    async def store(self, item: MemoryItem) -> bool:
        """存儲記憶項目（同時存儲向量和元數據）"""
        try:
            # 存儲到向量資料庫
            self.collection.add(
                documents=[str(item.content)],
                metadatas=[item.to_dict()],
                ids=[item.id]
            )
            
            # 備份到內存存儲
            await self.fallback_storage.store(item)
            return True
        except Exception as e:
            print(f"向量存儲失敗: {e}")
            return False
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """檢索特定記憶"""
        try:
            results = self.collection.get(ids=[memory_id])
            if results['documents']:
                metadata = results['metadatas'][0]
                item = MemoryItem.from_dict(metadata)
                item.access_count += 1
                item.last_accessed = datetime.now()
                await self.store(item)  # 更新訪問統計
                return item
        except Exception as e:
            print(f"向量檢索失敗: {e}")
            # 嘗試從備份存儲檢索
            return await self.fallback_storage.retrieve(memory_id)
        return None
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """語義搜索記憶"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            memories = []
            for metadata in results['metadatas'][0]:
                memories.append(MemoryItem.from_dict(metadata))
            
            return memories
        except Exception as e:
            print(f"向量搜索失敗: {e}")
            # 降級到文本搜索
            return await self.fallback_storage.search(query, limit)
    
    async def delete(self, memory_id: str) -> bool:
        """刪除記憶"""
        try:
            self.collection.delete(ids=[memory_id])
            await self.fallback_storage.delete(memory_id)
            return True
        except Exception as e:
            print(f"向量刪除失敗: {e}")
            return False
    
    async def cleanup_expired(self) -> int:
        """清理過期記憶"""
        # ChromaDB 不直接支援條件刪除，需要先查詢再刪除
        try:
            all_items = self.collection.get()
            current_time = datetime.now()
            expired_ids = []
            
            for i, metadata in enumerate(all_items['metadatas']):
                if metadata.get('expiry'):
                    expiry = datetime.fromisoformat(metadata['expiry'])
                    if current_time > expiry:
                        expired_ids.append(all_items['ids'][i])
            
            if expired_ids:
                self.collection.delete(ids=expired_ids)
            
            return len(expired_ids)
        except Exception as e:
            print(f"向量清理失敗: {e}")
            return 0


class MemoryManager:
    """
    記憶系統管理器
    
    整合多種存儲後端，提供統一的記憶管理介面
    """
    
    def __init__(self, storage_type: str = "hybrid", **kwargs):
        self.storage_type = storage_type
        self.storages = self._init_storages(**kwargs)
        
        # 記憶管理配置
        self.max_working_memory = kwargs.get("max_working_memory", 100)
        self.auto_cleanup_interval = kwargs.get("auto_cleanup_interval", 3600)  # 1小時
        self.consolidation_threshold = kwargs.get("consolidation_threshold", 0.8)
        
        # 統計資訊
        self.stats = {
            "total_memories": 0,
            "working_memories": 0,
            "long_term_memories": 0,
            "episodic_memories": 0
        }
        
        # 啟動自動清理任務
        self._start_background_tasks()
    
    def _init_storages(self, **kwargs) -> Dict[str, MemoryStorage]:
        """初始化存儲後端"""
        storages = {}
        
        if self.storage_type == "memory":
            storages["primary"] = InMemoryStorage()
        elif self.storage_type == "sqlite":
            db_path = kwargs.get("db_path", "memory.db")
            storages["primary"] = SQLiteStorage(db_path)
        elif self.storage_type == "vector":
            collection_name = kwargs.get("collection_name", "agent_memories")
            storages["primary"] = VectorStorage(collection_name)
        elif self.storage_type == "hybrid":
            # 混合模式：工作記憶用內存，長期記憶用 SQLite，語義搜索用向量
            storages["working"] = InMemoryStorage()
            storages["persistent"] = SQLiteStorage(kwargs.get("db_path", "memory.db"))
            storages["semantic"] = VectorStorage(kwargs.get("collection_name", "agent_memories"))
        
        return storages
    
    def _start_background_tasks(self):
        """啟動背景任務"""
        # 在實際應用中，這裡會啟動定時任務
        pass
    
    async def store_memory(self, content: Any, memory_type: MemoryType = MemoryType.WORKING,
                          priority: MemoryPriority = MemoryPriority.MEDIUM,
                          tags: Optional[List[str]] = None,
                          ttl: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        存儲記憶
        
        Args:
            content: 記憶內容
            memory_type: 記憶類型
            priority: 優先級
            tags: 標籤
            ttl: 生存時間（秒）
            metadata: 元數據
            
        Returns:
            記憶ID
        """
        # 創建記憶項目
        expiry = datetime.now() + timedelta(seconds=ttl) if ttl else None
        
        memory_item = MemoryItem(
            content=content,
            memory_type=memory_type,
            priority=priority,
            expiry=expiry,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 選擇合適的存儲後端
        storage = self._select_storage_for_type(memory_type)
        
        # 存儲記憶
        success = await storage.store(memory_item)
        
        if success:
            self._update_stats(memory_type, 1)
            
            # 檢查是否需要記憶整理
            if memory_type == MemoryType.WORKING:
                await self._check_working_memory_limit()
        
        return memory_item.id
    
    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """檢索記憶"""
        # 從所有存儲後端嘗試檢索
        for storage in self.storages.values():
            memory = await storage.retrieve(memory_id)
            if memory:
                return memory
        return None
    
    async def search_memories(self, query: str, memory_type: Optional[MemoryType] = None,
                            limit: int = 10, use_semantic: bool = True) -> List[MemoryItem]:
        """
        搜索記憶
        
        Args:
            query: 搜索查詢
            memory_type: 記憶類型過濾
            limit: 結果限制
            use_semantic: 是否使用語義搜索
            
        Returns:
            記憶項目列表
        """
        if use_semantic and "semantic" in self.storages:
            results = await self.storages["semantic"].search(query, limit)
        else:
            # 從主要存儲搜索
            storage = self._select_storage_for_type(memory_type or MemoryType.WORKING)
            results = await storage.search(query, limit)
        
        # 按類型過濾
        if memory_type:
            results = [m for m in results if m.memory_type == memory_type]
        
        return results[:limit]
    
    async def delete_memory(self, memory_id: str) -> bool:
        """刪除記憶"""
        deleted = False
        for storage in self.storages.values():
            if await storage.delete(memory_id):
                deleted = True
        return deleted
    
    async def consolidate_memories(self):
        """記憶整理：將重要的工作記憶轉移到長期記憶"""
        if "working" not in self.storages:
            return
        
        working_storage = self.storages["working"]
        long_term_storage = self.storages.get("persistent") or self.storages["primary"]
        
        # 獲取所有工作記憶
        # 注意：這是簡化實作，實際應該有更複雜的整理邏輯
        print("開始記憶整理...")
        
        # 清理過期記憶
        await self.cleanup_expired_memories()
    
    async def cleanup_expired_memories(self) -> int:
        """清理過期記憶"""
        total_cleaned = 0
        for storage in self.storages.values():
            cleaned = await storage.cleanup_expired()
            total_cleaned += cleaned
        
        if total_cleaned > 0:
            print(f"清理了 {total_cleaned} 個過期記憶")
        
        return total_cleaned
    
    async def store_execution(self, agent_id: str, task: str, result: Any, metadata: Dict[str, Any]):
        """存儲執行記錄（專用於 Agent 執行歷史）"""
        execution_memory = {
            "agent_id": agent_id,
            "task": task,
            "result": result,
            "execution_metadata": metadata
        }
        
        await self.store_memory(
            content=execution_memory,
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.MEDIUM,
            tags=["execution", "agent_history"],
            metadata={"agent_id": agent_id}
        )
    
    def _select_storage_for_type(self, memory_type: MemoryType) -> MemoryStorage:
        """為記憶類型選擇合適的存儲後端"""
        if self.storage_type == "hybrid":
            if memory_type == MemoryType.WORKING:
                return self.storages["working"]
            elif memory_type in [MemoryType.LONG_TERM, MemoryType.PROCEDURAL]:
                return self.storages["persistent"]
            else:
                return self.storages["semantic"]
        else:
            return self.storages["primary"]
    
    async def _check_working_memory_limit(self):
        """檢查工作記憶限制"""
        if self.stats["working_memories"] > self.max_working_memory:
            await self.consolidate_memories()
    
    def _update_stats(self, memory_type: MemoryType, delta: int):
        """更新統計資訊"""
        self.stats["total_memories"] += delta
        
        if memory_type == MemoryType.WORKING:
            self.stats["working_memories"] += delta
        elif memory_type == MemoryType.LONG_TERM:
            self.stats["long_term_memories"] += delta
        elif memory_type == MemoryType.EPISODIC:
            self.stats["episodic_memories"] += delta
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """獲取記憶統計資訊"""
        return self.stats.copy()
    
    def is_healthy(self) -> bool:
        """檢查記憶系統健康狀態"""
        try:
            # 基本健康檢查
            return len(self.storages) > 0
        except Exception:
            return False


# 使用範例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 創建記憶管理器
        memory_manager = MemoryManager(storage_type="hybrid")
        
        # 存儲一些記憶
        memory_id_1 = await memory_manager.store_memory(
            content="學習了 CrewAI 的基本概念",
            memory_type=MemoryType.LONG_TERM,
            tags=["學習", "CrewAI"]
        )
        
        memory_id_2 = await memory_manager.store_memory(
            content="當前正在設計 Agent 架構",
            memory_type=MemoryType.WORKING,
            tags=["工作", "設計"],
            ttl=3600  # 1小時後過期
        )
        
        # 搜索記憶
        search_results = await memory_manager.search_memories("CrewAI")
        print(f"搜索到 {len(search_results)} 個相關記憶")
        
        # 檢索特定記憶
        retrieved = await memory_manager.retrieve_memory(memory_id_1)
        if retrieved:
            print(f"檢索成功: {retrieved.content}")
        
        # 統計資訊
        stats = memory_manager.get_memory_statistics()
        print(f"記憶統計: {stats}")
    
    asyncio.run(main()) 