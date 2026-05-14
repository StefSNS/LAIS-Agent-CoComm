---
layout: page
title: API Reference
nav_order: 3
---

# API Reference

## Core Modules

### ActiveSessionLog

Session and task coordination with auto-monitoring.

```python
from agent_sync import ActiveSessionLog

log = ActiveSessionLog(
    json_path="data/sessions.json",
    shared_path="/shared/sessions.json"
)

# Create session
session = log.create_session(
    task_description="Build feature X",
    created_by="claude",
    capabilities_needed=["code", "reasoning"]
)

# Get current session
current = log.get_session()

# Update task status
log.update_task_status(task_id, "completed", result="OK")

# Start/stop monitoring
log.enable_full_monitoring(poll_interval=10.0)
log.disable_monitoring()
```

### SharedMemory

Cross-agent memory with priority and access tracking.

```python
from agent_sync import SharedMemory

memory = SharedMemory()

# Store with priority
memory.store("agent_a", "project_status", "Active", priority="high")

# Retrieve
results = memory.retrieve("agent_b", category="project")

# Cross-agent search
found = memory.cross_agent_search("development")

# Get status
status = memory.get_sync_status()
```

### A2AServer

HTTP server for agent-to-agent communication.

```python
from agent_sync import A2AServer, start_a2a_server

# Start server
server = start_a2a_server(port=8020)

# Register agent
server.protocol.register_agent(
    "my_agent",
    "My Agent",
    ["code", "search"]
)

# List agents
agents = server.protocol.list_agents()

# Get status
status = server.protocol.get_status()
```

## Coordination Modules

### AsyncAgent

Durable async agents with checkpoint/resume.

```python
from agent_sync import AsyncAgent, AsyncAgentPool

async def my_handler(context):
    result = await do_work(context)
    return result

# Single agent
agent = AsyncAgent("worker", my_handler, timeout=300)
result = await agent.run("task_1", "Process data")

# Agent pool
pool = AsyncAgentPool(max_agents=5)
result = await pool.submit("worker", my_handler, "task_2", "Process more")
```

### TaskDAG

Goal decomposition into parallelizable task graphs.

```python
from agent_sync import TaskDAG, GoalDecomposer, create_goal_dag

# Quick create from goal string
dag = create_goal_dag("Build a REST API with tests")

# Manual creation
dag = TaskDAG("my_dag", "Complex project")
dag.add_node(TaskNode("task_1", "Design", "planner"))
dag.add_node(TaskNode("task_2", "Implement", "coder", dependencies={"task_1"}))

# Get parallel execution groups
groups = dag.get_parallel_groups()

# Estimate duration
estimated = dag.estimate_duration()
```

### ConsensusEngine

Multi-agent voting and negotiation.

```python
from agent_sync import ConsensusEngine, VoteStrategy

engine = ConsensusEngine()

# Create room
room = engine.create_room(
    "design_choice",
    "Choose implementation approach",
    {"coder": 1.0, "reviewer": 1.0},
    VoteStrategy.MAJORITY
)

# Submit proposals
room.submit_proposal("coder", "use_fastapi", "Fast development", 0.8)
room.submit_proposal("reviewer", "use_flask", "Simpler", 0.7)

# Vote
room.vote("coder", "proposal_0")
room.vote("reviewer", "proposal_0")  # Unanimous!

# Resolve
result = room.resolve()
```

### EvolvingGraph

Self-healing task graphs.

```python
from agent_sync import EvolvingGraph, GraphEvolutionEngine

engine = GraphEvolutionEngine()
graph = engine.create_graph("build_project")

# Add tasks
graph.add_node("design", "Create API design")
graph.add_node("implement", "Write code", max_attempts=3)
graph.add_node("test", "Run tests")

# Add dependencies
graph.add_edge("design", "implement")
graph.add_edge("implement", "test")

# Register recovery handler
graph.register_recovery_handler("timeout", lambda e, t: f"retry {t}")

# Mark failure and auto-heal
if graph.mark_node_failed("implement", "timeout error"):
    print("Retrying...")
else:
    report = engine.auto_heal("build_project")
    print(f"Alternatives: {report}")
```

### TrustManager

Agent reputation and escrow.

```python
from agent_sync import TrustManager, create_trust_system

trust = create_trust_system()

# Record task completion
trust.task_completed("opencode", success=True, value=10.0)

# Create escrow
escrow_id = trust.create_escrow(
    "client",
    "opencode",
    amount=100.0,
    task_id="task_123",
    release_conditions={"success": True}
)

# Release escrow
trust.release_escrow(escrow_id, success=True, reason="Task completed")

# Check trust score
score = trust.get_trust_score("opencode")
print(f"Score: {score['score']}, Level: {score['level']}")
```

## Helper Modules

### AgentRole

Role-based agent definitions.

```python
from agent_sync import AgentRole, RoleRegistry, get_role_registry

# Create custom role
coder = AgentRole(
    role="coder",
    goal="Write clean code",
    backstory="Senior developer",
    capabilities=["code", "shell"],
    tools=["editor", "terminal"]
)

# Register
registry = get_role_registry()
registry.register(coder)

# Get role
role = registry.get("coder")
```

### HandoffAgent

Explicit agent routing.

```python
from agent_sync import HandoffAgent, HandoffChain, HandoffRules

# Explicit handoff
handoff = HandoffAgent(
    agent="reviewer",
    reason="Code done, needs review",
    context={"files": ["main.py"]}
)

# Handoff chain
chain = HandoffChain()
chain.start_chain("task_1", "coder", [
    HandoffAgent("reviewer", "Review code"),
    HandoffAgent("tester", "Test")
])

# Auto-handoff based on rules
from agent_sync import auto_handoff
next_step = auto_handoff({"task_type": "code", "status": "completed"})
```

## CLI

```bash
# Start server
agent-sync start --port 8020

# Status
agent-sync status

# Delegate
agent-sync delegate --to opencode --task "Fix bug" --priority high

# List agents
agent-sync list

# Dead letter queue
agent-sync dlq
```

## Environment Configuration

```bash
# Enable auto-monitoring
export LAIS_AUTO_MONITOR=true

# Polling interval (seconds)
export LAIS_POLL_INTERVAL=10.0

# Cross-terminal shared path
export LAIS_SHARED_SESSION_PATH=/shared/sessions.json

# Agent identifier
export LAIS_AGENT_ID=opencode
```