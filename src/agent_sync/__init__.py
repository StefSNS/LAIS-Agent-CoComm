"""
LAIS-agent-CoComm - Agent-to-Agent Communication & Coordination
A lightweight, standalone multi-agent coordination framework.
"""

__version__ = "0.3.0"
__author__ = "Stefa"

from .session_log import ActiveSessionLog, FileWatcher
from .memory_sync import SharedMemory, load_shared_memory
from .a2a_server import A2AServer, start_a2a_server
from .trigger import TriggerManager
from .config import AgentConfigLoader, AgentConfig, ToolConfig, PolicyConfig
from .roles import AgentRole, RoleRegistry, AgentWithRole, get_role_registry
from .handoff import HandoffAgent, HandoffChain, HandoffRules, auto_handoff
from .async_agent import AsyncAgent, AsyncAgentPool, AgentState
from .goal_planner import TaskDAG, GoalDecomposer, create_goal_dag
from .consensus import ConsensusEngine, ConsensusRoom, VoteStrategy, resolve_conflict
from .graph_evolution import EvolvingGraph, GraphEvolutionEngine, NodeStatus
from .trust import TrustManager, AgentReputation, create_trust_system, check_agent_trust

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
    # Async
    "AsyncAgent",
    "AsyncAgentPool",
    "AgentState",
    # Goal Planning
    "TaskDAG",
    "GoalDecomposer",
    "create_goal_dag",
    # Consensus
    "ConsensusEngine",
    "ConsensusRoom",
    "VoteStrategy",
    "resolve_conflict",
    # Graph Evolution
    "EvolvingGraph",
    "GraphEvolutionEngine",
    "NodeStatus",
    # Trust
    "TrustManager",
    "AgentReputation",
    "create_trust_system",
    "check_agent_trust",
]