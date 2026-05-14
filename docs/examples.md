---
layout: page
title: Examples
nav_order: 4
---

# Examples

## Multi-Agent Coordination

### Basic Task Delegation

```python
from agent_sync import A2AServer, start_a2a_server

# Start server
server = start_a2a_server()

# Agent A delegates task to Agent B
task = server.protocol.delegate_task(
    from_agent="planner",
    to_agent="coder",
    task_type="code",
    payload={"description": "Create user authentication"},
    priority="high"
)

print(f"Task {task.task_id} delegated to coder")
```

### Cross-Agent Memory Sharing

```python
from agent_sync import SharedMemory

memory = SharedMemory()

# Agent A stores information
memory.store("planner", "project_plan", """
    1. User authentication (3 days)
    2. Dashboard (2 days)
    3. API endpoints (2 days)
""", priority="high")

# Agent B reads the plan
plan = memory.retrieve("coder", key="project_plan")
for entry in plan:
    print(f"{entry['agent']}: {entry['value'][:50]}...")
```

### Session Coordination

```python
from agent_sync import ActiveSessionLog

log = ActiveSessionLog(shared_path="/shared/sessions.json")

# Create collaborative session
session = log.create_session(
    task_description="Build REST API",
    created_by="planner",
    capabilities_needed=["code", "test", "review"]
)

# Monitor for remote changes
def on_remote_change(source, data):
    print(f"Remote update from {source}: {data}")

log.trigger_manager.register_type_callback("remote_change", on_remote_change)

# Start monitoring (auto-enabled by default)
log.enable_full_monitoring()
```

## Async Agent Pool

### Concurrent Task Processing

```python
import asyncio
from agent_sync import AsyncAgent, AsyncAgentPool

async def code_handler(context):
    task = context.get("task", "default")
    # Simulate work
    await asyncio.sleep(1)
    return {"status": "completed", "result": f"Processed {task}"}

async def main():
    pool = AsyncAgentPool(max_agents=3)

    # Submit multiple tasks
    tasks = [
        pool.submit("coder", code_handler, f"task_{i}", f"Process item {i}")
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)

asyncio.run(main())
```

### Checkpoint and Resume

```python
from agent_sync import AsyncAgent

async def long_task(context):
    steps = ["analyze", "implement", "test", "deploy"]
    results = []

    for i, step in enumerate(steps):
        print(f"Executing step {i}: {step}")
        await asyncio.sleep(1)
        results.append({"step": step, "done": True})

        # Checkpoint every 2 steps
        if (i + 1) % 2 == 0:
            print(f"Checkpoint after step {i}")

    return {"completed": True, "steps": results}

agent = AsyncAgent("builder", long_task, checkpoint_interval=2)
result = await agent.run("build_1", "Build system")
print(f"Final result: {result}")
```

## Goal Decomposition

### Automatic Task Planning

```python
from agent_sync import GoalDecomposer

decomposer = GoalDecomposer()

# Decompose a goal into parallelizable tasks
dag = decomposer.decompose_with_llm_style(
    "Build and deploy a web application with CI/CD"
)

print(f"Goal: {dag.goal_description}")
print(f"Parallel groups: {dag.get_parallel_groups()}")

# Execute groups
for group in dag.get_parallel_groups():
    print(f"Running in parallel: {[n.id for n in group]}")
```

### Custom DAG

```python
from agent_sync import TaskDAG, TaskNode

dag = TaskDAG("api_project", "Build REST API")

# Add nodes with dependencies
dag.add_node(TaskNode("1", "Database design", "planner"))
dag.add_node(TaskNode("2", "API endpoints", "coder", dependencies={"1"}))
dag.add_node(TaskNode("3", "Authentication", "coder", dependencies={"1"}))
dag.add_node(TaskNode("4", "Tests", "tester", dependencies={"2", "3"}))
dag.add_node(TaskNode("5", "Documentation", "reviewer", dependencies={"4"}))

# Add edges
dag.add_edge("1", "2")
dag.add_edge("1", "3")
dag.add_edge("2", "4")
dag.add_edge("3", "4")
dag.add_edge("4", "5")

# Get execution plan
groups = dag.get_parallel_groups()
print(f"Execution plan: {len(groups)} stages")
for i, group in enumerate(groups):
    print(f"Stage {i}: {[n.description for n in group]}")
```

## Consensus

