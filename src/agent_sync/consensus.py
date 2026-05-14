"""
Consensus Engine (from Mycelium pattern)
Structured negotiation when agents disagree - reaches single shared answer.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib


class VoteStrategy(Enum):
    MAJORITY = "majority"  # >50% wins
    WEIGHTED = "weighted"  # Based on agent trust scores
    UNANIMOUS = "unanimous"  # All must agree
    ROUND_ROBIN = "round_robin"  # Iterate until consensus


@dataclass
class Proposal:
    """A proposal from an agent."""
    id: str
    agent_id: str
    content: Any
    rationale: str = ""
    confidence: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsensusRound:
    """A round of consensus negotiation."""
    round_id: str
    proposals: List[Proposal] = field(default_factory=list)
    votes: Dict[str, str] = field(default_factory=dict)  # agent_id -> proposal_id
    winner: Optional[str] = None
    status: str = "pending"  # pending, consensus, deadlock, resolved


class ConsensusRoom:
    """
    A room where agents negotiate to reach consensus.
    Similar to Mycelium's consensus rooms.
    """

    def __init__(
        self,
        room_id: str,
        topic: str,
        strategy: VoteStrategy = VoteStrategy.MAJORITY,
        max_rounds: int = 5
    ):
        self.room_id = room_id
        self.topic = topic
        self.strategy = strategy
        self.max_rounds = max_rounds

        self.rounds: List[ConsensusRound] = []
        self.current_round: Optional[ConsensusRound] = None
        self.participants: Dict[str, float] = {}  # agent_id -> trust_weight

        self._round_counter = 0

    def add_participant(self, agent_id: str, trust_weight: float = 1.0):
        """Add an agent to the room."""
        self.participants[agent_id] = trust_weight

    def submit_proposal(self, agent_id: str, content: Any, rationale: str = "", confidence: float = 0.5):
        """Submit a proposal to the current round."""
        if not self.current_round or self.current_round.status != "pending":
            self._start_new_round()

        proposal = Proposal(
            id=f"proposal_{len(self.current_round.proposals)}",
            agent_id=agent_id,
            content=content,
            rationale=rationale,
            confidence=confidence
        )
        self.current_round.proposals.append(proposal)

    def vote(self, agent_id: str, proposal_id: str):
        """Vote for a proposal."""
        if self.current_round and self.current_round.status == "pending":
            self.current_round.votes[agent_id] = proposal_id

    def resolve(self) -> Optional[Dict]:
        """Resolve the current round based on strategy."""
        if not self.current_round:
            return None

        proposals = self.current_round.proposals
        votes = self.current_round.votes

        if not proposals or not votes:
            return None

        if self.strategy == VoteStrategy.MAJORITY:
            # Count votes
            vote_counts: Dict[str, int] = {}
            for voter_id, voted_proposal_id in votes.items():
                vote_counts[voted_proposal_id] = vote_counts.get(voted_proposal_id, 0) + 1

            max_votes = max(vote_counts.values())
            winners = [p_id for p_id, count in vote_counts.items() if count == max_votes]

            if len(winners) == 1:
                self.current_round.winner = winners[0]
                self.current_round.status = "consensus"
            else:
                # Tie - need another round
                self.current_round.status = "deadlock"

        elif self.strategy == VoteStrategy.WEIGHTED:
            # Weighted by trust
            weighted_scores: Dict[str, float] = {}
            for voter_id, voted_proposal_id in votes.items():
                weight = self.participants.get(voter_id, 1.0)
                weighted_scores[voted_proposal_id] = weighted_scores.get(voted_proposal_id, 0) + weight

            max_score = max(weighted_scores.values())
            winners = [p_id for p_id, score in weighted_scores.items() if score == max_score]

            self.current_round.winner = winners[0] if len(winners) == 1 else None
            self.current_round.status = "consensus" if self.current_round.winner else "deadlock"

        elif self.strategy == VoteStrategy.UNANIMOUS:
            # All must vote for same proposal
            if len(set(votes.values())) == 1 and len(votes) >= len(self.participants):
                self.current_round.winner = list(votes.values())[0]
                self.current_round.status = "consensus"
            else:
                self.current_round.status = "deadlock"

        # Add to history and return result
        self.rounds.append(self.current_round)

        return {
            "round_id": self.current_round.round_id,
            "winner": self.current_round.winner,
            "status": self.current_round.status,
            "proposals": [p.id for p in proposals],
            "votes": votes
        }

    def _start_new_round(self):
        """Start a new consensus round."""
        self._round_counter += 1
        self.current_round = ConsensusRound(
            round_id=f"round_{self._round_counter}"
        )

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "topic": self.topic,
            "strategy": self.strategy.value,
            "participants": self.participants,
            "rounds": len(self.rounds),
            "current_round": self.current_round.round_id if self.current_round else None
        }


class ConsensusEngine:
    """Manages multiple consensus rooms."""

    def __init__(self):
        self.rooms: Dict[str, ConsensusRoom] = {}

    def create_room(
        self,
        room_id: str,
        topic: str,
        participants: Dict[str, float],
        strategy: VoteStrategy = VoteStrategy.MAJORITY
    ) -> ConsensusRoom:
        """Create a new consensus room."""
        room = ConsensusRoom(room_id, topic, strategy)
        for agent_id, weight in participants.items():
            room.add_participant(agent_id, weight)

        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[ConsensusRoom]:
        """Get a room by ID."""
        return self.rooms.get(room_id)

    def list_rooms(self) -> List[Dict]:
        """List all rooms."""
        return [room.to_dict() for room in self.rooms.values()]


# Convenience function
def resolve_conflict(agents: List[str], proposals: List[Any], strategy: VoteStrategy = VoteStrategy.MAJORITY) -> Optional[Any]:
    """
    Quick conflict resolution between agents.

    Example:
        agents = ["coder", "reviewer"]
        proposals = ["use_function_a()", "use_function_b()"]
        result = resolve_conflict(agents, proposals)
    """
    engine = ConsensusEngine()
    room_id = f"conflict_{hashlib.md5(str(proposals).encode()).hexdigest()[:8]}"

    room = engine.create_room(
        room_id,
        "auto_conflict",
        {a: 1.0 for a in agents},
        strategy
    )

    for i, proposal in enumerate(proposals):
        room.submit_proposal(agents[i], proposal)

    for agent in agents:
        room.vote(agent, room.current_round.proposals[i].id)

    result = room.resolve()
    if result and result["winner"]:
        winner_idx = int(result["winner"].split("_")[1])
        return proposals[winner_idx] if winner_idx < len(proposals) else None

    return None