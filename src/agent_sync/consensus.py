"""
Consensus - Multi-Agent Consensus Engine
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class VoteStrategy(Enum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    UNANIMOUS = "unanimous"


@dataclass
class ConsensusRoom:
    room_id: str
    topic: str
    votes: Dict[str, Any] = field(default_factory=dict)
    strategy: VoteStrategy = VoteStrategy.MAJORITY
    resolved: bool = False


class ConsensusEngine:
    """Multi-agent consensus resolution."""

    def __init__(self):
        self.rooms: Dict[str, ConsensusRoom] = {}

    def create_room(self, topic: str, strategy: VoteStrategy = VoteStrategy.MAJORITY) -> str:
        room_id = f"room_{len(self.rooms)}"
        self.rooms[room_id] = ConsensusRoom(room_id=room_id, topic=topic, strategy=strategy)
        return room_id

    def vote(self, room_id: str, agent_id: str, decision: Any):
        if room_id in self.rooms:
            self.rooms[room_id].votes[agent_id] = decision

    def resolve(self, room_id: str) -> Optional[Any]:
        if room_id not in self.rooms:
            return None

        room = self.rooms[room_id]
        votes = list(room.votes.values())

        if room.strategy == VoteStrategy.MAJORITY:
            counts = {}
            for v in votes:
                key = json.dumps(v, sort_keys=True)
                counts[key] = counts.get(key, 0) + 1
            result = max(counts, key=counts.get)
            room.resolved = True
            return json.loads(result)

        elif room.strategy == VoteStrategy.UNANIMOUS:
            if all(v == votes[0] for v in votes):
                room.resolved = True
                return votes[0]

        return None


def resolve_conflict(agents: List[str], topic: str) -> Optional[Any]:
    engine = ConsensusEngine()
    room_id = engine.create_room(topic, VoteStrategy.MAJORITY)
    for agent in agents:
        engine.vote(room_id, agent, {"decision": "agreed"})
    return engine.resolve(room_id)