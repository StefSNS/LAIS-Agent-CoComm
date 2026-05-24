"""
Config - Agent Configuration and Policy Management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


@dataclass
class ToolConfig:
    name: str
    command: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class PolicyConfig:
    name: str
    rules: List[str] = field(default_factory=list)
    priority: str = "medium"


@dataclass
class AgentConfig:
    agent_id: str
    name: str
    capabilities: List[str]
    tools: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)
    budget_usd: float = 1.0
    memory_tier: str = "warm"


class AgentConfigLoader:
    """Load and manage agent configurations."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._default_path()
        self._agents = {}
        self._load()

    def _default_path(self) -> Path:
        return Path(__file__).parent.parent / "config" / "agents.json"

    def _load(self):
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                self._agents = {a["agent_id"]: AgentConfig(**a) for a in data.get("agents", [])}
            except Exception:
                self._agents = self._default_agents()
        else:
            self._agents = self._default_agents()

    def _default_agents(self) -> Dict[str, AgentConfig]:
        return {
            "lais": AgentConfig("lais", "LAIS", ["orchestration", "gui", "chat"]),
            "jarvis": AgentConfig("jarvis", "JARVIS", ["voice", "text", "search"]),
            "opencode": AgentConfig("opencode", "OpenCode", ["code", "shell", "git"]),
            "claude": AgentConfig("claude", "Claude", ["code", "reasoning", "analysis"])
        }

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentConfig]:
        return list(self._agents.values())

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"agents": [vars(a) for a in self._agents.values()]}
        self.config_path.write_text(json.dumps(data, indent=2))