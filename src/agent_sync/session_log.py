"""
ActiveSessionLog - Session and Task Coordination
Manages cross-agent sessions with FileWatcher and polling fallback.
"""

import json
import os
import sqlite3
import threading
import time
import uuid
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class HybridStorage:
    """Hybrid JSON + SQLite storage for sessions."""

    def __init__(self, json_path: Path, sqlite_path: Path):
        self.json_path = Path(json_path)
        self.sqlite_path = Path(sqlite_path)
        self._lock = threading.Lock()
        self._init_sqlite()

    def _init_sqlite(self):
        with self._lock:
            conn = sqlite3.connect(str(self.sqlite_path))
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS sessions
                (session_id TEXT PRIMARY KEY, data TEXT, archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("""CREATE TABLE IF NOT EXISTS tasks
                (id INTEGER PRIMARY KEY, session_id TEXT, description TEXT,
                 archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()
            conn.close()

    def write_json(self, data: dict):
        with self._lock:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def read_json(self) -> dict:
        with self._lock:
            if not self.json_path.exists():
                return {}
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)


class FileWatcher:
    """File change detection with watchdog (preferred) or polling fallback."""

    def __init__(self, path: Path, callback, poll_interval: float = 5.0):
        self.path = Path(path)
        self.callback = callback
        self.poll_interval = poll_interval
        self._watchdog = self._check_watchdog()
        self._running = False
        self._observer = None
        self._poll_thread = None
        self._last_mtime = self.path.stat().st_mtime if self.path.exists() else None

    def _check_watchdog(self) -> bool:
        try:
            import watchdog
            return True
        except ImportError:
            return False

    def start(self):
        if self._watchdog:
            self._start_watchdog()
        else:
            self._start_polling()
        self._running = True

    def _start_watchdog(self):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class Handler(FileSystemEventHandler):
                def __init__(self, watcher):
                    self.watcher = watcher
                def on_modified(self, event):
                    if event.src_path == str(self.watcher.path):
                        self.watcher.callback()

            self._observer = Observer()
            self._observer.schedule(Handler(self), str(self.path.parent), recursive=False)
            self._observer.start()
        except Exception:
            self._watchdog = False
            self._start_polling()

    def _start_polling(self):
        def poll():
            while self._running:
                if self.path.exists():
                    mtime = self.path.stat().st_mtime
                    if self._last_mtime and mtime != self._last_mtime:
                        self._last_mtime = mtime
                        self.callback()
                    elif self._last_mtime is None:
                        self._last_mtime = mtime
                time.sleep(self.poll_interval)
        self._poll_thread = threading.Thread(target=poll, daemon=True)
        self._poll_thread.start()

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()


class TriggerManager:
    """Event-driven triggers with typed callbacks."""

    def __init__(self):
        self._callbacks = []
        self._type_callbacks = {}
        self._lock = threading.Lock()

    def register_callback(self, callback):
        with self._lock:
            self._callbacks.append(callback)

    def register_type_callback(self, event_type: str, callback):
        with self._lock:
            if event_type not in self._type_callbacks:
                self._type_callbacks[event_type] = []
            self._type_callbacks[event_type].append(callback)

    def trigger(self, source: str, data: dict):
        event_type = data.get("type", "")
        with self._lock:
            all_cbs = list(self._callbacks)
            type_cbs = list(self._type_callbacks.get(event_type, []))
        for cb in all_cbs + type_cbs:
            try:
                cb(source, data)
            except Exception as e:
                print(f"[TriggerManager] Callback error: {e}")


class ActiveSessionLog:
    """Main session coordination class with auto-monitoring."""

    def __init__(self, json_path: Optional[str] = None, db_path: Optional[str] = None,
                 shared_path: Optional[str] = None):
        base = Path(__file__).parent.parent / "data"
        base.mkdir(parents=True, exist_ok=True)

        self.json_path = Path(json_path) if json_path else base / "active_sessions.json"
        self.db_path = Path(db_path) if db_path else base / "sessions.db"
        self.shared_path = Path(shared_path) if shared_path else self.json_path

        self.storage = HybridStorage(self.json_path, self.db_path)
        self.trigger_manager = TriggerManager()
        self.file_watcher = None
        self._poll_running = False
        self._session_lock = threading.Lock()

        self._current_session = self.storage.read_json()

        # Auto-start monitoring
        if os.environ.get("LAIS_AUTO_MONITOR", "true").lower() == "true":
            self._enable_monitoring()

    @contextlib.contextmanager
    def _atomic_update(self):
        """Context manager for atomic session operations."""
        with self._session_lock:
            self._current_session = self.storage.read_json()
            yield self._current_session
            self.storage.write_json(self._current_session)

    def _enable_monitoring(self):
        """Enable FileWatcher or polling."""
        try:
            import watchdog
            self.file_watcher = FileWatcher(self.shared_path, self._on_remote_change)
            self.file_watcher.start()
            print("[ActiveSessionLog] FileWatcher started (watchdog)")
        except ImportError:
            self._start_polling()

    def _on_remote_change(self):
        """Callback when shared file changes."""
        self.trigger_manager.trigger("system", {"type": "remote_change", "source": "cross_terminal"})

    def _start_polling(self):
        """Fallback polling for systems without watchdog."""
        def poll():
            while self._poll_running:
                # Check for changes
                time.sleep(float(os.environ.get("LAIS_POLL_INTERVAL", "10.0")))
        self._poll_running = True
        threading.Thread(target=poll, daemon=True).start()

    def create_session(self, task_description: str, created_by: str,
                       capabilities_needed: list = None) -> dict:
        """Create a new session with task."""
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        task = {
            "id": f"task_{uuid.uuid4().hex[:8]}",
            "description": task_description,
            "priority": "medium",
            "assigned_to": [],
            "status": "pending",
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "subtasks": [],
            "logs": [],
            "capabilities_needed": capabilities_needed or []
        }
        session = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "tasks": [task],
            "agents": [],
            "execution_mode": "sequential"
        }
        with self._atomic_update() as s:
            s.update(session)
        return session

    def get_session(self) -> dict:
        """Get current session."""
        return self._current_session

    def update_task_status(self, task_id: str, status: str, result: str = None):
        """Update task status."""
        with self._atomic_update() as session:
            for task in session.get("tasks", []):
                if task["id"] == task_id:
                    task["status"] = status
                    task["logs"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "status_update",
                        "new_status": status
                    })
                    break