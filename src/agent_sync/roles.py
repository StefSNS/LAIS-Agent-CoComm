"""
Agent Roles - Role-based agent definitions (from crewAI pattern)
Each agent has a role, goal, and backstory for structured coordination.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class AgentRole:
    """
    Defines an agent's role in a multi-agent system.

    Attributes:
        role: The agent's role (e.g., "coder", "reviewer", "tester")
        goal: What the agent aims to achieve
        backstory: The agent's history/experience for context
        capabilities: What the agent can do
        tools: Available tools for this role
    """
    role: str
    goal: str
    backstory: str = ""
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.7

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature
        }


class RoleRegistry:
    """Registry of available agent roles."""

    DEFAULT_ROLES = {
        "coder": AgentRole(
            role="coder",
            goal="Write clean, efficient code that solves the problem",
            backstory="Expert programmer with years of experience in multiple languages. "
                     "Focuses on best practices, patterns, and maintainability.",
            capabilities=["code", "shell", "git", "debug"],
            tools=["editor", "terminal", "git"]
        ),
        "reviewer": AgentRole(
            role="reviewer",
            goal="Ensure code quality and catch bugs before merge",
            backstory="Senior developer with eye for detail. Reviews code for "
                     "security, performance, and maintainability issues.",
            capabilities=["code", "analysis", "search"],
            tools=["code_analyzer", "linter"]
        ),
        "tester": AgentRole(
            role="tester",
            goal="Verify functionality and prevent regressions",
            backstory="QA specialist focused on comprehensive test coverage. "
                     "Creates unit, integration, and end-to-end tests.",
            capabilities=["code", "testing"],
            tools=["test_runner", "debugger"]
        ),
        "researcher": AgentRole(
            role="researcher",
            goal="Gather information and provide insights",
            backstory="Research analyst skilled at finding and synthesizing information. "
                     "Can access APIs, databases, and web resources.",
            capabilities=["search", "web", "analysis"],
            tools=["web_search", "api_client"]
        ),
        "planner": AgentRole(
            role="planner",
            goal="Break down complex tasks into actionable steps",
            backstory="Technical lead experienced in architecture and project management. "
                     "Specializes in task decomposition and resource allocation.",
            capabilities=["planning", "analysis", "coordination"],
            tools=["task_manager"]
        )
    }

    def __init__(self):
        self._roles: Dict[str, AgentRole] = dict(self.DEFAULT_ROLES)

    def register(self, role: AgentRole):
        """Register a new role or update existing."""
        self._roles[role.role] = role

    def get(self, role_name: str) -> Optional[AgentRole]:
        """Get a role by name."""
        return self._roles.get(role_name)

    def list_roles(self) -> List[str]:
        """List all available role names."""
        return list(self._roles.keys())

    def roles_with_capability(self, capability: str) -> List[AgentRole]:
        """Find roles that have a specific capability."""
        return [r for r in self._roles.values() if capability in r.capabilities]


class AgentWithRole:
    """An agent instance bound to a specific role."""

    def __init__(self, agent_id: str, role: AgentRole):
        self.agent_id = agent_id
        self.role = role
        self.current_task: Optional[str] = None
        self.task_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()

    def assign_task(self, task_id: str, description: str):
        """Assign a task to this agent."""
        self.current_task = task_id
        self.task_history.append({
            "task_id": task_id,
            "description": description,
            "assigned_at": datetime.now().isoformat(),
            "status": "in_progress"
        })

    def complete_task(self, result: Dict[str, Any]):
        """Mark the current task as complete."""
        if self.task_history:
            self.task_history[-1]["status"] = "completed"
            self.task_history[-1]["result"] = result
            self.task_history[-1]["completed_at"] = datetime.now().isoformat()
        self.current_task = None

    def fail_task(self, error: str):
        """Mark the current task as failed."""
        if self.task_history:
            self.task_history[-1]["status"] = "failed"
            self.task_history[-1]["error"] = error
            self.task_history[-1]["failed_at"] = datetime.now().isoformat()
        self.current_task = None

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role.to_dict(),
            "current_task": self.current_task,
            "task_count": len(self.task_history),
            "created_at": self.created_at
        }


# Global registry instance
_role_registry = RoleRegistry()


def get_role_registry() -> RoleRegistry:
    """Get the global role registry."""
    return _role_registry