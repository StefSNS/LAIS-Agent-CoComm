#!/usr/bin/env python3
"""
Quick test to verify LAIS-agent-CoComm installation.
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from agent_sync import (
            ActiveSessionLog, SharedMemory, A2AServer,
            TriggerManager, start_a2a_server, FileWatcher
        )
        print("  [OK] All modules imported")
        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False

def test_session_log():
    """Test ActiveSessionLog."""
    print("Testing ActiveSessionLog...")
    try:
        from agent_sync import ActiveSessionLog
        log = ActiveSessionLog()
        session = log.create_session("test task", "tester")
        assert session is not None
        print(f"  [OK] Created session: {session['session_id'][:20]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_shared_memory():
    """Test SharedMemory."""
    print("Testing SharedMemory...")
    try:
        from agent_sync import SharedMemory
        memory = SharedMemory()
        result = memory.store("test", "key1", "value1", priority="low")
        assert result is True
        retrieved = memory.retrieve("test", key="key1")
        assert len(retrieved) > 0
        print(f"  [OK] Stored and retrieved entry")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_a2a_server():
    """Test A2A server can be started."""
    print("Testing A2A server...")
    try:
        from agent_sync import A2AServer
        server = A2AServer()
        assert server is not None
        print(f"  [OK] Server instantiated (port {server.port})")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_trigger_manager():
    """Test TriggerManager."""
    print("Testing TriggerManager...")
    try:
        from agent_sync import TriggerManager
        tm = TriggerManager()
        triggered = []

        def callback(source, data):
            triggered.append(data)

        tm.register_callback(callback)
        tm.trigger("test", {"type": "test", "data": "hello"})
        assert len(triggered) == 1
        print("  [OK] Trigger callbacks working")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def main():
    print("=" * 50)
    print("LAIS-agent-CoComm Installation Test")
    print("=" * 50)
    print()

    results = []
    results.append(test_imports())
    results.append(test_session_log())
    results.append(test_shared_memory())
    results.append(test_a2a_server())
    results.append(test_trigger_manager())

    print()
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)

    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())