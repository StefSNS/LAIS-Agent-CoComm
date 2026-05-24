"""
OpenCode-CoComm Bridge
Bridges OpenCode SQLite database with CoComm shared memory.
"""

import sys
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opencode-cocomm-bridge")


class OpenCodeCoCommBridge:
    """Bridge OpenCode SQLite database to CoComm shared memory."""

    def __init__(self, opencode_data_dir: Path, cocomm_data_dir: Path):
        self.opencode_dir = Path(opencode_data_dir)
        self.cocomm_dir = Path(cocomm_data_dir)
        self.cocomm_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.opencode_dir / "opencode.db"
        
        # Initialize CoComm shared memory
        sys.path.insert(0, str(self.cocomm_dir.parent / "src"))
        from agent_sync.memory_sync import SharedMemory
        
        self._memory_file = self.cocomm_dir / "shared_memory.json"
        self._memory_file.write_text('{"entries": [], "agents": {}}')
        self._sm = SharedMemory(self.cocomm_dir)
        
        logger.info(f"OpenCode dir: {self.opencode_dir}")
        logger.info(f"CoComm dir: {self.cocomm_dir}")
        logger.info(f"OpenCode DB: {self.db_path}")

    def _query_db(self, query: str, params: tuple = ()) -> List[tuple]:
        """Query OpenCode SQLite database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.debug(f"DB query error: {e}")
            return []

    def sync_sessions(self) -> int:
        """Sync OpenCode sessions to CoComm shared memory."""
        count = 0
        
        # Get recent sessions (using correct column names)
        sessions = self._query_db(
            "SELECT id, title, model, directory, time_updated FROM session ORDER BY time_updated DESC LIMIT 20"
        )
        
        for session in sessions:
            session_id = session.get('id', '')[:16]
            title = session.get('title', 'Unknown')
            
            # Parse model if it's JSON
            model = session.get('model', 'Unknown')
            if model and isinstance(model, str) and model.startswith('{'):
                try:
                    model_data = json.loads(model)
                    model = model_data.get('id', model)
                except:
                    pass
            
            self._sm.store(
                agent="opencode",
                key=f"session_{session_id}",
                value=f"{title} | Model: {model}",
                category="opencode_session"
            )
            count += 1
        
        if count > 0:
            logger.info(f"Synced {count} OpenCode sessions to CoComm")
        
        return count

    def sync_messages(self, session_id: str = None, limit: int = 50) -> int:
        """Sync OpenCode messages to CoComm shared memory."""
        count = 0
        
        # Check message table schema
        msg_cols = self._query_db("PRAGMA table_info(message)")
        col_names = [c['name'] for c in msg_cols]
        
        if session_id:
            query = f"SELECT id, session_id, role, content, time_created FROM message WHERE session_id = ? ORDER BY time_created DESC LIMIT ?"
            messages = self._query_db(query, (session_id, limit))
        else:
            query = f"SELECT id, session_id, role, content, time_created FROM message ORDER BY time_created DESC LIMIT ?"
            messages = self._query_db(query, (limit,))
        
        for msg in messages:
            key = f"msg_{msg.get('id', 'unknown')}"[:32]
            role = msg.get('role', 'unknown')
            content = str(msg.get('content', ''))[:200]
            
            self._sm.store(
                agent="opencode",
                key=key,
                value=f"[{role}] {content}",
                category="opencode_message"
            )
            count += 1
        
        if count > 0:
            logger.info(f"Synced {count} messages to CoComm")
        
        return count

    def get_recent_context(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation context."""
        context = []
        
        # Get recent sessions
        sessions = self._query_db(
            "SELECT id, title, model, directory FROM session ORDER BY time_updated DESC LIMIT ?",
            (limit,)
        )
        
        for session in sessions:
            sid = session.get('id', '')[:16]
            title = session.get('title', 'Unknown')
            
            # Parse model
            model = session.get('model', 'Unknown')
            if model and isinstance(model, str) and model.startswith('{'):
                try:
                    model_data = json.loads(model)
                    model = model_data.get('id', model)
                except:
                    pass
            
            # Get last message for this session
            messages = self._query_db(
                "SELECT role, content FROM message WHERE session_id = ? ORDER BY time_created DESC LIMIT 1",
                (session.get('id'),)
            )
            
            if messages:
                context.append({
                    "session_id": sid,
                    "session_title": title,
                    "model": model,
                    "directory": session.get('directory', ''),
                    "last_message": {
                        "role": messages[0].get('role'),
                        "content": str(messages[0].get('content', ''))[:100]
                    }
                })
        
        return context

    def store(self, agent: str, key: str, value: Any, category: str = "general"):
        """Store value in shared memory via CoComm."""
        if isinstance(value, dict):
            value = json.dumps(value)
        self._sm.store(agent, key, str(value)[:500], category)

    def retrieve(self, agent: str = "opencode", key: str = None, category: str = None) -> list:
        """Retrieve from shared memory."""
        return self._sm.retrieve(agent, key, category)

    def search(self, query: str) -> list:
        """Search shared memory."""
        return self._sm.cross_agent_search(query)

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        sync_status = self._sm.get_sync_status()
        
        # Get session count from DB
        sessions = self._query_db("SELECT COUNT(*) as count FROM session")
        db_sessions = sessions[0]['count'] if sessions else 0
        
        return {
            "opencode_dir": str(self.opencode_dir),
            "cocomm_dir": str(self.cocomm_dir),
            "db_sessions": db_sessions,
            "shared_memory_entries": sync_status["total_entries"],
            "agents_in_memory": sync_status["agents"],
            "last_check": datetime.now().isoformat()
        }

    def sync_all(self) -> Dict[str, int]:
        """Sync all OpenCode data to CoComm."""
        results = {
            "sessions": self.sync_sessions(),
            "messages": self.sync_messages(limit=20)
        }
        return results


def create_bridge() -> OpenCodeCoCommBridge:
    """Create bridge instance."""
    opencode_dir = Path.home() / ".local" / "share" / "opencode"
    cocomm_dir = Path("C:/Users/stefa/Desktop/AI projects/integrations/cocomm/data")
    
    return OpenCodeCoCommBridge(opencode_dir, cocomm_dir)


if __name__ == "__main__":
    print("OpenCode-CoComm Bridge")
    print("=" * 50)
    
    bridge = create_bridge()
    
    print(f"\nStatus: {bridge.get_status()}")
    
    print(f"\nSyncing all data...")
    results = bridge.sync_all()
    print(f"Synced: {results}")
    
    print(f"\nRecent context:")
    context = bridge.get_recent_context(3)
    for c in context:
        print(f"  - {c['session_name']} ({c['model']})")
    
    print(f"\nFinal status: {bridge.get_status()}")