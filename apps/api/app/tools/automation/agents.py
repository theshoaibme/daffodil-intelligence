"""Invoke specialized domain agents as tools."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from ..base import BaseTool, ToolParameter, ToolResult
from ...runtime.tool_context import get_user_id

_STREAMING_AGENTS = frozenset(
    {
        "planning",
        "academic",
        "exam",
        "library",
        "transport",
        "research",
        "writing",
        "tasks",
        "event",
        "automation",
        "career",
        "coding",
        "computer_use",
    }
)


async def _stream_agent_turn(
    *,
    key: str,
    message: str,
    uid: int,
    metadata: Dict[str, Any] | None = None,
) -> str:
    """Run a nested agent turn and emit task/agent/tool events for simulation."""
    from ...runtime.pipeline import run_turn_stream
    from ...runtime.task_events import append_nested_event, emit_task, new_task_id

    parent_task = emit_task(
        kind="agent",
        name=key,
        title=f"Agent: {key.replace('_', ' ').title()}",
        status="active",
        agent_id=key,
        depth=1,
    )
    task_id = parent_task["task_id"]
    content_parts: List[str] = []

    async for event in run_turn_stream(
        message,
        user_id=uid,
        chat_id=f"invoke-{uid}-{key}",
        agent_id=key,
        metadata=metadata,
    ):
        etype = event.get("type")
        if etype == "content":
            content_parts.append(event.get("content") or "")
        elif etype in ("tool", "subagent", "memory", "agent", "task", "ui"):
            child = dict(event)
            child["parent_id"] = task_id
            child["depth"] = int(child.get("depth") or 0) + 2
            append_nested_event(child)
        elif etype == "status" and event.get("content"):
            append_nested_event(
                emit_task(
                    parent_id=task_id,
                    kind="status",
                    name="status",
                    title=str(event["content"])[:120],
                    status="success",
                    depth=2,
                )
            )

    emit_task(
        task_id=task_id,
        parent_id=parent_task.get("parent_id"),
        kind="agent",
        name=key,
        title=f"Agent: {key.replace('_', ' ').title()}",
        status="success",
        agent_id=key,
        depth=1,
    )
    append_nested_event(
        {"type": "subagent", "agent_id": key, "name": key, "status": "success"}
    )
    return "".join(content_parts).strip()


class ListAgentsTool(BaseTool):
    name = "list_agents"
    description = (
        "List all specialized agents available to invoke (academic, routine, exam, "
        "planning, library, etc.) plus any custom Agent Hub agents, with short descriptions."
    )
    category = "automation"
    parameters: list[ToolParameter] = []

    async def execute(self, **kwargs) -> ToolResult:
        from ...agents.registry import AGENT_MAP
        from ...agents.builder import list_agents

        agents = [
            {"id": key, "name": agent.name, "description": agent.description, "kind": "builtin"}
            for key, agent in AGENT_MAP.items()
        ]
        for custom in list_agents():
            if custom.id in AGENT_MAP:
                continue
            agents.append(
                {
                    "id": custom.id,
                    "name": custom.name,
                    "description": custom.description,
                    "kind": "custom",
                }
            )
        return self.ok({"agents": agents, "count": len(agents)})


class InvokeAgentTool(BaseTool):
    name = "invoke_agent"
    description = (
        "Run a specialized agent (routine, exam, planning, academic, library, research, etc.) "
        "with a message and return its response. Use for tasks that need a specific expert agent."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="agent_type",
            type="string",
            description=(
                "Agent key e.g. routine, exam, planning, academic, event, automation, research"
            ),
        ),
        ToolParameter(
            name="message",
            type="string",
            description="Task or question to send to that agent",
        ),
        ToolParameter(
            name="user_id",
            type="string",
            description="Web user id (optional; uses current session if omitted)",
            required=False,
        ),
    ]

    async def execute(
        self, agent_type: str, message: str, user_id: str = None, **kwargs
    ) -> ToolResult:
        from ...agents.registry import AGENT_MAP
        from ...agents.builder import get_agent
        from ...runtime.task_events import append_nested_event

        key = (agent_type or "").strip().lower()
        uid = int(user_id) if user_id else get_user_id()

        append_nested_event(
            {
                "type": "subagent",
                "agent_id": key,
                "name": key,
                "status": "active",
            }
        )

        agent = AGENT_MAP.get(key)
        if agent:
            try:
                from ...runtime.tool_context import get_department, get_section

                ctx = {
                    "user_id": uid,
                    "section": get_section(default=""),
                    "department": get_department(),
                }
                if key == "routine":
                    from ...automation.routine_mcp import merge_invoke_metadata
                    from ...runtime.routine_turn import run_routine_for_invoke

                    meta = merge_invoke_metadata(key, message, uid)
                    nested = await run_routine_for_invoke(
                        message, user_id=uid, metadata=meta
                    )
                    response = nested.get("content") or ""
                    ui_blocks = nested.get("ui_blocks") or []
                    return ToolResult(
                        success=True,
                        data={
                            "agent_type": key,
                            "agent_name": agent.name,
                            "response": response,
                        },
                        ui_blocks=ui_blocks,
                        summary=response,
                        tool_name=self.name,
                    )
                if key in _STREAMING_AGENTS:
                    meta = None
                    if key in ("planning", "academic", "exam", "library", "transport"):
                        from ...automation.routine_mcp import merge_invoke_metadata

                        meta = merge_invoke_metadata(key, message, uid)
                    response = await _stream_agent_turn(
                        key=key, message=message, uid=uid, metadata=meta
                    )
                else:
                    response = await agent.process(message, ctx)
                    ui_blocks = _collect_pending_ui_blocks()
                    append_nested_event(
                        {
                            "type": "subagent",
                            "agent_id": key,
                            "name": key,
                            "status": "success",
                        }
                    )
                    return ToolResult(
                        success=True,
                        data={
                            "agent_type": key,
                            "agent_name": agent.name,
                            "response": response,
                        },
                        ui_blocks=ui_blocks,
                        summary=response,
                        tool_name=self.name,
                    )
                return self.ok(
                    {
                        "agent_type": key,
                        "agent_name": agent.name,
                        "response": response,
                    }
                )
            except Exception as e:
                return self.fail(f"Agent '{key}' failed: {e}")

        custom = get_agent(key)
        if custom:
            try:
                response = await _stream_agent_turn(key=key, message=message, uid=uid)
                return self.ok(
                    {
                        "agent_type": key,
                        "agent_name": custom.name,
                        "response": response,
                    }
                )
            except Exception as e:
                return self.fail(f"Custom agent '{key}' failed: {e}")

        available = ", ".join(sorted(AGENT_MAP.keys()))
        return self.fail(f"Unknown agent '{agent_type}'. Available: {available}")


class ParallelInvokeAgentsTool(BaseTool):
    name = "parallel_invoke_agents"
    description = (
        "Run multiple specialized agents in parallel on the same message. "
        "Use when the user request spans domains (e.g. routine + research). "
        "agent_types is a comma-separated list or JSON array of agent keys."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="agent_types",
            type="string",
            description="Comma-separated agent keys e.g. routine,research",
        ),
        ToolParameter(
            name="message",
            type="string",
            description="Task or question for each agent",
        ),
        ToolParameter(
            name="user_id",
            type="string",
            description="Web user id (optional)",
            required=False,
        ),
    ]

    async def execute(
        self, agent_types: str, message: str, user_id: str = None, **kwargs
    ) -> ToolResult:
        from ...runtime.task_events import emit_task, new_task_id

        uid = int(user_id) if user_id else get_user_id()
        keys = _parse_agent_types(agent_types)
        if not keys:
            return self.fail("agent_types is required (e.g. routine,research)")

        group_id = new_task_id("parallel")
        emit_task(
            task_id=group_id,
            kind="plan",
            name="parallel_invoke",
            title=f"Parallel: {', '.join(keys)}",
            status="active",
            parallel_group=group_id,
            depth=1,
        )

        async def _run_one(agent_key: str) -> Dict[str, Any]:
            emit_task(
                parent_id=group_id,
                kind="agent",
                name=agent_key,
                title=f"Parallel {agent_key}",
                status="active",
                agent_id=agent_key,
                parallel_group=group_id,
                depth=2,
            )
            try:
                meta = None
                if agent_key in ("routine", "planning", "academic", "exam", "library", "transport"):
                    from ...automation.routine_mcp import merge_invoke_metadata

                    meta = merge_invoke_metadata(agent_key, message, uid)
                text = await _stream_agent_turn(
                    key=agent_key, message=message, uid=uid, metadata=meta
                )
                emit_task(
                    parent_id=group_id,
                    kind="agent",
                    name=agent_key,
                    title=f"Parallel {agent_key}",
                    status="success",
                    agent_id=agent_key,
                    parallel_group=group_id,
                    depth=2,
                )
                return {"agent_type": agent_key, "response": text, "ok": True}
            except Exception as e:
                emit_task(
                    parent_id=group_id,
                    kind="agent",
                    name=agent_key,
                    title=f"Parallel {agent_key}",
                    status="error",
                    agent_id=agent_key,
                    parallel_group=group_id,
                    depth=2,
                )
                return {"agent_type": agent_key, "error": str(e), "ok": False}

        results = await asyncio.gather(*[_run_one(k) for k in keys])
        emit_task(
            task_id=group_id,
            kind="plan",
            name="parallel_invoke",
            title=f"Parallel: {', '.join(keys)}",
            status="success",
            parallel_group=group_id,
            depth=1,
        )
        return self.ok({"parallel_group": group_id, "results": results, "agents": keys})


def _collect_pending_ui_blocks() -> List[Any]:
    """Attach UI blocks produced by agent.process() run_tool calls."""
    from ...runtime.task_events import pop_pending_ui_events
    from ...ui_blocks.schemas import UiBlock

    blocks: List[Any] = []
    for event in pop_pending_ui_events():
        payload = event.get("block")
        if isinstance(payload, dict):
            blocks.append(UiBlock.model_validate(payload))
    return blocks


def _parse_agent_types(raw: str) -> List[str]:
    text = (raw or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            import json

            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(x).strip().lower() for x in parsed if str(x).strip()]
        except Exception:
            pass
    return [p.strip().lower() for p in text.replace(";", ",").split(",") if p.strip()]
