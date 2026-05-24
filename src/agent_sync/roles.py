"""
Roles - Agent Role System and Registry
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    EXECUTOR = "executor"
    OBSERVER = "observer"
    SPECIALIST = "specialist"


@dataclass
class RoleRegistry:
    roles: Dict[AgentRole, List[str]] = field(default_factory=dict)

    def register(self, role: AgentRole, agent_ids: List[str]):
        self.roles[role] = agent_ids

    def get_agents_by_role(self, role: AgentRole) -> List[str]:
        return self.roles.get(role, [])


class AgentWithRole:
    def __init__(self, agent_id: str, role: AgentRole, registry: RoleRegistry):
        self.agent_id = agent_id
        self.role = role
        self.registry = registry

    def can_delegate_to(self, target_role: AgentRole) -> bool:
        return target_role in [
            AgentRole.EXECUTOR,
            AgentRole.SPECIALIST,
            AgentRole.OBSERVER
        ]


_registry = RoleRegistry()


def get_role_registry() -> RoleRegistry:
    return _registry