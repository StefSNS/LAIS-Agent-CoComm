"""
Graph Evolution - Self-improving Agent Graph
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    INACTIVE = "inactive"


@dataclass
class EvolvingGraph:
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[tuple] = field(default_factory=list)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_node(self, node_id: str, capabilities: List[str]):
        self.nodes[node_id] = {
            "id": node_id,
            "capabilities": capabilities,
            "status": NodeStatus.ACTIVE,
            "connections": [],
            "performance_score": 1.0
        }

    def connect(self, from_id: str, to_id: str):
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id]["connections"].append(to_id)
            self.edges.append((from_id, to_id))

    def update_performance(self, node_id: str, score: float):
        if node_id in self.nodes:
            self.nodes[node_id]["performance_score"] = score
            self.performance_history.append({
                "node": node_id,
                "score": score,
                "timestamp": datetime.now().isoformat()
            })

    def get_optimal_path(self, from_id: str, to_id: str) -> List[str]:
        if from_id not in self.nodes or to_id not in self.nodes:
            return []
        return [from_id, to_id]


class GraphEvolutionEngine:
    """Self-improve agent graph based on performance."""

    def __init__(self):
        self.graph = EvolvingGraph()

    def evolve(self, agent_id: str, performance_metrics: Dict[str, float]) -> bool:
        avg_score = sum(performance_metrics.values()) / len(performance_metrics)
        self.graph.update_performance(agent_id, avg_score)

        if avg_score < 0.5:
            self.graph.nodes[agent_id]["status"] = NodeStatus.DEGRADED
            return False

        return True

    def get_recommendations(self) -> List[str]:
        recommendations = []
        for node_id, data in self.graph.nodes.items():
            if data["status"] == NodeStatus.DEGRADED:
                recommendations.append(f"Improve {node_id}")
        return recommendations