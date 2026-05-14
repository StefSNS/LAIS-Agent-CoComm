"""
Goal to Task DAG Auto-Decomposition (from open-multi-agent pattern)
Automatically breaks down high-level goals into parallelizable task graphs.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class TaskNode:
    """A node in the task DAG."""
    id: str
    description: str
    agent_type: str  # e.g., "coder", "reviewer", "tester"
    dependencies: Set[str] = field(default_factory=set)
    estimated_duration: int = 60  # seconds
    priority: str = "medium"
    status: str = "pending"  # pending, running, completed, failed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "agent_type": self.agent_type,
            "dependencies": list(self.dependencies),
            "estimated_duration": self.estimated_duration,
            "priority": self.priority,
            "status": self.status
        }


class TaskDAG:
    """Directed Acyclic Graph of tasks."""

    def __init__(self, goal_id: str, goal_description: str):
        self.goal_id = goal_id
        self.goal_description = goal_description
        self.nodes: Dict[str, TaskNode] = {}
        self.created_at = datetime.now().isoformat()

    def add_node(self, node: TaskNode):
        """Add a task node to the DAG."""
        self.nodes[node.id] = node

    def add_edge(self, from_id: str, to_id: str):
        """Add dependency edge (from -> to means to depends on from)."""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[to_id].dependencies.add(from_id)

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks that have all dependencies satisfied."""
        ready = []
        for node in self.nodes.values():
            if node.status != "pending":
                continue
            # Check all dependencies are completed
            deps_completed = all(
                self.nodes.get(dep_id).status == "completed"
                for dep_id in node.dependencies
                if dep_id in self.nodes
            )
            if deps_completed or not node.dependencies:
                ready.append(node)
        return ready

    def get_parallel_groups(self) -> List[List[TaskNode]]:
        """Group tasks that can run in parallel."""
        groups = []
        remaining = set(self.nodes.keys())

        while remaining:
            ready = self.get_ready_tasks()
            ready_ids = {n.id for n in ready}

            # Only include nodes that are both ready and remaining
            group = [n for n in ready if n.id in remaining]
            if not group:
                # Deadlock - remaining tasks have unmet dependencies
                break

            groups.append(group)
            remaining -= ready_ids

        return groups

    def estimate_duration(self) -> int:
        """Estimate total duration (critical path)."""
        # Simple estimation: sum of max parallel groups
        groups = self.get_parallel_groups()
        return sum(max(n.estimated_duration for n in group) for group in groups)

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "goal_description": self.goal_description,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "parallel_groups": [[n.id for n in g] for g in self.get_parallel_groups()],
            "estimated_duration": self.estimate_duration(),
            "created_at": self.created_at
        }


class GoalDecomposer:
    """
    Decomposes natural language goals into task DAGs.
    Uses pattern matching and LLM-style reasoning.
    """

    # Task decomposition patterns
    TASK_PATTERNS = {
        "build": {
            "subtasks": ["design", "implement", "test", "deploy"],
            "agent_map": {"design": "planner", "implement": "coder", "test": "tester", "deploy": "deployer"}
        },
        "fix": {
            "subtasks": ["investigate", "implement", "verify"],
            "agent_map": {"investigate": "researcher", "implement": "coder", "verify": "reviewer"}
        },
        "review": {
            "subtasks": ["analyze", "report"],
            "agent_map": {"analyze": "reviewer", "report": "reviewer"}
        },
        "research": {
            "subtasks": ["gather", "analyze", "synthesize"],
            "agent_map": {"gather": "researcher", "analyze": "researcher", "synthesize": "planner"}
        }
    }

    def __init__(self):
        self.dag_history: List[TaskDAG] = []

    def decompose(self, goal: str, context: Dict = None) -> TaskDAG:
        """Decompose a goal into a task DAG."""
        goal_lower = goal.lower()

        # Generate DAG ID
        dag_id = f"dag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dag = TaskDAG(dag_id, goal)

        # Find matching pattern
        matched_pattern = None
        for pattern_key, pattern_data in self.TASK_PATTERNS.items():
            if pattern_key in goal_lower:
                matched_pattern = pattern_data
                break

        if matched_pattern:
            # Use pattern-based decomposition
            subtasks = matched_pattern["subtasks"]
            agent_map = matched_pattern["agent_map"]
        else:
            # Default decomposition
            subtasks = ["analyze", "execute", "verify"]
            agent_map = {"analyze": "planner", "execute": "coder", "verify": "tester"}

        # Create nodes
        for i, subtask in enumerate(subtasks):
            node = TaskNode(
                id=f"{dag_id}_task_{i}",
                description=f"{subtask} - {goal}",
                agent_type=agent_map.get(subtask, "coder"),
                priority="high" if i == len(subtasks) - 1 else "medium",
                estimated_duration=120 * (i + 1)  # Increasing time for later tasks
            )
            dag.add_node(node)

        # Add dependencies (each task depends on previous)
        nodes_list = list(dag.nodes.values())
        for i in range(1, len(nodes_list)):
            dag.add_edge(nodes_list[i-1].id, nodes_list[i].id)

        self.dag_history.append(dag)
        return dag

    def decompose_with_llm_style(self, goal: str, context: Dict = None) -> TaskDAG:
        """
        More sophisticated decomposition that considers context.
        In production, this would call an LLM.
        """
        # Simple heuristic decomposition
        dag_id = f"dag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dag = TaskDAG(dag_id, goal)

        # Analyze goal complexity
        complexity_indicators = ["and", "or", "with", "also", "then"]
        has_complexity = any(word in goal.lower() for word in complexity_indicators)

        if has_complexity:
            # Complex goal - more granular tasks
            nodes = [
                TaskNode(f"{dag_id}_1", "Understand requirements", "planner", estimated_duration=60),
                TaskNode(f"{dag_id}_2", "Break into components", "planner", dependencies={f"{dag_id}_1"}),
                TaskNode(f"{dag_id}_3", "Implement component 1", "coder", dependencies={f"{dag_id}_2"}),
                TaskNode(f"{dag_id}_4", "Implement component 2", "coder", dependencies={f"{dag_id}_2"}),
                TaskNode(f"{dag_id}_5", "Integrate components", "coder", dependencies={f"{dag_id}_3", f"{dag_id}_4"}),
                TaskNode(f"{dag_id}_6", "Test integration", "tester", dependencies={f"{dag_id}_5"}),
                TaskNode(f"{dag_id}_7", "Verify and finalize", "reviewer", dependencies={f"{dag_id}_6"}),
            ]
        else:
            # Simple goal
            nodes = [
                TaskNode(f"{dag_id}_1", "Analyze goal", "planner", estimated_duration=60),
                TaskNode(f"{dag_id}_2", "Execute", "coder", dependencies={f"{dag_id}_1"}),
                TaskNode(f"{dag_id}_3", "Verify", "tester", dependencies={f"{dag_id}_2"}),
            ]

        for node in nodes:
            dag.add_node(node)

        self.dag_history.append(dag)
        return dag


def create_goal_dag(goal: str, context: Dict = None) -> TaskDAG:
    """Convenience function to create a goal DAG."""
    decomposer = GoalDecomposer()
    return decomposer.decompose(goal, context)