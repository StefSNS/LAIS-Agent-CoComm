"""
SharedMemory - Cross-agent shared memory with priority and access tracking.
"""

import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from threading import Lock
from collections import defaultdict

DEFAULT_DIR = Path(__file__).parent.parent / "data"
DEFAULT_DIR.mkdir(parents=True, exist_ok=True)

SHARED_MEMORY_FILE = DEFAULT_DIR / "shared_memory.json"
SYNC_LOG_FILE = DEFAULT_DIR / "sync_log.json"

PRIORITY_KEYWORDS = {
    "high": {"urgent", "critical", "important", "fix", "bug", "error", "deploy", "code"},
    "medium": {"update", "change", "enhance", "feature", "design", "pattern"}
}


def determine_priority(value: str, key: str = "") -> str:
    """Auto-determine priority based on keywords."""
    combined = f"{key} {value}".lower()
    if any(k in combined for k in PRIORITY_KEYWORDS["high"]):
        return "high"
    if any(k in combined for k in PRIORITY_KEYWORDS["medium"]):
        return "medium"
    return "low"


class SharedMemory:
    """Cross-agent shared memory store."""

    def __init__(self, memory_dir: Path = None):
        self._dir = Path(memory_dir) if memory_dir else DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._memory_file = self._dir / "shared_memory.json"
        self._sync_log = self._dir / "sync_log.json"
        self._lock = Lock()
        self._triggers = defaultdict(list)
        self._data = self._load()
        self._init_triggers()

    def _load(self) -> dict:
        if self._memory_file.exists():
            try:
                return json.loads(self._memory_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"entries": [], "agents": {}}

    def _save(self):
        with self._lock:
            self._memory_file.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def _init_triggers(self):
        """Default high-priority notification trigger."""
        def notify(agent, entry):
            print(f"[SharedMemory] High-priority sync: {agent} -> {entry.get('key')}")
        self.register_trigger("all", notify)

    def register_trigger(self, agent: str, callback):
        self._triggers[agent].append(callback)

    def store(self, agent: str, key: str, value: str,
              category: str = "general", priority: str = None, notify: bool = True) -> bool:
        """Store a memory entry."""
        if priority is None:
            priority = determine_priority(value, key)

        now = datetime.now().isoformat()
        entry_id = f"{agent}_{key}_{int(time.time())}"

        existing = [e for e in self._data["entries"] if e["key"] == key and e.get("agent") == agent]

        if existing:
            existing[0].update({"value": value, "updated": now, "ttl": None, "priority": priority})
            entry = existing[0]
        else:
            entry = {
                "id": entry_id, "agent": agent, "key": key, "value": value,
                "category": category, "created": now, "updated": now, "ttl": None,
                "priority": priority, "accessed_by": [agent],
                "access_patterns": {agent: 1}, "auto_crystallized": False
            }
            self._data["entries"].append(entry)

        # Update agent activity
        if agent not in self._data["agents"]:
            self._data["agents"][agent] = {"first_seen": now, "last_active": now}
        self._data["agents"][agent]["last_active"] = now

        self._save()
        self._log_sync(agent, "store", key, priority)

        if priority == "high" and notify:
            self._notify_triggers(agent, entry)

        return True

    def _notify_triggers(self, agent, entry):
        for callback in self._triggers.get("all", []) + self._triggers.get(agent, []):
            try:
                callback(agent, entry)
            except Exception as e:
                print(f"[SharedMemory] Trigger error: {e}")

    def retrieve(self, agent: str, key: str = None, category: str = None,
                 limit: int = 10, update_access: bool = True) -> list:
        """Retrieve memory entries."""
        results = []
        for entry in self._data["entries"]:
            if key and entry["key"] != key:
                continue
            if category and entry.get("category") != category:
                continue

            if update_access:
                if "accessed_by" not in entry:
                    entry["accessed_by"] = []
                if agent not in entry["accessed_by"]:
                    entry["accessed_by"].append(agent)
                entry["access_patterns"][agent] = entry["access_patterns"].get(agent, 0) + 1

            results.append(entry)

        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        if update_access:
            self._save()
        return results[:limit]

    def cross_agent_search(self, query: str, limit: int = 20) -> list:
        """Search across all agents' memories."""
        q = query.lower()
        results = []
        for entry in self._data["entries"]:
            score = 0
            if q in entry.get("key", "").lower(): score += 3
            if q in entry.get("value", "").lower(): score += 2
            if q in entry.get("category", "").lower(): score += 1
            if score > 0:
                results.append((entry, score))
        results.sort(key=lambda x: (x[1], x[0].get("updated", "")), reverse=True)
        return [e for e, _ in results[:limit]]

    def get_sync_status(self) -> dict:
        """Get comprehensive sync status."""
        priorities = defaultdict(int)
        crystallized = 0
        for entry in self._data["entries"]:
            priorities[entry.get("priority", "low")] += 1
            if entry.get("auto_crystallized"):
                crystallized += 1
        return {
            "total_entries": len(self._data["entries"]),
            "agents": list(self._data.get("agents", {}).keys()),
            "last_sync": self._data.get("last_sync"),
            "priority_counts": dict(priorities),
            "crystallized": crystallized
        }

    def _log_sync(self, agent: str, action: str, key: str, priority: str = "low"):
        log_entry = {"timestamp": datetime.now().isoformat(), "agent": agent,
                     "action": action, "key": key, "priority": priority}
        try:
            log = json.loads(self._sync_log.read_text()) if self._sync_log.exists() else []
            log.append(log_entry)
            self._sync_log.write_text(json.dumps(log[-200:], indent=2))
        except Exception:
            pass

    def log_session_action(self, agent: str, action: str, context: dict = None,
                           metadata: dict = None):
        """Log agent session action for traceability."""
        action_hash = hashlib.md5(f"{agent}{action}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        trace = {
            "trace_id": f"trace_{action_hash}",
            "timestamp": datetime.now().isoformat(),
            "agent": agent, "action": action,
            "context": context or {}, "metadata": metadata or {}
        }
        trace_file = self._dir / f"{agent}_trace.json"
        try:
            traces = json.loads(trace_file.read_text()) if trace_file.exists() else []
            traces.append(trace)
            trace_file.write_text(json.dumps(traces[-500:], indent=2))
        except Exception as e:
            print(f"[SharedMemory] Failed to log session action: {e}")
        return trace["trace_id"]


def load_shared_memory(memory_dir: Path = None) -> SharedMemory:
    """Factory function."""
    return SharedMemory(memory_dir)