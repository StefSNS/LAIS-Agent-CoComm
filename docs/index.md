---
layout: home
title: LAIS-agent-CoComm
nav_order: 1
---

# LAIS-agent-CoComm

**Agent-to-Agent Communication & Coordination Framework**

A lightweight, standalone multi-agent coordination framework for AI systems. Enables cross-agent task delegation, shared memory, real-time file watching, and structured communication without requiring cloud services.

{: .highlight }
> Built for the LAIS multi-agent system. Open source and free for any AI to integrate.

---

## Features

| Feature | Description |
|---------|-------------|
| **A2A Server** | HTTP server for agent task delegation and messaging |
| **Shared Memory** | Cross-agent memory with priority levels and access tracking |
| **FileWatcher** | Real-time file monitoring (watchdog) with polling fallback |
| **Async Agents** | Durable async agents with checkpoint/resume |
| **Goal Planning** | Auto-decompose goals into parallelizable task DAGs |
| **Consensus Engine** | Multi-agent voting and negotiation |
| **Self-Healing** | Auto-adapt task graphs on failures |
| **Trust System** | Agent reputation and escrow for coordination |

---

## Quick Start

```bash
pip install lais-agent-cocomm
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
│  ├── AsyncAgent        - Durable async execution           │
│  ├── TaskDAG           - Goal decomposition               │
│  ├── ConsensusEngine    - Multi-agent voting               │
│  └── TriggerManager     - Event-driven callbacks            │
└─────────────────────────────────────────────────────────────┘
```

---

## Documentation

- [Getting Started](getting-started.html) - Installation and first steps
- [API Reference](api-reference.html) - Complete module documentation
- [Examples](examples.html) - Usage examples and patterns
- [Architecture](architecture.html) - System design overview

---

## Comparison

| Feature | LAIS | CrewAI | mcp-agent | open-multi-agent |
|---------|------|--------|-----------|------------------|
| Local-first | ✅ | ❌ | ❌ | ❌ |
| A2A protocol | ✅ | ❌ | ❌ | ❌ |
| FileWatcher | ✅ | ❌ | ❌ | ❌ |
| Consensus engine | ✅ | ❌ | ❌ | ❌ |
| Self-healing | ✅ | ❌ | ❌ | ❌ |
| Trust/escrow | ✅ | ❌ | ❌ | ❌ |

---

## License

MIT License - Free for personal and commercial use.

---

[View on GitHub](https://github.com/StefSNS/LAIS-Agent-CoComm){: .btn }