import sqlite3
from typing import List, Optional, Set
from datetime import datetime
from synth_agent.memory.memory_list.episodic import Episode


class SQLiteDocumentStore:
    """SQLite文档存储"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            memory_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            context TEXT NOT NULL
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON memories(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
        
        conn.commit()
        conn.close()
    
    def save(self, episode: Episode):
        """保存情景记忆"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO memories (memory_id, session_id, timestamp, content, context) VALUES (?, ?, ?, ?, ?)',
            (episode.memory_id, episode.session_id, episode.timestamp.isoformat(), episode.content, str(episode.context))
        )
        
        conn.commit()
        conn.close()
    
    def get(self, memory_id: str) -> Optional[Episode]:
        """获取情景记忆"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM memories WHERE memory_id = ?', (memory_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Episode(
                memory_id=row['memory_id'],
                session_id=row['session_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                content=row['content'],
                context=eval(row['context'])
            )
        return None
    
    def delete(self, memory_id: str):
        """删除情景记忆"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM memories WHERE memory_id = ?', (memory_id,))
        
        conn.commit()
        conn.close()
    
    def get_by_session(self, session_id: str, limit: int = 10) -> List[Episode]:
        """按会话获取情景记忆"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM memories WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?',
            (session_id, limit)
        )
        rows = cursor.fetchall()
        
        conn.close()
        
        episodes = []
        for row in rows:
            episodes.append(Episode(
                memory_id=row['memory_id'],
                session_id=row['session_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                content=row['content'],
                context=eval(row['context'])
            ))
        
        return episodes
    
    def get_all_ids(self) -> Set[str]:
        """获取所有记忆ID"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT memory_id FROM memories')
        rows = cursor.fetchall()
        
        conn.close()
        
        return {row[0] for row in rows}
