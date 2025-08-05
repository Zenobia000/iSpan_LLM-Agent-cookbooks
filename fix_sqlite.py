#!/usr/bin/env python3
"""
SQLite 版本修正腳本
解決 ChromaDB 對 SQLite 版本要求的相容性問題
"""

import sys
import os

def fix_sqlite():
    """修正 SQLite 版本問題"""
    try:
        # 嘗試導入 pysqlite3，如果可用就替代內建 sqlite3
        import pysqlite3.dbapi2 as sqlite3
        
        # 將 pysqlite3 註冊為 sqlite3 模組
        sys.modules['sqlite3'] = sqlite3
        sys.modules['sqlite3.dbapi2'] = sqlite3
        
        print(f"✅ 成功啟用 pysqlite3，SQLite 版本: {sqlite3.sqlite_version}")
        return True
        
    except ImportError:
        print("❌ 無法導入 pysqlite3-binary，請確保已安裝：")
        print("   poetry add pysqlite3-binary")
        return False

def test_chromadb():
    """測試 ChromaDB 是否能正常工作"""
    try:
        import chromadb
        print(f"✅ ChromaDB 導入成功，版本: {chromadb.__version__}")
        
        # 創建一個測試用的記憶體資料庫
        client = chromadb.Client()
        collection = client.create_collection("test_collection")
        print("✅ ChromaDB 測試集合創建成功")
        
        # 測試基本操作
        collection.add(
            documents=["This is a test document"],
            ids=["test_id_1"]
        )
        
        results = collection.query(
            query_texts=["test"],
            n_results=1
        )
        
        print("✅ ChromaDB 基本操作測試通過")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 修正 SQLite 版本相容性問題...")
    
    if fix_sqlite():
        print("\n🧪 測試 ChromaDB...")
        if test_chromadb():
            print("\n🎉 SQLite 修正成功！ChromaDB 可以正常使用！")
        else:
            print("\n⚠️ SQLite 已修正，但 ChromaDB 仍有問題")
    else:
        print("\n❌ SQLite 修正失敗") 