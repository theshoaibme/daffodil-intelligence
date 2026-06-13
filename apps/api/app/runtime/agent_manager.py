"""Agent lifecycle management: spawn, delegate, pause, resume, cancel."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

AgentStatus = Literal[
    "pending", "running", "paused", "completed", "failed", "cancelled"
]


@dataclass
class AgentHandle:
    id: str
    name: str
    status: AgentStatus = "pending"
    parent_id: Optional[str] = None
    parallel_group: Optional[str] = None
    context_ref: str = ""
    started_at: Optional[datetime] = None
    checkpoint: Optional[Dict[str, Any]] = None
    persona: Optional[str] = None


@dataclass
class SharedContext:
    session_id: str
    turn_id: str
    facts: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    agent_messages: List[Dict[str, Any]] = field(default_factory=list)


class AgentManager:
    """In-process agent registry for a single-tenant deployment."""

    def __init__(self):
        self._agents: Dict[str, AgentHandle] = {}
        self._contexts: Dict[str, SharedContext] = {}

    def _ctx_key(self, session_id: str, turn_id: str) -> str:
        return f"{session_id}:{turn_id}"

    async def spawn_agent(
        self,
        *,
        name: str,
        persona: Optional[str] = None,
        parent_id: Optional[str] = None,
        parallel_group: Optional[str] = None,
        session_id: str,
        turn_id: str,
    ) -> AgentHandle:
        agent_id = f"agent-{uuid4().hex[:10]}"
        handle = AgentHandle(
            id=agent_id,
            name=name,
            status="running",
            parent_id=parent_id,
            parallel_group=parallel_group,
            context_ref=self._ctx_key(session_id, turn_id),
            started_at=datetime.now(timezone.utc),
            persona=persona,
        )
        self._agents[agent_id] = handle
        logger.debug("spawned agent %s (%s)", agent_id, name)
        return handle

    async def delegate(
        self,
        parent: AgentHandle,
        child_specs: List[Dict[str, Any]],
        *,
        session_id: str,
        turn_id: str,
    ) -> List[AgentHandle]:
        group = f"grp-{uuid4().hex[:8]}"
        handles = []
        for spec in child_specs:
            handle = await self.spawn_agent(
                name=spec.get("name", "delegated"),
                persona=spec.get("persona"),
                parent_id=parent.id,
                parallel_group=group,
                session_id=session_id,
                turn_id=turn_id,
            )
            handles.append(handle)
        return handles

    async def pause(self, handle: AgentHandle) -> AgentHandle:
        handle.status = "paused"
        self._agents[handle.id] = handle
        return handle

    async def resume(self, handle: AgentHandle) -> AgentHandle:
        handle.status = "running"
        self._agents[handle.id] = handle
        return handle

    async def cancel(self, handle: AgentHandle) -> AgentHandle:
        handle.status = "cancelled"
        self._agents[handle.id] = handle
        return handle

    async def complete(
        self,
        handle: AgentHandle,
        *,
        status: AgentStatus = "completed",
    ) -> AgentHandle:
        handle.status = status
        self._agents[handle.id] = handle
        return handle

    def get(self, agent_id: str) -> Optional[AgentHandle]:
        return self._agents.get(agent_id)

    def list_active(self, session_id: Optional[str] = None) -> List[AgentHandle]:
        active = [a for a in self._agents.values() if a.status == "running"]
        if session_id:
            prefix = f"{session_id}:"
            active = [a for a in active if a.context_ref.startswith(prefix)]
        return active

    async def get_shared_context(self, session_id: str, turn_id: str) -> SharedContext:
        key = self._ctx_key(session_id, turn_id)
        if key not in self._contexts:
            self._contexts[key] = SharedContext(session_id=session_id, turn_id=turn_id)
        return self._contexts[key]

    def clear_turn(self, session_id: str, turn_id: str) -> None:
        key = self._ctx_key(session_id, turn_id)
        self._contexts.pop(key, None)


# Module singleton
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager
