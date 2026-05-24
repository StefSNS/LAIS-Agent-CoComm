"""
Async - Async Agent System
"""

import asyncio
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AsyncAgent:
    agent_id: str
    name: str
    state: AgentState = AgentState.IDLE
    task: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AsyncAgentPool:
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.agents: Dict[str, AsyncAgent] = {}
        self._running = 0

    async def submit(self, agent_id: str, task: Callable, *args) -> Any:
        if self._running >= self.max_concurrent:
            await self._wait_for_slot()

        agent = AsyncAgent(agent_id=agent_id, name=agent_id, state=AgentState.RUNNING)
        self.agents[agent_id] = agent
        self._running += 1
        agent.started_at = datetime.now()

        try:
            result = await task(*args)
            agent.state = AgentState.COMPLETED
            agent.result = result
        except Exception as e:
            agent.state = AgentState.FAILED
            agent.result = str(e)
        finally:
            self._running -= 1
            agent.completed_at = datetime.now()

        return agent.result

    async def _wait_for_slot(self):
        while self._running >= self.max_concurrent:
            await asyncio.sleep(0.1)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "max_concurrent": self.max_concurrent,
            "agents": {aid: {"state": a.state.value} for aid, a in self.agents.items()}
        }