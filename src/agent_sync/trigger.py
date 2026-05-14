"""
Trigger - Event-driven trigger system with typed callbacks.
"""

import threading
from datetime import datetime
from typing import Callable, Dict, List, Any


class TriggerManager:
    """
    Event-driven trigger system for agent coordination.
    Supports general callbacks and typed event callbacks.
    """

    def __init__(self):
        self._callbacks: List[Callable] = []
        self._type_callbacks: Dict[str, List[Callable]] = {}
        self._event_history: List[dict] = []
        self._lock = threading.Lock()

    def register_callback(self, callback: Callable) -> None:
        """Register a general callback for all events."""
        with self._lock:
            self._callbacks.append(callback)

    def register_type_callback(self, event_type: str, callback: Callable) -> None:
        """Register a callback for a specific event type."""
        with self._lock:
            if event_type not in self._type_callbacks:
                self._type_callbacks[event_type] = []
            self._type_callbacks[event_type].append(callback)

    def unregister_callback(self, callback: Callable) -> bool:
        """Remove a callback. Returns True if found."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                return True
            for event_type in self._type_callbacks:
                if callback in self._type_callbacks[event_type]:
                    self._type_callbacks[event_type].remove(callback)
                    return True
        return False

    def trigger(self, source: str, data: dict) -> None:
        """Fire trigger to all matching callbacks."""
        event_type = data.get("type", "")

        with self._lock:
            all_callbacks = list(self._callbacks)
            type_callbacks = list(self._type_callbacks.get(event_type, []))
            type_callbacks.extend(self._type_callbacks.get("*", []))

        # Log event
        event = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "event_type": event_type,
            "data": data
        }
        self._event_history.append(event)
        if len(self._event_history) > 100:
            self._event_history = self._event_history[-100:]

        # Fire general callbacks
        for callback in all_callbacks:
            try:
                callback(source, data)
            except Exception as e:
                print(f"[TriggerManager] Callback error: {e}")

        # Fire type-specific callbacks
        for callback in type_callbacks:
            try:
                callback(source, data)
            except Exception as e:
                print(f"[TriggerManager] Type callback error: {e}")

    def trigger_user(self, task: str, target_agent: str) -> None:
        """Trigger user-initiated event."""
        self.trigger("user", {
            "type": "user_task",
            "task": task,
            "target": target_agent,
            "timestamp": datetime.now().isoformat()
        })

    def trigger_agent(self, from_agent: str, to_agent: str,
                      request: str, urgency: str = "medium") -> None:
        """Trigger agent-to-agent help request."""
        self.trigger("agent", {
            "type": "help_request",
            "from": from_agent,
            "to": to_agent,
            "request": request,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat()
        })

    def trigger_system(self, agent_id: str, reason: str) -> None:
        """Trigger system anomaly detection."""
        self.trigger("system", {
            "type": "anomaly_detected",
            "agent": agent_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

    def trigger_remote_change(self, agent_id: str = None) -> None:
        """Trigger remote file change event."""
        self.trigger("system", {
            "type": "remote_change",
            "agent": agent_id,
            "source": "cross_terminal",
            "timestamp": datetime.now().isoformat()
        })

    def get_event_history(self, limit: int = 20) -> List[dict]:
        """Get recent trigger events."""
        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()