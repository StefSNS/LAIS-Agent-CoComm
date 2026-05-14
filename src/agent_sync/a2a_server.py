"""
A2A Server - HTTP server for agent-to-agent communication.
Provides task submission, messaging, and agent discovery endpoints.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


A2A_VERSION = "1.0"
DEFAULT_PORT = 8020


class A2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for A2A protocol endpoints."""

    protocol: Optional['ProtocolLayer'] = None

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _get_agent_card(self) -> dict:
        """Build A2A Agent Card."""
        agents = self.protocol.list_agents() if self.protocol else []
        return {
            "name": "LAIS-agent-CoComm",
            "description": "Multi-agent coordination framework",
            "url": f"http://localhost:{DEFAULT_PORT}",
            "version": A2A_VERSION,
            "capabilities": ["a2a/task_submit", "a2a/task_status", "a2a/agent_discovery"],
            "agents": agents
        }

    def _parse_path(self):
        parsed = urlparse(self.path)
        return parsed.path.rstrip("/"), parsed

    def do_GET(self):
        path, parsed = self._parse_path()

        if path in ("/.well-known/agent-card", "/a2a/agent-card"):
            self._send_json(self._get_agent_card())

        elif path == "/a2a/tasks/cleanup":
            if not self.protocol:
                self.send_response(500)
                self.wfile.write(b'{"error": "Protocol not initialized"}')
                return
            hours = int(dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("hours", "1"))
            removed = self.protocol.cleanup_completed_tasks(hours)
            self._send_json({"removed": removed, "message": f"Removed {removed} completed tasks older than {hours}h"})

        elif path == "/a2a/tasks":
            agent = dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("agent")
            status = dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("status")
            tasks = self.protocol.list_tasks(agent=agent, status=status) if self.protocol else []
            self._send_json({"tasks": tasks})

        elif path.startswith("/a2a/tasks/"):
            task_id = path[len("/a2a/tasks/"):]
            if not task_id:
                self.send_response(400)
                self.wfile.write(b'{"error": "Missing task_id"}')
                return
            task = self.protocol.get_task(task_id) if self.protocol else None
            if not task:
                self.send_response(404)
                self.wfile.write(b'{"error": "Task not found"}')
                return
            self._send_json(task)

        elif path == "/a2a/messages/cleanup":
            if not self.protocol:
                self.send_response(500)
                self.wfile.write(b'{"error": "Protocol not initialized"}')
                return
            hours = int(dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("hours", "24"))
            removed = self.protocol.cleanup_messages(hours)
            self._send_json({"removed": removed, "message": f"Removed {removed} expired messages"})

        elif path == "/a2a/messages/clear":
            if not self.protocol:
                self.send_response(500)
                self.wfile.write(b'{"error": "Protocol not initialized"}')
                return
            removed = self.protocol.clear_responded_messages()
            self._send_json({"removed": removed, "message": f"Cleared {removed} stale messages"})

        elif path == "/a2a/messages":
            agent = dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("agent")
            unread_only = dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p).get("unread") == "true"
            messages = self.protocol.get_messages(agent=agent, unread_only=unread_only) if self.protocol else []
            self._send_json({"messages": messages, "count": len(messages)})

        elif path == "/status":
            status = self.protocol.get_status() if self.protocol else {}
            self._send_json(status)

        else:
            self.send_response(404)
            self.wfile.write(b'{"error": "Not found"}')

    def do_POST(self):
        path, _ = self._parse_path()
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if path == "/a2a/tasks":
            if not self.protocol:
                self.send_response(500)
                self.wfile.write(b'{"error": "Protocol not initialized"}')
                return

            task = self.protocol.delegate_task(
                from_agent=data.get("from_agent", "remote"),
                to_agent=data.get("to_agent"),
                task_type=data.get("task_type", "generic"),
                payload=data.get("payload", {}),
                priority=data.get("priority", "normal")
            )
            self._send_json(task.to_dict(), 201)

        elif path == "/a2a/message":
            if not self.protocol:
                self.send_response(500)
                self.wfile.write(b'{"error": "Protocol not initialized"}')
                return

            msg_id = self.protocol.send_message(
                from_agent=data.get("from_agent", "remote"),
                to_agent=data.get("to_agent"),
                message=data.get("message", ""),
                message_type=data.get("message_type", "request")
            )
            if msg_id:
                self._send_json({"message_id": msg_id, "status": "sent"}, 201)
            else:
                self.send_response(404)
                self.wfile.write(b'{"error": "Unknown agent"}')

        else:
            self.send_response(404)
            self.wfile.write(b'{"error": "Not found"}')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass


class Task:
    """A2A Task representation."""

    def __init__(self, task_id: str, from_agent: str, to_agent: str,
                 task_type: str, payload: dict, priority: str = "normal"):
        self.task_id = task_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.result = None

    def complete(self, result: dict = None):
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        self.result = result or {"status": "executed_locally"}

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result
        }


class Message:
    """A2A Message representation."""

    def __init__(self, msg_id: str, from_agent: str, to_agent: str,
                 message: str, message_type: str = "request"):
        self.msg_id = msg_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.message = message
        self.message_type = message_type
        self.timestamp = datetime.now().isoformat()
        self.read = False
        self.responded = False

    def to_dict(self) -> dict:
        return {
            "message_id": self.msg_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message": self.message,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "read": self.read,
            "responded": self.responded
        }


