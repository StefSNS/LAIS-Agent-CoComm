---
layout: page
title: Architecture
nav_order: 5
---

# Architecture

## System Overview

LAIS-agent-CoComm is a layered architecture for multi-agent coordination:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│         (Your agents, custom handlers, integrations)        │
├─────────────────────────────────────────────────────────────┤
│                    Coordination Layer                         │
│  ┌─────────────┬──────────────┬─────────────────────────┐  │
│  │   A2A       │   Handoff    │      Consensus          │  │
│  │   Server    │   Chains     │      Engine            │  │
│  └─────────────┴──────────────┴─────────────────────────┘  │
│  ┌─────────────┬──────────────┬─────────────────────────┐  │
│  │   Async     │   Goal DAG   │      Self-Healing      │  │
│  │   Agents    │   Planner    │      Graphs            │  │
│  └─────────────┴──────────────┴─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Memory Layer                              │
│  ┌─────────────┬──────────────┬─────────────────────────┐  │
│  │  Shared     │  Session     │      Trust             │  │
│  │  Memory     │  Log         │      System            │  │
│  └─────────────┴──────────────┴─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer                           │
│  ┌─────────────┬──────────────┬─────────────────────────┐  │
│  │   HTTP      │   File        │      (WebSocket)        │  │
│  │   A2A       │   Watching    │      (Future)          │  │
│  └─────────────┴──────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### A2A Server

HTTP server implementing the Agent-to-Agent protocol.

- **Endpoint**: `http://localhost:8020`
- **Protocol**: REST with JSON
- **Features**:
  - Agent discovery (`/a2a/agent-card`)
  - Task submission (`POST /a2a/tasks`)
  - Messaging (`POST /a2a/message`)
  - Status monitoring (`/status`)

### Shared Memory

Cross-agent memory store with:

- Priority levels (high/medium/low)
- Access tracking
- TTL support
- Cross-agent search

### Active Session Log

Coordinates multi-agent sessions:

- JSON + SQLite hybrid storage
- FileWatcher for cross-terminal sync
- Polling fallback
- Trigger callbacks

## Coordination Patterns

### 1. Direct Delegation

```
Agent A → [Task] → Agent B
```

Simple one-to-one task assignment via A2A.

### 2. Handoff Chain

```
Agent A → [Complete] → Agent B → [Complete] → Agent C
```

Sequential handoff where each agent completes and passes to next.

### 3. Parallel Execution

```
           → Agent B
Task → ────┼──→ Agent C  (Same task, multiple agents)
           → Agent D
```

Same task executed by multiple agents (with consensus on result).

### 4. DAG Execution

```
    [Design]
        │
   ┌────┴────┐
[Backend]  [Frontend]
   │           │
   └────┬──────┘
        │
     [Integrate]
        │
     [Deploy]
```

Directed Acyclic Graph with dependencies.

## Data Flow

### Task Delegation Flow

```
User/Trigger → A2A Server → Protocol Layer → Task Queue
                                              │
                         ┌─────────────────────┘
                         ↓
              ┌──────────┴──────────┐
              │                     │
          Local Agent          Remote Agent
              │                     │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │   Shared Memory     │
              │   (State + Results) │
              └─────────────────────┘
```

### Cross-Terminal Flow

```
Terminal 1                    Terminal 2
    │                              │
    ├─ Write active_sessions.json ─┤
    │                              │
    │         FileWatcher           │
    │              │                │
    │              ↓                │
    └──── Detect change ───────────┘
                  │
                  ↓
         TriggerManager → Callbacks
```

## Configuration

### Environment Variables

```bash
# Monitoring
LAIS_AUTO_MONITOR=true
LAIS_POLL_INTERVAL=10.0

# Cross-terminal
LAIS_SHARED_SESSION_PATH=/shared/sessions.json

# Agent identity
LAIS_AGENT_ID=opencode
```

### YAML Configuration

```yaml
agents:
  - id: coder
    name: Coder
    capabilities: [code, shell]
    max_retries: 3

tools:
  terminal:
    name: terminal
    type: function

policies:
  safe_execution:
    rules:
      - action: allow
        pattern: ".*"
```

## Security Considerations

- Local-only by default (no cloud dependency)
- No authentication (suitable for development)
- Input validation on all endpoints
- Rate limiting recommended for production

## Performance

- FileWatcher preferred over polling (instant vs 5-10s delay)
- Async agents for concurrent execution
- Checkpoint/resume for long-running tasks
- Dead letter queue for failure recovery

## Extensibility

### Custom Agent Handler

```python
from agent_sync import A2AServer

server = A2AServer()

def my_handler(context):
    # Your agent logic
    return {"result": "done"}

server.protocol.register_local_agent(
    "my_agent",
    "My Agent",
    ["custom_capability"]
)
server.protocol.local_agent_handlers["my_agent"] = my_handler
```

### Custom Trigger Callback

```python
from agent_sync import TriggerManager

triggers = TriggerManager()

def on_remote_change(source, data):
    print(f"Change from {source}: {data}")

triggers.register_type_callback("remote_change", on_remote_change)
```

## Related Documentation

- [Getting Started](getting-started.html)
- [API Reference](api-reference.html)
- [Examples](examples.html)