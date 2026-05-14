"""
Trust/Escrow System (from MoltGrid pattern)
Agent-to-agent accountability with reputation and escrow for paid coordination.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TransactionStatus(Enum):
    PENDING = "pending"
    ESCROWED = "escrowed"
    RELEASED = "released"
    DISPUTED = "disputed"
    REFUNDED = "refunded"


class ReputationLevel(Enum):
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    TRUSTED = 4


@dataclass
class AgentReputation:
    """Reputation score for an agent."""
    agent_id: str
    score: float = 50.0  # 0-100
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_escrow: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def adjust_score(self, delta: float):
        """Adjust reputation score."""
        self.score = max(0, min(100, self.score + delta))
        self.last_updated = datetime.now().isoformat()

    def get_level(self) -> ReputationLevel:
        """Get reputation level."""
        if self.score >= 90:
            return ReputationLevel.TRUSTED
        elif self.score >= 70:
            return ReputationLevel.HIGH
        elif self.score >= 50:
            return ReputationLevel.MEDIUM
        elif self.score >= 30:
            return ReputationLevel.LOW
        return ReputationLevel.UNKNOWN


@dataclass
class EscrowTransaction:
    """A financial escrow between agents."""
    transaction_id: str
    from_agent: str
    to_agent: str
    amount: float
    task_id: str
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    released_at: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


class TrustManager:
    """Manages agent reputation and escrow."""

    def __init__(self):
        self.reputations: Dict[str, AgentReputation] = {}
        self.escrow_transactions: Dict[str, EscrowTransaction] = {}
        self.transaction_history: List[Dict] = []

    def get_reputation(self, agent_id: str) -> AgentReputation:
        """Get or create reputation for an agent."""
        if agent_id not in self.reputations:
            self.reputations[agent_id] = AgentReputation(agent_id)
        return self.reputations[agent_id]

    def adjust_reputation(self, agent_id: str, delta: float, reason: str):
        """Adjust an agent's reputation score."""
        rep = self.get_reputation(agent_id)
        rep.adjust_score(delta)

        self.transaction_history.append({
            "type": "reputation_adjustment",
            "agent_id": agent_id,
            "delta": delta,
            "new_score": rep.score,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

    def task_completed(self, agent_id: str, success: bool, value: float = 0):
        """Record task completion and adjust reputation."""
        rep = self.get_reputation(agent_id)

        if success:
            rep.completed_tasks += 1
            # Positive adjustment based on value
            delta = min(5.0, 1.0 + value * 0.01)
            self.adjust_reputation(agent_id, delta, "task_completed")
        else:
            rep.failed_tasks += 1
            # Negative adjustment
            delta = -min(10.0, 2.0 + value * 0.01)
            self.adjust_reputation(agent_id, delta, "task_failed")

    def create_escrow(
        self,
        from_agent: str,
        to_agent: str,
        amount: float,
        task_id: str,
        release_conditions: Dict[str, Any] = None
    ) -> str:
        """Create an escrow transaction."""
        transaction_id = f"escrow_{len(self.escrow_transactions)}_{datetime.now().strftime('%s')}"

        tx = EscrowTransaction(
            transaction_id=transaction_id,
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount,
            task_id=task_id,
            status=TransactionStatus.ESCROWED,
            conditions=release_conditions or {}
        )

        self.escrow_transactions[transaction_id] = tx

        # Update agent escrow totals
        self.get_reputation(to_agent).total_escrow += amount

        return transaction_id

    def release_escrow(self, transaction_id: str, success: bool, reason: str = "") -> bool:
        """Release or refund escrow based on task outcome."""
        tx = self.escrow_transactions.get(transaction_id)
        if not tx or tx.status != TransactionStatus.ESCROWED:
            return False

        if success:
            tx.status = TransactionStatus.RELEASED
            tx.released_at = datetime.now().isoformat()
            # Reputation boost for successful completion
            self.task_completed(tx.to_agent, True, tx.amount)
        else:
            tx.status = TransactionStatus.REFUNDED
            tx.released_at = datetime.now().isoformat()
            # Reputation penalty for failure
            self.task_completed(tx.to_agent, False, tx.amount)

        self.transaction_history.append({
            "type": "escrow_release",
            "transaction_id": transaction_id,
            "status": tx.status.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def get_trust_score(self, agent_id: str) -> Dict[str, Any]:
        """Get full trust information for an agent."""
        rep = self.get_reputation(agent_id)
        return {
            "agent_id": agent_id,
            "score": rep.score,
            "level": rep.get_level().name,
            "completed_tasks": rep.completed_tasks,
            "failed_tasks": rep.failed_tasks,
            "success_rate": rep.completed_tasks / (rep.completed_tasks + rep.failed_tasks)
                if (rep.completed_tasks + rep.failed_tasks) > 0 else 0,
            "total_escrow": rep.total_escrow,
            "last_updated": rep.last_updated
        }

    def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary of all agents."""
        return {
            "total_agents": len(self.reputations),
            "avg_reputation": sum(r.score for r in self.reputations.values()) / len(self.reputations)
                if self.reputations else 0,
            "trusted_agents": sum(
                1 for r in self.reputations.values()
                if r.get_level() == ReputationLevel.TRUSTED
            ),
            "active_escrows": sum(
                1 for tx in self.escrow_transactions.values()
                if tx.status == TransactionStatus.ESCROWED
            )
        }

    def to_dict(self) -> dict:
        return {
            "trust_summary": self.get_agent_summary(),
            "reputations": {
                aid: {
                    "score": rep.score,
                    "level": rep.get_level().name,
                    "completed": rep.completed_tasks,
                    "failed": rep.failed_tasks
                }
                for aid, rep in self.reputations.items()
            }
        }


# Convenience functions
def create_trust_system() -> TrustManager:
    """Create a new trust manager."""
    return TrustManager()


def check_agent_trust(manager: TrustManager, agent_id: str, min_level: ReputationLevel = ReputationLevel.LOW) -> bool:
    """Check if an agent meets minimum trust requirements."""
    rep = manager.get_reputation(agent_id)
    return rep.get_level().value >= min_level.value