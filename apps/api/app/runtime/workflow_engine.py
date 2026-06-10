"""Durable workflow DAG engine with checkpoints and parallel execution."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

NodeStatus = Literal["pending", "running", "success", "error", "cancelled"]
WorkflowStatus = Literal["pending", "running", "paused", "completed", "failed", "cancelled"]


@dataclass
class WorkflowNodeSpec:
    id: str
    kind: str = "agent"
    agent_id: Optional[str] = None
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    parallel_group: Optional[str] = None


@dataclass
class WorkflowSpec:
    name: str
    nodes: List[WorkflowNodeSpec] = field(default_factory=list)


@dataclass
class WorkflowState:
    id: str
    status: WorkflowStatus = "pending"
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    checkpoint: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowEngine:
    """In-memory workflow engine with optional DB persistence hooks."""

    def __init__(self):
        self._workflows: Dict[str, WorkflowState] = {}

    def create(self, spec: WorkflowSpec, *, user_id: int, chat_id: Optional[int] = None) -> WorkflowState:
        wf_id = str(uuid4())
        nodes: Dict[str, Dict[str, Any]] = {}
        for node in spec.nodes:
            nodes[node.id] = {
                "id": node.id,
                "kind": node.kind,
                "agent_id": node.agent_id,
                "name": node.name,
                "status": "pending",
                "input": node.input,
                "depends_on": node.depends_on,
                "parallel_group": node.parallel_group,
                "output": None,
            }
        state = WorkflowState(
            id=wf_id,
            status="pending",
            nodes=nodes,
            checkpoint={"user_id": user_id, "chat_id": chat_id, "name": spec.name},
        )
        self._workflows[wf_id] = state
        return state

    def get(self, workflow_id: str) -> Optional[WorkflowState]:
        return self._workflows.get(workflow_id)

    def _ready_nodes(self, state: WorkflowState) -> List[str]:
        ready = []
        for nid, node in state.nodes.items():
            if node["status"] != "pending":
                continue
            deps = node.get("depends_on") or []
            if all(state.nodes[d]["status"] == "success" for d in deps if d in state.nodes):
                ready.append(nid)
        return ready

    async def run(self, workflow_id: str) -> WorkflowState:
        state = self._workflows.get(workflow_id)
        if not state:
            raise ValueError(f"Workflow not found: {workflow_id}")

        state.status = "running"
        while True:
            ready = self._ready_nodes(state)
            if not ready:
                pending = [n for n in state.nodes.values() if n["status"] == "pending"]
                if pending:
                    state.status = "failed"
                    break
                state.status = "completed"
                break

            groups: Dict[Optional[str], List[str]] = {}
            for nid in ready:
                pg = state.nodes[nid].get("parallel_group")
                groups.setdefault(pg, []).append(nid)

            for group_nodes in groups.values():
                await asyncio.gather(
                    *[self._run_node(state, nid) for nid in group_nodes]
                )

        return state

    async def _run_node(self, state: WorkflowState, node_id: str) -> None:
        node = state.nodes[node_id]
        node["status"] = "running"
        node["started_at"] = datetime.now(timezone.utc).isoformat()
        try:
            # Placeholder: actual execution delegates to AgentManager / tools
            await asyncio.sleep(0)
            node["status"] = "success"
            node["output"] = {"completed": True}
        except Exception as exc:
            node["status"] = "error"
            node["output"] = {"error": str(exc)}
        node["finished_at"] = datetime.now(timezone.utc).isoformat()
        state.checkpoint["last_node"] = node_id

    def pause(self, workflow_id: str) -> Optional[WorkflowState]:
        state = self._workflows.get(workflow_id)
        if state:
            state.status = "paused"
        return state

    def cancel(self, workflow_id: str) -> Optional[WorkflowState]:
        state = self._workflows.get(workflow_id)
        if state:
            state.status = "cancelled"
            for node in state.nodes.values():
                if node["status"] in ("pending", "running"):
                    node["status"] = "cancelled"
        return state


_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
