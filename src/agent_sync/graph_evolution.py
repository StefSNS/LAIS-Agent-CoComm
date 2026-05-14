"""
Self-Healing Graph Evolution (from Hive pattern)
Auto-adapts task DAG on failures - recovers and redirects work.
"""

from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"


class EdgeStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class GraphNode:
    """A node in the evolving task graph."""
    id: str
    task: str
    assigned_agent: str = ""
    status: NodeStatus = NodeStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    result: Optional[Any] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts


@dataclass
class GraphEdge:
    """Directed edge between nodes."""
    from_node: str
    to_node: str
    status: EdgeStatus = EdgeStatus.ACTIVE


class EvolvingGraph:
    """
    A self-healing task graph that adapts to failures.
    Like Hive's auto-evolving graphs.
    """

    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.created_at = datetime.now().isoformat()
        self.failure_history: List[Dict] = []

        # Recovery strategies
        self._recovery_handlers: Dict[str, Callable] = {}

    def add_node(self, node_id: str, task: str, max_attempts: int = 3):
        """Add a node to the graph."""
        self.nodes[node_id] = GraphNode(
            id=node_id,
            task=task,
            max_attempts=max_attempts
        )

    def add_edge(self, from_id: str, to_id: str):
        """Add a dependency edge."""
        if from_id in self.nodes and to_id in self.nodes:
            self.edges.append(GraphEdge(from_node=from_id, to_node=to_id))

    def register_recovery_handler(self, error_type: str, handler: Callable):
        """Register a recovery handler for specific error types."""
        self._recovery_handlers[error_type] = handler

    def mark_node_failed(self, node_id: str, error: str) -> bool:
        """Mark a node as failed and trigger recovery if possible."""
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]
        node.error = error

        # Record failure for learning
        self.failure_history.append({
            "node_id": node_id,
            "task": node.task,
            "error": error,
            "attempts": node.attempts,
            "timestamp": datetime.now().isoformat()
        })

        # Check if we can retry
        if node.can_retry():
            node.status = NodeStatus.RETRY
            node.attempts += 1

            # Try recovery handler if available
            for error_type, handler in self._recovery_handlers.items():
                if error_type in error.lower():
                    recovered_task = handler(error, node.task)
                    if recovered_task:
                        node.task = recovered_task
                        break

            return True
        else:
            node.status = NodeStatus.FAILED
            self._propagate_failure(node_id)
            return False

    def _propagate_failure(self, failed_node_id: str):
        """Propagate failure to dependent nodes."""
        # Find nodes that depend on failed node
        for edge in self.edges:
            if edge.from_node == failed_node_id:
                target_node = self.nodes.get(edge.to_node)
                if target_node and target_node.status == NodeStatus.PENDING:
                    target_node.status = NodeStatus.SKIPPED
                    edge.status = EdgeStatus.FAILED

    def get_ready_nodes(self) -> List[GraphNode]:
        """Get nodes ready to execute (dependencies satisfied)."""
        ready = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue

            # Check all dependencies are completed
            deps = [e.from_node for e in self.edges if e.to_node == node.id]
            deps_completed = all(
                self.nodes.get(dep_id).status == NodeStatus.COMPLETED
                for dep_id in deps
                if dep_id in self.nodes
            )

            if deps_completed:
                ready.append(node)

        return ready

    def get_alternative_routes(self, failed_node_id: str) -> List[str]:
        """Find alternative routes when a node fails."""
        # Simple alternative: skip to next available node
        alternatives = []

        # Find nodes that were blocked by this node
        blocked = [e.to_node for e in self.edges if e.from_node == failed_node_id]

        # Find nodes that don't depend on failed node
        for node_id, node in self.nodes.items():
            if node_id in blocked:
                continue
            if node.status == NodeStatus.PENDING:
                alternatives.append(node_id)

        return alternatives

    def evolve_on_failure(self) -> Dict[str, Any]:
        """Analyze failures and evolve the graph."""
        failed_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.FAILED]
        if not failed_nodes:
            return {"evolved": False, "reason": "no_failures"}

        # Generate evolution report
        report = {
            "evolved": True,
            "failed_nodes": len(failed_nodes),
            "alternatives_found": {},
            "recovery_actions": []
        }

        for node in failed_nodes:
            alts = self.get_alternative_routes(node.id)
            report["alternatives_found"][node.id] = alts

            # Suggest recovery action
            if alts:
                report["recovery_actions"].append({
                    "node": node.id,
                    "action": "skip_to_alternatives",
                    "targets": alts
                })
            else:
                report["recovery_actions"].append({
                    "node": node.id,
                    "action": "rollback",
                    "message": "No alternatives - requires manual intervention"
                })

        return report

    def to_dict(self) -> dict:
        ready = self.get_ready_nodes()
        return {
            "graph_id": self.graph_id,
            "nodes": {
                nid: {
                    "task": n.task,
                    "status": n.status.value,
                    "attempts": n.attempts,
                    "error": n.error
                }
                for nid, n in self.nodes.items()
            },
            "ready_nodes": [n.id for n in ready],
            "failed_count": sum(1 for n in self.nodes.values() if n.status == NodeStatus.FAILED),
            "failure_history_count": len(self.failure_history)
        }


class GraphEvolutionEngine:
    """Engine that manages multiple evolving graphs."""

    def __init__(self):
        self.graphs: Dict[str, EvolvingGraph] = {}

    def create_graph(self, graph_id: str) -> EvolvingGraph:
        """Create a new evolving graph."""
        graph = EvolvingGraph(graph_id)
        self.graphs[graph_id] = graph
        return graph

    def get_graph(self, graph_id: str) -> Optional[EvolvingGraph]:
        """Get a graph by ID."""
        return self.graphs.get(graph_id)

    def auto_heal(self, graph_id: str) -> Dict[str, Any]:
        """Auto-heal a graph after failures."""
        graph = self.graphs.get(graph_id)
        if not graph:
            return {"error": "graph_not_found"}

        return graph.evolve_on_failure()

    def get_stats(self) -> Dict:
        """Get overall statistics."""
        total_nodes = sum(len(g.nodes) for g in self.graphs.values())
        failed_nodes = sum(
            sum(1 for n in g.nodes.values() if n.status == NodeStatus.FAILED)
            for g in self.graphs.values()
        )
        return {
            "total_graphs": len(self.graphs),
            "total_nodes": total_nodes,
            "failed_nodes": failed_nodes,
            "failure_rate": failed_nodes / total_nodes if total_nodes > 0 else 0
        }