"""
LAIS-agent-CoComm - Agent-to-Agent Communication & Coordination
A lightweight, standalone multi-agent coordination framework.
"""

__version__ = "0.2.0"
__author__ = "Stefa"

from .session_log import ActiveSessionLog, FileWatcher
from .memory_sync import SharedMemory, load_shared_memory
from .a2a_server import A2AServer, start_a2a_server
from .trigger import TriggerManager
from .config import AgentConfigLoader, AgentConfig, ToolConfig, PolicyConfig
from .roles import AgentRole, RoleRegistry, AgentWithRole, get_role_registry
from .handoff import HandoffAgent, HandoffChain, HandoffRules, auto_handoff

__all__ = [
    # Core
    "ActiveSessionLog",
    "SharedMemory",
    "load_shared_memory",
    "A2AServer",
    "start_a2a_server",
    "TriggerManager",
    "FileWatcher",
    # Config
    "AgentConfigLoader",
    "AgentConfig",
    "ToolConfig",
    "PolicyConfig",
    # Roles
    "AgentRole",
    "RoleRegistry",
    "AgentWithRole",
    "get_role_registry",
    # Handoff
    "HandoffAgent",
    "HandoffChain",
    "HandoffRules",
    "auto_handoff",
]