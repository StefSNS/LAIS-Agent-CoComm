---
layout: page
title: Vault Integration
nav_order: 6
---

# Vault Integration

LAIS-agent-CoComm can integrate with an Obsidian vault for persistent cross-session context and knowledge management.

## Overview

The vault integration provides:
- **Context loading** — Restore session context on startup
- **Knowledge search** — Query vault notes for relevant information
- **Memory sync** — Write decisions and learnings back to vault

## Configuration

```python
from agent_sync import VaultIntegration

vault = VaultIntegration(
    vault_path="C:/Users/stefa/Desktop/AI projects/Obsidian/Unified Brain"
)

# Load session context
context = vault.load_context()

# Search vault
results = vault.search("python async patterns")

# Write memory
vault.write_note("30_Projects/session_notes.md", "# Session Notes\n- Task completed")
```

## Vault Structure

Recommended folder structure for agent coordination:

```
Unified Brain/
├── 00_Inbox/           # Unprocessed notes from agents
├── 30_Projects/        # Active project notes
│   └── shared/         # Cross-agent project state
├── 40_System/          # Agent registry, protocols
│   ├── agent_registry.md
│   └── Log - Agent Handoff Protocol.md
└── 50_Memory/          # Persistent learnings
    ├── crystallized.json
    └── Decision Log.md
```

## Context Files

### agent_registry.md

Tracks all registered agents and their capabilities:

```markdown
# Agent Registry

## Claude Code
- ID: claude
- Capabilities: code, reasoning, analysis, search, shell

## OpenCode
- ID: opencode
- Capabilities: code, shell, git, api
```

### crystallized.json

Cross-session learnings in JSON format:

```json
[
  {"key": "a2a_delegation", "value": "Use explicit handoff for clarity"},
  {"key": "memory_sync", "value": "High priority for task status updates"}
]
```

## Integration Example

```python
from agent_sync import ActiveSessionLog, SharedMemory
from vault_sync import VaultIntegration

class CoordinatedAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.vault = VaultIntegration()
        self.session = ActiveSessionLog()
        self.memory = SharedMemory()

    def on_startup(self):
        # Load vault context
        context = self.vault.load_context()
        self.memory.restore(context.get("memory", {}))

        # Start session monitoring
        self.session.start_monitoring()

    def on_task_complete(self, task_id: str, result: dict):
        # Update shared memory
        self.memory.store(self.agent_id, f"task_{task_id}", result)

        # Optionally write to vault
        self.vault.log_decision(f"Task {task_id} completed", result)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LAIS_VAULT_PATH` | Path to Obsidian vault |
| `LAIS_AGENT_ID` | Current agent identifier |

## See Also

- [Architecture](architecture.html)
- [API Reference](api-reference.html)