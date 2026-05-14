# LAIS-agent-CoComm
### Local AI System - Agent-to-Agent Communication & Coordination

A lightweight, standalone multi-agent coordination framework for AI systems. Enables cross-agent task delegation, shared memory, real-time file watching, and structured communication without requiring cloud services.

---

## Features

| Feature | Description |
|---------|-------------|
| **A2A Server** | HTTP server for agent task delegation and messaging |
| **Shared Memory** | Cross-agent memory with priority levels and access tracking |
| **FileWatcher** | Real-time file monitoring (watchdog) with polling fallback |
| **Trigger System** | Event-driven triggers with typed callbacks |
| **4-Tier Memory** | Hot/Warm/Cold/Crystallized memory architecture |
| **Session Persistence** | Cross-session continuity with SQLite + JSON |
| **Cross-Terminal** | Works across multiple terminals via shared files |
| **Local-First** | No cloud dependency, runs on any machine |

---

## Quick Start

```bash
pip install -e .
```

```python
from agent_sync import ActiveSessionLog, SharedMemory, A2AServer

# Start session monitoring
log = ActiveSessionLog()

# Share memory with other agents
memory = SharedMemory()
memory.store("agent_a", "task_status", "processing", priority="high")

# Start A2A server
server = A2AServer()
server.start()
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAIS-agent-CoComm                        │
├─────────────────────────────────────────────────────────────┤
│  A2A Server (port 8020)                                    │
│  ├── Task submission  /a2a/tasks                           │
│  ├── Messaging         /a2a/message                         │
│  └── Agent discovery   /a2a/agent-card                     │
├─────────────────────────────────────────────────────────────┤
│  Coordination Layer                                         │
│  ├── ActiveSessionLog  - Session + task coordination       │
│  ├── SharedMemory      - Cross-agent memory store          │
│  ├── TriggerManager    - Event-driven callbacks            │
│  └── FileWatcher       - Real-time file change detection   │
├─────────────────────────────────────────────────────────────┤
│  Storage                                                    │
│  ├── JSON files     - Active sessions, shared memory       │
│  └── SQLite         - Archived sessions, long-term        │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparison with Similar Systems

| Feature | LAIS | crewAI | wshobson/agents | Agent-MCP |
|---------|------|--------|-----------------|-----------|
| Local-first | ✅ | ❌ | ✅ | ❌ |
| A2A protocol | ✅ | ❌ | ❌ | ✅ |
| FileWatcher | ✅ | ❌ | ❌ | ❌ |
| 4-tier memory | ✅ | ❌ | ❌ | ❌ |
| Vault integration | ✅ | ❌ | ❌ | ❌ |
| Cross-terminal | ✅ | ❌ | ❌ | ❌ |
| Shared memory | ✅ | Partial | ❌ | ✅ |

---

## Agent Communication Flow

```python
# Agent A sends task to Agent B
from agent_sync import A2AServer

server = A2AServer()

# Agent A submits task
server.protocol.delegate_task(
    from_agent="agent_a",
    to_agent="agent_b", 
    task_type="code",
    payload={"description": "Fix bug in module X"},
    priority="high"
)

# Agent B receives via polling or file watcher
```

---

## Shared Memory Example

```python
from agent_sync import SharedMemory

memory = SharedMemory()

# Store with priority
memory.store("lais", "project_status", "Active development", priority="high")

# Retrieve with access tracking
results = memory.retrieve("opencode", category="project")

# Cross-agent search
found = memory.cross_agent_search("development")
```

---

## File Watching for Cross-Terminal Sync

```python
from agent_sync import ActiveSessionLog

log = ActiveSessionLog(
    shared_path="/shared/folder/active_sessions.json"
)

# Auto-starts FileWatcher (watchdog) or polling fallback
# Remote changes are detected instantly
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LAIS_AUTO_MONITOR` | `true` | Auto-start file watching |
| `LAIS_POLL_INTERVAL` | `10.0` | Polling interval (seconds) |
| `LAIS_SHARED_SESSION_PATH` | — | Cross-terminal session file |
| `LAIS_AGENT_ID` | `opencode` | Agent identifier |

---

## Requirements

- Python 3.10+
- watchdog (optional, for file watching)
- aiosqlite (optional, for async SQLite)

---

## License

MIT License - Free for personal and commercial use.

---

Built for the [[LAIS]] multi-agent system by Stefa.