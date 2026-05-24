"""
Trust - Agent Trust and Reputation System
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class AgentReputation:
    agent_id: str
    trust_score: float = 0.5
    successful_tasks: int = 0
    failed_tasks: int = 0
    last_interaction: Optional[datetime] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


class TrustManager:
    """Track and manage agent trust scores."""

    def __init__(self):
        self.reputations: Dict[str, AgentReputation] = {}

    def record_interaction(self, agent_id: str, success: bool, task_type: str):
        if agent_id not in self.reputations:
            self.reputations[agent_id] = AgentReputation(agent_id=agent_id)

        rep = self.reputations[agent_id]
        rep.last_interaction = datetime.now()

        if success:
            rep.successful_tasks += 1
        else:
            rep.failed_tasks += 1

        total = rep.successful_tasks + rep.failed_tasks
        rep.trust_score = rep.successful_tasks / total if total > 0 else 0.5

        rep.history.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "task_type": task_type
        })

    def get_trust_score(self, agent_id: str) -> float:
        if agent_id not in self.reputations:
            return 0.5
        return self.reputations[agent_id].trust_score

    def is_trusted(self, agent_id: str, threshold: float = 0.7) -> bool:
        return self.get_trust_score(agent_id) >= threshold


def create_trust_system() -> TrustManager:
    return TrustManager()


def check_agent_trust(manager: TrustManager, agent_id: str) -> Dict[str, Any]:
    score = manager.get_trust_score(agent_id)
    return {
        "agent_id": agent_id,
        "trust_score": score,
        "trusted": manager.is_trusted(agent_id),
        "level": "high" if score > 0.8 else "medium" if score > 0.5 else "low"
    }