class ProtocolLayer:
    """A2A protocol implementation."""

    def __init__(self):
        self._tasks = []
        self._messages = []
        self._agents = []
        self._lock = threading.Lock()
        self._init_default_agents()

    def _init_default_agents(self):
        self._agents = [
            {"agent_id": "lais", "name": "LAIS", "capabilities": ["orchestration", "gui", "chat"]},
            {"agent_id": "jarvis", "name": "Jarvis", "capabilities": ["voice", "text", "search"]},
            {"agent_id": "opencode", "name": "OpenCode", "capabilities": ["code", "shell", "git"]},
            {"agent_id": "claude", "name": "Claude", "capabilities": ["code", "reasoning", "analysis"]}
        ]

    def register_agent(self, agent_id: str, name: str, capabilities: list):
        with self._lock:
            for a in self._agents:
                if a["agent_id"] == agent_id:
                    a.update({"name": name, "capabilities": capabilities})
                    return
            self._agents.append({"agent_id": agent_id, "name": name, "capabilities": capabilities})

    def list_agents(self) -> list:
        return self._agents

    def delegate_task(self, from_agent: str, to_agent: str,
                     task_type: str, payload: dict, priority: str = "normal") -> Task:
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(task_id, from_agent, to_agent, task_type, payload, priority)

        with self._lock:
            self._tasks.append(task)
            # Auto-complete for demo (real impl would queue)
            task.complete()

        return task

    def get_task(self, task_id: str) -> Optional[dict]:
        for task in self._tasks:
            if task.task_id == task_id:
                return task.to_dict()
        return None

    def list_tasks(self, agent: str = None, status: str = None) -> list:
        tasks = self._tasks
        if agent:
            tasks = [t for t in tasks if t.to_agent == agent or t.from_agent == agent]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [t.to_dict() for t in tasks[-50:]]

    def send_message(self, from_agent: str, to_agent: str,
                    message: str, message_type: str = "request") -> Optional[str]:
        import uuid
        msg_id = f"msg_{from_agent}_{to_agent}_{uuid.uuid4().hex[:8]}"
        msg = Message(msg_id, from_agent, to_agent, message, message_type)

        with self._lock:
            self._messages.append(msg)

        return msg_id

    def get_messages(self, agent: str = None, unread_only: bool = False) -> list:
        """Get messages, optionally filtered by agent or unread status."""
        messages = self._messages
        if agent:
            messages = [m for m in messages if m.to_agent == agent or m.from_agent == agent]
        if unread_only:
            messages = [m for m in messages if not m.read and not m.responded]
        return [m.to_dict() for m in messages[-50:]]

    def cleanup_completed_tasks(self, max_age_hours: int = 1) -> int:
        """Remove completed tasks older than max_age_hours."""
        from datetime import datetime
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        to_remove = []
        for task in self._tasks:
            if task.status not in ("completed", "failed"):
                continue
            try:
                created = datetime.fromisoformat(task.created_at.replace("Z", "+00:00")).timestamp()
                if created < cutoff:
                    to_remove.append(task.task_id)
            except Exception:
                pass
        for task_id in to_remove:
            self._tasks = [t for t in self._tasks if t.task_id != task_id]
        return len(to_remove)

    def cleanup_messages(self, max_age_hours: int = 24) -> int:
        """Remove messages older than max_age_hours."""
        from datetime import datetime
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        to_remove = []
        for msg in self._messages:
            try:
                ts = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00")).timestamp()
                if ts < cutoff:
                    to_remove.append(msg.msg_id)
            except Exception:
                pass
        for msg_id in to_remove:
            self._messages = [m for m in self._messages if m.msg_id != msg_id]
        return len(to_remove)

    def clear_responded_messages(self) -> int:
        """Remove all messages with status 'responded' or 'read'."""
        before = len(self._messages)
        self._messages = [m for m in self._messages if not m.responded and not m.read]
        return before - len(self._messages)

    def get_status(self) -> dict:
        return {
            "server": "LAIS-agent-CoComm",
            "version": A2A_VERSION,
            "agents_registered": len(self._agents),
            "tasks_total": len(self._tasks),
            "messages_total": len(self._messages)
        }


class A2AServer:
    """A2A HTTP server."""

    def __init__(self, protocol: ProtocolLayer = None, port: int = DEFAULT_PORT):
        self.protocol = protocol or ProtocolLayer()
        self.port = port
        self.host = "localhost"
        self.server = None
        self.thread = None
        self.running = False

        A2ARequestHandler.protocol = self.protocol
        A2ARequestHandler.server_name = "LAIS-agent-CoComm"

    def start(self):
        if self.running:
            return
        self.server = HTTPServer((self.host, self.port), A2ARequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.running = True
        print(f"[A2AServer] Started at http://{self.host}:{self.port}")

    def stop(self):
        if self.server and self.running:
            self.server.shutdown()
            self.running = False

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


def start_a2a_server(port: int = DEFAULT_PORT) -> A2AServer:
    """Factory function to start A2A server."""
    server = A2AServer(port=port)
    server.start()
    return server


if __name__ == "__main__":
    print("=== LAIS-agent-CoComm A2A Server ===")
    server = start_a2a_server()
    print("Press Ctrl+C to stop")
    try:
        while server.running:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        server.stop()
        print("Server stopped")