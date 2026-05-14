"""
Example usage of LAIS-agent-CoComm
"""

from agent_sync import (
    ActiveSessionLog, SharedMemory, A2AServer,
    TriggerManager, start_a2a_server
)


def example_session_log():
    """Session and task coordination example."""
    print("=== ActiveSessionLog Example ===")

    # Create session log
    log = ActiveSessionLog(
        json_path="data/sessions/active.json",
        shared_path="data/sessions/shared.json"
    )

    # Create a new session with task
    session = log.create_session(
        task_description="Review code for bugs",
        created_by="claude",
        capabilities_needed=["code", "reasoning"]
    )
    print(f"Created session: {session['session_id']}")

    # Register callback for remote changes
    def on_remote_change(source, data):
        print(f"[Callback] Remote change detected: {data}")

    log.trigger_manager.register_type_callback("remote_change", on_remote_change)


def example_shared_memory():
    """Cross-agent shared memory example."""
    print("\n=== SharedMemory Example ===")

    memory = SharedMemory()

    # Store with priority
    memory.store("agent_a", "project_status", "Active development", priority="high")
    memory.store("agent_b", "task_queue", "3 tasks pending", priority="medium")
    memory.store("agent_a", "coding_note", "Use pattern X for Y", priority="low")

    # Retrieve
    results = memory.retrieve("agent_b", category="general")
    print(f"Retrieved {len(results)} entries")

    # Search across agents
    found = memory.cross_agent_search("development")
    print(f"Search 'development': {len(found)} results")

    # Get status
    status = memory.get_sync_status()
    print(f"Status: {status['total_entries']} entries, {status['agents']} agents")


def example_a2a_server():
    """A2A server example."""
    print("\n=== A2A Server Example ===")

    # Start server
    server = start_a2a_server(port=8020)
    print(f"Server running at {server.url}")

    # Register a new agent
    server.protocol.register_agent(
        "custom_agent",
        "Custom Agent",
        ["code", "search", "analyze"]
    )
    print("Registered custom_agent")

    # List agents
    agents = server.protocol.list_agents()
    print(f"Agents: {[a['agent_id'] for a in agents]}")

    # Submit task (in real usage, another agent would call this via HTTP)
    task = server.protocol.delegate_task(
        from_agent="claude",
        to_agent="custom_agent",
        task_type="code",
        payload={"description": "Fix bug in module X"},
        priority="high"
    )
    print(f"Task submitted: {task.task_id}")


def example_trigger_manager():
    """Trigger manager example."""
    print("\n=== TriggerManager Example ===")

    triggers = TriggerManager()

    # Register typed callbacks
    def handle_incoming_task(source, data):
        print(f"[Handler] Incoming task from {source}: {data.get('task')}")

    def handle_remote_change(source, data):
        print(f"[Handler] Remote change detected")

    triggers.register_type_callback("incoming_task", handle_incoming_task)
    triggers.register_type_callback("remote_change", handle_remote_change)

    # Fire events
    triggers.trigger("claude", {"type": "incoming_task", "task": "Fix bug"})
    triggers.trigger_agent("claude", "opencode", "Help with refactor", urgency="high")
    triggers.trigger_system("opencode", "Task timeout detected")


if __name__ == "__main__":
    print("LAIS-agent-CoComm Examples\n")

    example_session_log()
    example_shared_memory()
    example_a2a_server()
    example_trigger_manager()

    print("\n=== All examples completed ===")