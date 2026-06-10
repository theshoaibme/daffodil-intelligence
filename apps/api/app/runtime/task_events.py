"""Turn-scoped task graph events for accurate agent simulation."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

_nested_events: ContextVar[List[Dict[str, Any]]] = ContextVar(
    "nested_task_events", default=[]
)
_pending_tool_events: List[Dict[str, Any]] = []
_pending_ui_events: List[Dict[str, Any]] = []
_turn_root_id: ContextVar[Optional[str]] = ContextVar("turn_root_task_id", default=None)


def new_task_id(prefix: str = "task") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def turn_root_id() -> str:
    root = _turn_root_id.get()
    if not root:
        root = new_task_id("root")
        _turn_root_id.set(root)
    return root


def reset_turn_tasks() -> None:
    _turn_root_id.set(None)
    _nested_events.set([])


def emit_task(
    *,
    task_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    kind: str = "agent",
    name: str,
    title: Optional[str] = None,
    status: str = "active",
    agent_id: Optional[str] = None,
    parallel_group: Optional[str] = None,
    depth: int = 0,
) -> Dict[str, Any]:
    """Build a task SSE event and queue it for nested/tool forwarding."""
    event = {
        "type": "task",
        "task_id": task_id or new_task_id(kind),
        "parent_id": parent_id or turn_root_id(),
        "kind": kind,
        "name": name,
        "title": title or name.replace("_", " ").title(),
        "status": status,
        "agent_id": agent_id or (name if kind == "agent" else None),
        "parallel_group": parallel_group,
        "depth": depth,
    }
    append_nested_event(event)
    return event


def append_nested_event(event: Dict[str, Any]) -> None:
    bucket = list(_nested_events.get() or [])
    bucket.append(event)
    _nested_events.set(bucket)


def take_nested_events() -> List[Dict[str, Any]]:
    events = list(_nested_events.get() or [])
    _nested_events.set([])
    return events


def stash_pending_tool_events(events: List[Dict[str, Any]]) -> None:
    global _pending_tool_events
    _pending_tool_events.extend(events)


def pop_pending_tool_events() -> List[Dict[str, Any]]:
    global _pending_tool_events
    events = list(_pending_tool_events)
    _pending_tool_events = []
    return events


def stash_pending_ui_events(events: List[Dict[str, Any]]) -> None:
    global _pending_ui_events
    _pending_ui_events.extend(events)


def pop_pending_ui_events() -> List[Dict[str, Any]]:
    global _pending_ui_events
    events = list(_pending_ui_events)
    _pending_ui_events = []
    return events
