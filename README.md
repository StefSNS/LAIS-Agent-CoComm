> **⚠️ ARCHIVED — 2026-06-10**
>
> This repository is **outdated and no longer actively maintained**.
>
> **What changed:** LAIS has evolved substantially. The current system includes CSI-Fusion (WiFi sensing security system), Hermes Agent (multi-platform CLI with MCP), LAIS Desktop (Electron app), and a 4-agent architecture with production deployments. None of these are reflected here.
>
> **Why archived:** The public code no longer represents the actual system. This repo is preserved as a **historical reference only**.
>
> **Status:** Read-only. No further updates, issues, or PRs will be accepted.
>
> ---

# LAIS-agent-CoComm
### Local AI System - Age nt-to-Agent Communication & Coordination

A l ightweight, standalone multi-agent coordinati on framework for AI systems. Enables cross-ag ent task delegation, shared memory, real-time  file watching, and structured communication  without requiring cloud services.

---

## Fe atures

| Feature | Description |
|---------| -------------|
| **A2A Server** | HTTP server  for agent task delegation and messaging |
|  **MCP Bridge** | Model Context Protocol integ ration for external tools |
| **WebSocket Ser ver** | Real-time bidirectional agent communi cation |
| **Shared Memory** | Cross-agent me mory with priority levels and access tracking  |
| **FileWatcher** | Real-time file monitor ing (watchdog) with polling fallback |
| **Tr igger System** | Event-driven triggers with t yped callbacks |
| **4-Tier Memory** | Hot/Wa rm/Cold/Crystallized memory architecture |
|  **Session Persistence** | Cross-session conti nuity with SQLite + JSON |
| **Cross-Terminal ** | Works across multiple terminals via shar ed files |
| **Local-First** | No cloud depen dency, runs on any machine |

---

## Quick S tart

```bash
pip install -e .
```

```python 
from agent_sync import ActiveSessionLog, Sha redMemory, A2AServer, MCPBridge

# Start sess ion monitoring
log = ActiveSessionLog()

# Sh are memory with other agents
memory = SharedM emory()
memory.store("agent_a", "task_status" , "processing", priority="high")

# Connect M CP tools
mcp = MCPBridge()
mcp.add_server("gi thub", "GitHub MCP", ["npx", "-y", "@modelcon textprotocol/server-github"])

# Start A2A se rver
server = A2AServer()
server.start()
```
 
---

## Architecture

```
┌───── ─────────────── ─────────────── ─────────────── ───────────┐
│                     LAIS-agent-CoComm                         │
├───────── ─────────────── ─────────────── ─────────────── ───────┤
│  A2A Server (por t 8020)                                    � �
│  ├── Task submission  /a2a/tasks                            │
│  ├──  Messaging         /a2a/message                          │
│  └── Agent discovery    /a2a/agent-card                     │
├ ─────────────── ─────────────── ─────────────── ─────────────── ─┤
│  Coordination Layer                                          │
│  ├──  ActiveSessionLog  - Session + task coordinati on       │
│  ├── SharedMemory       - Cross-agent memory store          │
│   ├── TriggerManager    - Event-driven c allbacks            │
│  └── FileWa tcher       - Real-time file change detection    │
├───────────� �──────────────� �──────────────� �──────────────� �────┤
│  Storage                                                     │
│   ├── JSON files     - Active sessions, s hared memory       │
│  └── SQLite          - Archived sessions, long-term         │
└────────────� ��──────────────� ��──────────────� ��──────────────� ��───┘
```

---

## Comparison with S imilar Systems

| Feature | LAIS | crewAI | w shobson/agents | Agent-MCP |
|---------|----- -|--------|-----------------|-----------|
| L ocal-first | ✅ | ❌ | ✅ | ❌ |
| A2A pr otocol | ✅ | ❌ | ❌ | ✅ |
| MCP integr ation | ✅ | ❌ | ❌ | ✅ |
| WebSocket s upport | ✅ | ❌ | ❌ | ❌ |
| FileWatche r | ✅ | ❌ | ❌ | ❌ |
| 4-tier memory |  ✅ | ❌ | ❌ | ❌ |
| Vault integration  | ✅ | ❌ | ❌ | ❌ |
| Cross-terminal |  ✅ | ❌ | ❌ | ❌ |
| Shared memory | ✅  | Partial | ❌ | ✅ |

---

## Agent Commu nication Flow

```python
# Agent A sends task  to Agent B
from agent_sync import A2AServer
 
server = A2AServer()

# Agent A submits task 
server.protocol.delegate_task(
    from_agen t="agent_a",
    to_agent="agent_b", 
    tas k_type="code",
    payload={"description": "F ix bug in module X"},
    priority="high"
)

 # Agent B receives via polling or file watche r
```

---

## Shared Memory Example

```pyth on
from agent_sync import SharedMemory

memor y = SharedMemory()

# Store with priority
mem ory.store("lais", "project_status", "Active d evelopment", priority="high")

# Retrieve wit h access tracking
results = memory.retrieve(" opencode", category="project")

# Cross-agent  search
found = memory.cross_agent_search("de velopment")
```

---

## File Watching for Cr oss-Terminal Sync

```python
from agent_sync  import ActiveSessionLog

log = ActiveSessionL og(
    shared_path="/shared/folder/active_se ssions.json"
)

# Auto-starts FileWatcher (wa tchdog) or polling fallback
# Remote changes  are detected instantly
```

---

## WebSocket  Server Example

```python
from agent_sync im port WebSocketServer

server = WebSocketServe r(host="127.0.0.1", port=8765)

async def mai n():
    await server.start()
    # Agents ca n now connect and communicate in real-time

a syncio.run(main())
```

---

## Environment V ariables

| Variable | Default | Description  |
|----------|---------|-------------|
| `LAI S_AUTO_MONITOR` | `true` | Auto-start file wa tching |
| `LAIS_POLL_INTERVAL` | `10.0` | Po lling interval (seconds) |
| `LAIS_SHARED_SES SION_PATH` | — | Cross-terminal session fil e |
| `LAIS_AGENT_ID` | `opencode` | Agent id entifier |

---

## Requirements

- Python 3. 10+
- watchdog (optional, for file watching)
 - aiosqlite (optional, for async SQLite)
- as yncio (built-in)

---

## License

MIT Licens e - Free for personal and commercial use.

-- -

Built for the [[LAIS]] multi-agent system  by Stefa. 