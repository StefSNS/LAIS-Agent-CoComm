"""
Handoff - Agent-to-Agent Task Handoff System
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HandoffRules:
    auto_handoff: bool = True
    priority_threshold: str = "high"
    capability_match_required: bool = True


@dataclass
class HandoffAgent:
    agent_id: str
    capabilities: List[str]
    current_load: float = 0.0
    available: bool = True


class HandoffChain:
    def __init__(self):
        self.chain: List[str] = []

    def add(self, agent_id: str):
        self.chain.append(agent_id)

    def get_chain(self) -> List[str]:
        return self.chain.copy()


def auto_handoff(agents: List[HandoffAgent], task: Dict[str, Any]) -> Optional[str]:
    """Automatically select best agent for task."""
    required_caps = task.get("required_capabilities", [])

    candidates = [a for a in agents if a.available and a.current_load < 0.8]

    if required_caps:
        for agent in candidates:
            if all(cap in agent.capabilities for cap in required_caps):
                return agent.agent_id

    if candidates:
        return min(candidates, key=lambda a: a.current_load).agent_id

    return None