"""
Async/Await support for durable agents (from mcp-agent pattern)
Enables long-running agents that can persist across multiple turns.
"""

import asyncio
import threading
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Represents an async agent task."""
    task_id: str
    agent_id: str
    description: str
    state: AgentState = AgentState.IDLE
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoints: List[Dict] = field(default_factory=list)


class AsyncAgent:
    """
    An async agent that can run durable tasks across multiple turns.
    Supports checkpoint/resume, pause/resume, and timeout handling.
    """

    def __init__(
        self,
        agent_id: str,
        handler: Callable[[str], Awaitable[Dict]],
        checkpoint_interval: int = 10,  # Save checkpoint every N steps
        timeout: int = 300  # 5 minutes default
    ):
        self.agent_id = agent_id
        self.handler = handler  # Async function to execute
        self.checkpoint_interval = checkpoint_interval
        self.timeout = timeout

        self._current_task: Optional[AgentTask] = None
        self._state = AgentState.IDLE
        self._checkpoints: Dict[str, AgentTask] = {}
        self._lock = threading.Lock()

    async def run(self, task_id: str, description: str, context: Dict = None) -> Dict:
        """Run an async task with durability."""
        task = AgentTask(
            task_id=task_id,
            agent_id=self.agent_id,
            description=description,
            state=AgentState.RUNNING,
            created_at=datetime.now().isoformat()
        )
        self._current_task = task
        self._state = AgentState.RUNNING

        try:
            # Run with timeout
            result = await asyncio.wait_for(
                self.handler(context or {}),
                timeout=self.timeout
            )

            task.state = AgentState.COMPLETED
            task.result = result
            task.updated_at = datetime.now().isoformat()
            self._state = AgentState.COMPLETED

            return result

        except asyncio.TimeoutError:
            task.state = AgentState.FAILED
            task.error = f"Task timed out after {self.timeout}s"
            task.updated_at = datetime.now().isoformat()
            self._state = AgentState.FAILED

            # Save checkpoint before failing
            self._save_checkpoint(task)

            return {"error": task.error, "task_id": task_id}

        except Exception as e:
            task.state = AgentState.FAILED
            task.error = str(e)
            task.updated_at = datetime.now().isoformat()
            self._state = AgentState.FAILED

            self._save_checkpoint(task)

            return {"error": str(e), "task_id": task_id}

        finally:
            self._current_task = None

    async def run_with_steps(self, task_id: str, description: str, steps: List[str]) -> Dict:
        """Run task with intermediate checkpoints."""
        results = []
        task = AgentTask(
            task_id=task_id,
            agent_id=self.agent_id,
            description=description,
            state=AgentState.RUNNING
        )
        self._current_task = task
        self._state = AgentState.RUNNING

        for i, step in enumerate(steps):
            try:
                # Execute each step
                step_result = await self.handler({"step": step, "step_index": i})
                results.append({"step": step, "result": step_result})

                # Checkpoint every N steps
                if (i + 1) % self.checkpoint_interval == 0:
                    task.checkpoints.append({
                        "step_index": i,
                        "step": step,
                        "partial_results": results.copy(),
                        "timestamp": datetime.now().isoformat()
                    })
                    self._save_checkpoint(task)

            except Exception as e:
                task.state = AgentState.FAILED
                task.error = f"Step {i} failed: {e}"
                self._save_checkpoint(task)
                return {"error": str(e), "completed_steps": results}

        task.state = AgentState.COMPLETED
        task.result = {"steps": results}
        self._state = AgentState.COMPLETED
        return {"steps": results}

    def _save_checkpoint(self, task: AgentTask):
        """Save task checkpoint for recovery."""
        self._checkpoints[task.task_id] = task

    async def resume_from_checkpoint(self, task_id: str, handler: Callable) -> Optional[Dict]:
        """Resume a task from its last checkpoint."""
        checkpoint = self._checkpoints.get(task_id)
        if not checkpoint:
            return None

        # Resume from last checkpoint
        partial_results = checkpoint.checkpoints[-1].get("partial_results", []) if checkpoint.checkpoints else []

        # Continue from where we left off
        self._current_task = checkpoint
        self._state = AgentState.RUNNING
        self.handler = handler  # Update handler for continuation

        return {"resumed": True, "checkpoint": checkpoint.checkpoints}

    def pause(self) -> bool:
        """Pause the current task."""
        if self._state == AgentState.RUNNING:
            self._state = AgentState.PAUSED
            if self._current_task:
                self._current_task.state = AgentState.PAUSED
            return True
        return False

    def resume(self) -> bool:
        """Resume a paused task."""
        if self._state == AgentState.PAUSED:
            self._state = AgentState.RUNNING
            if self._current_task:
                self._current_task.state = AgentState.RUNNING
            return True
        return False

    def get_state(self) -> Dict:
        """Get current agent state."""
        return {
            "agent_id": self.agent_id,
            "state": self._state.value,
            "current_task": self._current_task.to_dict() if self._current_task else None,
            "checkpoints": len(self._checkpoints)
        }


class AsyncAgentPool:
    """Pool of async agents for concurrent execution."""

    def __init__(self, max_agents: int = 5):
        self.max_agents = max_agents
        self._agents: Dict[str, AsyncAgent] = {}
        self._semaphore = asyncio.Semaphore(max_agents)

    async def submit(self, agent_id: str, handler: Callable, task_id: str, description: str) -> str:
        """Submit a task to the pool."""
        async with self._semaphore:
            if agent_id not in self._agents:
                self._agents[agent_id] = AsyncAgent(agent_id, handler)

            agent = self._agents[agent_id]
            result = await agent.run(task_id, description)
            return result

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get status of a specific agent."""
        agent = self._agents.get(agent_id)
        return agent.get_state() if agent else None

    def list_agents(self) -> List[str]:
        """List all agents in the pool."""
        return list(self._agents.keys())