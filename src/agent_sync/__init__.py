"""
LAIS-agent-CoComm - Agent-to-Agent Communication & Coordination
A lightweight, standalone multi-agent coordination framework.
"""

__version__ = "0.1.0"
__author__ = "Stefa"

from .session_log import ActiveSessionLog, FileWatcher
from .memory_sync import SharedMemory, load_shared_memory
from .a2a_server import A2AServer, start_a2a_server
from .trigger import TriggerManager

__all__ = [
    "ActiveSessionLog",
    "SharedMemory",
    "load_shared_memory",
    "A2AServer",
    "start_a2a_server",
    "TriggerManager",
    "FileWatcher",
]