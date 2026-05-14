---
layout: page
title: Getting Started
nav_order: 2
---

# Getting Started

## Installation

### Using pip

```bash
pip install lais-agent-cocomm
```

### From source

```bash
git clone https://github.com/StefSNS/LAIS-Agent-CoComm.git
cd LAIS-Agent-CoComm
pip install -e .
```

### Requirements

- Python 3.10+
- watchdog (optional, for FileWatcher)
- aiosqlite (optional, for async SQLite)

## Your First Agent

```python
from agent_sync import ActiveSessionLog, SharedMemory

# Create session log
log = ActiveSessionLog()

# Create a session with a task
session = log.create_session(
    task_description="Review code for bugs",
    created_by="claude",
    capabilities_needed=["code", "reasoning"]
)

# Share state with other agents
memory = SharedMemory()
memory.store("claude", "session_id", session["session_id"], priority="high")
```

## Start A2A Server

```python
from agent_sync import A2AServer, start_a2a_server

# Option 1: Quick start
server = start_a2a_server()

# Option 2: Custom config
server = A2AServer(port=8080)
server.start()

print(f"Server running at {server.url}")
```

## CLI Tool

```bash
# Start server
agent-sync start

# Check status
agent-sync status

# Delegate task
agent-sync delegate --to opencode --task "Fix bug in module X"

# List agents
agent-sync list

# View failed tasks
agent-sync dlq
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LAIS_AUTO_MONITOR` | `true` | Auto-start file watching |
| `LAIS_POLL_INTERVAL` | `10.0` | Polling interval (seconds) |
| `LAIS_SHARED_SESSION_PATH` | — | Cross-terminal session file |
| `LAIS_AGENT_ID` | `opencode` | Agent identifier |

## Next Steps

- [API Reference](api-reference.html) - Complete module documentation
- [Examples](examples.html) - Usage examples
- [Architecture](architecture.html) - System design