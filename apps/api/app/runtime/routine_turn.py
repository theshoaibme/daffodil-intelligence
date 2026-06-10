"""Direct Routine Agent handling for class schedules — data/routines, memory, MCP."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from ..agents.routine import RoutineAgent
from ..automation.routine_mcp import ensure_mcp_in_metadata
from .intent_router import route_message
from .task_events import (
    append_nested_event,
    emit_task,
    pop_pending_ui_events,
    reset_turn_tasks,
    turn_root_id,
)

_MAIN_AGENTS = frozenset({"main", "supervisor", "default", ""})

_CLASS_ROUTINE_SIGNALS = (
    "class routine",
    "class schedule",
    "weekly routine",
    "today class",
    "tomorrow class",
    "today's class",
    "tomorrow's class",
    "today routine",
    "tomorrow routine",
    "tomorrow's routine",
    "today's routine",
)


def should_use_routine_fast_path(message: str, agent_id: Optional[str] = None) -> bool:
    """True when this turn should bypass the main LLM and use RoutineAgent + tools."""
    aid = (agent_id or "main").strip().lower()
    if aid not in _MAIN_AGENTS and aid != "routine":
        return False
    plan = route_message(message)
    lower = (message or "").lower()
    if "get_class_routine" in lower:
        return True
    if any(k in lower for k in _CLASS_ROUTINE_SIGNALS):
        return True
    if plan.primary == "routine":
        return True
    return False


def _build_context(user_id: Any, metadata: Optional[dict]) -> Dict[str, Any]:
    meta = metadata or {}
    return {
        "user_id": int(user_id or 0),
        "section": meta.get("section") or "",
        "department": meta.get("department") or "",
    }


def _start_task_tree(*, orchestrator: str = "main") -> Dict[str, Dict[str, Any]]:
    """Create root → routine agent → get_class_routine tool task chain."""
    reset_turn_tasks()
    root = emit_task(
        kind="agent",
        name=orchestrator,
        title=f"Orchestrator ({orchestrator})",
        status="active",
        agent_id=orchestrator,
        depth=0,
    )
    routine = emit_task(
        parent_id=root["task_id"],
        kind="agent",
        name="routine",
        title="Routine Agent",
        status="active",
        agent_id="routine",
        depth=1,
    )
    tool = emit_task(
        parent_id=routine["task_id"],
        kind="tool",
        name="get_class_routine",
        title="Load class routine",
        status="active",
        agent_id="routine",
        depth=2,
    )
    return {"root": root, "routine": routine, "tool": tool}


def _complete_task_tree(tasks: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mark tool → routine → root as success."""
    events: List[Dict[str, Any]] = []
    tool = tasks["tool"]
    routine = tasks["routine"]
    root = tasks["root"]
    events.append(
        emit_task(
            task_id=tool["task_id"],
            parent_id=tool.get("parent_id"),
            kind="tool",
            name="get_class_routine",
            title="Load class routine",
            status="success",
            agent_id="routine",
            depth=2,
        )
    )
    events.append(
        emit_task(
            task_id=routine["task_id"],
            parent_id=routine.get("parent_id"),
            kind="agent",
            name="routine",
            title="Routine Agent",
            status="success",
            agent_id="routine",
            depth=1,
        )
    )
    events.append(
        emit_task(
            task_id=root["task_id"],
            parent_id=root.get("parent_id") or turn_root_id(),
            kind="agent",
            name=root.get("name", "main"),
            title=root.get("title", "Orchestrator"),
            status="success",
            agent_id=root.get("agent_id", "main"),
            depth=0,
        )
    )
    return events


async def _execute_routine(
    message: str,
    *,
    user_id: Any = 0,
    metadata: Optional[dict] = None,
    orchestrator: str = "main",
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    tasks = _start_task_tree(orchestrator=orchestrator)
    ctx = _build_context(user_id, metadata)
    content = await RoutineAgent().process(message, ctx)
    ui_events = pop_pending_ui_events()
    ui_blocks = [e["block"] for e in ui_events if isinstance(e.get("block"), dict)]
    result = {
        "content": content,
        "engine": "routine",
        "agents": ["routine"],
        "tool_calls": ["get_class_routine"],
        "ui_events": ui_events,
        "ui_blocks": ui_blocks,
        "agent_id": "routine",
    }
    return result, tasks


async def run_routine_fast_path(
    message: str,
    *,
    user_id: Any = 0,
    metadata: Optional[dict] = None,
    orchestrator: str = "main",
) -> Dict[str, Any]:
    """Execute RoutineAgent with real tools; never invent schedule rows."""
    result, _tasks = await _execute_routine(
        message, user_id=user_id, metadata=metadata, orchestrator=orchestrator
    )
    return result


async def stream_routine_fast_path(
    message: str,
    *,
    user_id: Any = 0,
    metadata: Optional[dict] = None,
    orchestrator: str = "main",
) -> AsyncIterator[dict]:
    """Stream task tree + routine agent + UI blocks + summary."""
    meta = ensure_mcp_in_metadata(dict(metadata or {}), message)
    tasks = _start_task_tree(orchestrator=orchestrator)

    yield tasks["root"]
    yield tasks["routine"]
    yield tasks["tool"]

    ctx = _build_context(user_id, meta)
    content = await RoutineAgent().process(
        message,
        ctx,
    )
    ui_events = pop_pending_ui_events()
    ui_blocks = [e["block"] for e in ui_events if isinstance(e.get("block"), dict)]

    for ui_event in ui_events:
        yield ui_event

    for done in _complete_task_tree(tasks):
        yield done

    has_table = any(
        isinstance(b, dict)
        and b.get("schema") == "data_table"
        and (b.get("data") or {}).get("rows")
        for b in ui_blocks
    )
    text = (content or "").strip()
    if text and (not has_table or len(text) < 120):
        yield {"type": "content", "content": text}


async def run_routine_for_invoke(
    message: str,
    *,
    user_id: int,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """Routine agent turn nested under invoke_agent — queues task events for the parent turn."""
    meta = ensure_mcp_in_metadata(dict(metadata or {}), message)
    tasks = _start_task_tree(orchestrator="automation")

    append_nested_event(tasks["routine"])
    append_nested_event(tasks["tool"])
    append_nested_event(
        {
            "type": "tool",
            "name": "get_class_routine",
            "status": "active",
            "agent_id": "routine",
            "source": "local",
        }
    )

    ctx = _build_context(user_id, meta)
    content = await RoutineAgent().process(message, ctx)
    ui_events = pop_pending_ui_events()
    ui_blocks = [e["block"] for e in ui_events if isinstance(e.get("block"), dict)]

    for ui_event in ui_events:
        append_nested_event(ui_event)

    append_nested_event(
        {
            "type": "tool",
            "name": "get_class_routine",
            "status": "success",
            "agent_id": "routine",
            "source": "local",
        }
    )
    append_nested_event(
        {"type": "subagent", "agent_id": "routine", "name": "routine", "status": "success"}
    )
    for done in _complete_task_tree(tasks):
        append_nested_event(done)

    return {
        "content": content,
        "ui_blocks": ui_blocks,
        "agent_id": "routine",
    }
