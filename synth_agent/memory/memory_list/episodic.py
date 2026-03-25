from datetime import datetime
from typing import Dict

class Episode:
    """情景记忆项"""
    
    def __init__(
        self,
        memory_id: str,
        session_id: str,
        timestamp: datetime,
        content: str,
        context: Dict
    ):
        self.memory_id = memory_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.content = content
        self.context = context
