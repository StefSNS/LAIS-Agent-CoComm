"""
Goal Planner - Task Decomposition and Planning
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskDAG:
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[tuple] = field(default_factory=list)

    def add_node(self, task_id: str, dependencies: List[str] = None):
        self.nodes[task_id] = {
            "id": task_id,
            "dependencies": dependencies or [],
            "status": "pending",
            "created": datetime.now().isoformat()
        }

    def add_edge(self, from_id: str, to_id: str):
        self.edges.append((from_id, to_id))

    def get_ready_tasks(self) -> List[str]:
        completed = {n for n, d in self.nodes.items() if d["status"] == "completed"}
        ready = []
        for task_id, data in self.nodes.items():
            if data["status"] == "pending":
                if all(dep in completed for dep in data.get("dependencies", [])):
                    ready.append(task_id)
        return ready


class GoalDecomposer:
    """Decompose complex goals into task DAGs."""

    def __init__(self):
        self.plans: List[TaskDAG] = []

    def decompose(self, goal: str, strategy: str = "sequential") -> TaskDAG:
        dag = TaskDAG()

        dag.add_node("task_1", dependencies=[])
        dag.add_node("task_2", dependencies=["task_1"])
        dag.add_node("task_3", dependencies=["task_1"])
        dag.add_node("task_4", dependencies=["task_2", "task_3"])

        self.plans.append(dag)
        return dag

    def get_plan(self, index: int = -1) -> Optional[TaskDAG]:
        return self.plans[index] if self.plans else None


def create_goal_dag(goal: str) -> TaskDAG:
    decomposer = GoalDecomposer()
    return decomposer.decompose(goal)