### Team Decision Making

```python
from agent_sync import ConsensusEngine, VoteStrategy

engine = ConsensusEngine()

# Create consensus room
room = engine.create_room(
    "tech_choice",
    "Choose backend framework",
    {"lead": 1.5, "senior_dev": 1.0, "junior_dev": 1.0},
    VoteStrategy.WEIGHTED
)

# Submit proposals
room.submit_proposal("lead", "FastAPI", "Modern, fast, async", 0.9)
room.submit_proposal("senior_dev", "Django", "Batteries included", 0.8)
room.submit_proposal("junior_dev", "Flask", "Simple, minimal", 0.7)

# Vote (weighted by trust)
room.vote("lead", "proposal_0")
room.vote("senior_dev", "proposal_0")  # Lead's proposal
room.vote("junior_dev", "proposal_0")  # Following lead

# Resolve
result = room.resolve()
print(f"Decision: {result}")

# Quick conflict resolution
from agent_sync import resolve_conflict
winner = resolve_conflict(
    ["agent_a", "agent_b"],
    ["use_approach_1", "use_approach_2"],
    VoteStrategy.MAJORITY
)
print(f"Quick resolution: {winner}")
```

## Self-Healing

### Automatic Recovery

```python
from agent_sync import GraphEvolutionEngine

engine = GraphEvolutionEngine()
graph = engine.create_graph("data_pipeline")

# Build pipeline
graph.add_node("fetch", "Fetch data from API")
graph.add_node("transform", "Transform data")
graph.add_node("load", "Load to database")
graph.add_node("notify", "Send notification")

graph.add_edge("fetch", "transform")
graph.add_edge("transform", "load")
graph.add_edge("load", "notify")

# Register recovery handler
def recover_timeout(error, task):
    return f"retry_with_timeout:{task}"

graph.register_recovery_handler("timeout", recover_timeout)

# Simulate failure
graph.nodes["transform"].status = "completed"
graph.nodes["load"].status = "running"

# Mark failure and auto-heal
if graph.mark_node_failed("load", "timeout connecting to DB"):
    print("Retrying load task...")
else:
    report = engine.auto_heal("data_pipeline")
    print(f"Self-healing report: {report}")
```

## Trust System

### Agent Accountability

```python
from agent_sync import TrustManager, check_agent_trust, ReputationLevel

trust = TrustManager()

# Track agent performance
trust.task_completed("opencode", success=True, value=50.0)
trust.task_completed("jarvis", success=True, value=30.0)
trust.task_completed("lais", success=True, value=40.0)

# Check trust before delegation
if check_agent_trust(trust, "opencode", ReputationLevel.MEDIUM):
    print("opencode meets trust requirements")
else:
    print("opencode needs more reputation")

# Create escrow for important task
escrow_id = trust.create_escrow(
    from_agent="client",
    to_agent="opencode",
    amount=100.0,
    task_id="critical_task",
    release_conditions={"min_score": 80}
)

# Release on success
trust.release_escrow(escrow_id, success=True)

# Get full trust report
summary = trust.get_agent_summary()
print(f"Total agents: {summary['total_agents']}")
print(f"Trusted: {summary['trusted_agents']}")
```

## Integration Patterns

### Combining Multiple Features

```python
from agent_sync import (
    A2AServer,
    SharedMemory,
    TaskDAG,
    ConsensusEngine,
    TrustManager
)

# Initialize all components
server = start_a2a_server()
memory = SharedMemory()
trust = TrustManager()

# Create goal-based task decomposition
dag = create_goal_dag("Build and deploy cloud application")

# For each task in DAG, check trust and delegate
for node in dag.nodes.values():
    trust_score = trust.get_trust_score(node.agent_type)

    if trust_score["level"] == "TRUSTED":
        # Trusted agent - delegate directly
        server.protocol.delegate_task(
            from_agent="planner",
            to_agent=node.agent_type,
            task_type="execute",
            payload={"task": node.description},
            priority=node.priority
        )
    else:
        # Create escrow for untrusted agents
        escrow_id = trust.create_escrow(
            "planner", node.agent_type, 50.0, node.id
        )
        # Delegate with escrow
        task = server.protocol.delegate_task(
            from_agent="planner",
            to_agent=node.agent_type,
            task_type="execute",
            payload={"task": node.description, "escrow": escrow_id},
            priority=node.priority
        )
```