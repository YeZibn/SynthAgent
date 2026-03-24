from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock
from pydantic import BaseModel


class MemoryEntry(BaseModel):
    key: str
    value: Any
    timestamp: datetime
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "metadata": self.metadata
        }


class SharedMemory:
    def __init__(self, max_size: int = 1000):
        self._memory: Dict[str, MemoryEntry] = {}
        self._history: List[MemoryEntry] = []
        self._max_size = max_size
        self._lock = Lock()

    def set(self, key: str, value: Any, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            timestamp = datetime.now()
            entry = MemoryEntry(
                key=key,
                value=value,
                timestamp=timestamp,
                agent_id=agent_id,
                metadata=metadata or {}
            )

            if key in self._memory:
                old_entry = self._memory[key]
                self._history.append(old_entry)

            self._memory[key] = entry

            if len(self._history) > self._max_size:
                self._history = self._history[-self._max_size:]

            print(f"💾 共享记忆已更新: {key} = {value} (by {agent_id or 'system'})")

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._memory.get(key)
            if entry:
                return entry.value
            return default

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        with self._lock:
            return self._memory.get(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._memory:
                entry = self._memory[key]
                self._history.append(entry)
                del self._memory[key]
                print(f"🗑️  共享记忆已删除: {key}")
                return True
            return False

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._memory

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return {key: entry.value for key, entry in self._memory.items()}

    def get_all_entries(self) -> List[MemoryEntry]:
        with self._lock:
            return list(self._memory.values())

    def get_keys(self) -> List[str]:
        with self._lock:
            return list(self._memory.keys())

    def filter_by_agent(self, agent_id: str) -> Dict[str, Any]:
        with self._lock:
            return {
                key: entry.value
                for key, entry in self._memory.items()
                if entry.agent_id == agent_id
            }

    def search(self, pattern: str) -> List[str]:
        with self._lock:
            import re
            regex = re.compile(pattern, re.IGNORECASE)
            return [
                key for key in self._memory.keys()
                if regex.search(key) or regex.search(str(self._memory[key].value))
            ]

    def update_metadata(self, key: str, metadata: Dict[str, Any]) -> bool:
        with self._lock:
            if key in self._memory:
                self._memory[key].metadata.update(metadata)
                return True
            return False

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            history = self._history[-limit:] if limit > 0 else self._history
            return [entry.to_dict() for entry in history]

    def clear(self) -> None:
        with self._lock:
            self._history.extend(self._memory.values())
            self._memory.clear()
            print("🧹 共享记忆已清空")

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            agent_counts: Dict[str, int] = {}
            for entry in self._memory.values():
                agent_id = entry.agent_id or "system"
                agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1

            return {
                "total_entries": len(self._memory),
                "history_entries": len(self._history),
                "max_size": self._max_size,
                "agent_distribution": agent_counts,
                "keys": list(self._memory.keys())
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._memory)

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found in shared memory")
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"SharedMemory(entries={stats['total_entries']}, history={stats['history_entries']})"
