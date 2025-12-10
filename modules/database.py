"""
檔案標準 (Standard):
本檔案負責 SQLite 資料庫的初始化、記憶儲存與檢索功能。
提供記憶的 CRUD 操作，以及 RAG (檢索增強生成) 所需的搜尋功能。
輸入：文字內容、時間戳記、標籤等
輸出：查詢結果、記憶 ID 等

執行方式 (Execution):
- 被 main.py 和 ai.py 模組呼叫
- 獨立測試：python -m modules.database (會建立測試資料並查詢)

相依性 (Dependencies):
- sqlite3: Python 內建模組
- datetime: 時間處理
- os: 路徑處理
- config: 系統配置
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import config

class Database:
    """資料庫管理類別"""
    
    def __init__(self, db_path: str = None):
        """
        初始化資料庫連線
        
        Args:
            db_path: 資料庫檔案路徑，預設使用 config.DB_PATH
        """
        self.db_path = db_path or config.Config.DB_PATH
        # 確保資料目錄存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 建立記憶表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                mode TEXT,
                tags TEXT,
                embedding TEXT
            )
        ''')
        
        # 建立索引以加速搜尋
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON memories(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_mode 
            ON memories(mode)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_memory(self, content: str, mode: str = None, tags: str = None) -> int:
        """
        新增記憶
        
        Args:
            content: 記憶內容
            mode: 模式（daily, chat, diary 等）
            tags: 標籤（逗號分隔）
        
        Returns:
            新增的記憶 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (content, mode, tags, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (content, mode, tags, datetime.now().isoformat()))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return memory_id
    
    def get_memories(self, 
                    limit: int = 10, 
                    mode: str = None,
                    start_date: str = None,
                    end_date: str = None) -> List[Dict]:
        """
        查詢記憶
        
        Args:
            limit: 返回筆數限制
            mode: 模式篩選
            start_date: 開始日期 (ISO 格式)
            end_date: 結束日期 (ISO 格式)
        
        Returns:
            記憶列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM memories WHERE 1=1'
        params = []
        
        if mode:
            query += ' AND mode = ?'
            params.append(mode)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_memories(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        關鍵字搜尋記憶（用於 RAG）
        
        Args:
            keyword: 搜尋關鍵字
            limit: 返回筆數限制
        
        Returns:
            相關記憶列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 簡單的關鍵字搜尋（未來可擴展為向量搜尋）
        cursor.execute('''
            SELECT * FROM memories 
            WHERE content LIKE ? 
            OR tags LIKE ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_memory_by_date(self, date: str) -> List[Dict]:
        """
        根據日期取得記憶（用於日記模式）
        
        Args:
            date: 日期字串 (YYYY-MM-DD)
        
        Returns:
            該日期的記憶列表
        """
        start_date = f'{date} 00:00:00'
        end_date = f'{date} 23:59:59'
        return self.get_memories(start_date=start_date, end_date=end_date)
    
    def get_recent_memories(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """
        取得最近 N 天的記憶（用於 RAG 上下文）
        
        Args:
            days: 天數
            limit: 返回筆數限制
        
        Returns:
            記憶列表
        """
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.get_memories(start_date=start_date, limit=limit)

if __name__ == '__main__':
    # 測試資料庫功能
    db = Database()
    
    # 新增測試記憶
    print("新增測試記憶...")
    id1 = db.add_memory("今天天氣很好", mode="daily", tags="天氣,日常")
    id2 = db.add_memory("我喜歡程式設計", mode="chat", tags="興趣,程式")
    print(f"新增記憶 ID: {id1}, {id2}")
    
    # 查詢記憶
    print("\n查詢所有記憶:")
    memories = db.get_memories(limit=5)
    for mem in memories:
        print(f"  [{mem['id']}] {mem['content']} ({mem['mode']})")
    
    # 關鍵字搜尋
    print("\n搜尋 '天氣':")
    results = db.search_memories("天氣")
    for mem in results:
        print(f"  [{mem['id']}] {mem['content']}")

