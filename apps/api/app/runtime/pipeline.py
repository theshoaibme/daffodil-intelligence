"""
Unified Chat Pipeline
=====================
Single entry for web chat, Telegram, WebSocket, and messaging webhooks.

Resolves global + per-agent skills/rulesets, then delegates to the orchestrator.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, List, Optional

from ..core.model_router import resolve_model_for_turn
from ..memory import memory_service
from ..prompts.modes import build_mode_system_prompt, mode_status_messages
from ..skills.resolver import resolve_runtime_config
from . import groq_chat, hf_chat, orchestrator
from .chat_router import groq_model_for_routing, should_use_fast_groq, should_use_hf_chat
from .intent_router import route_message
from .routine_turn import run_routine_fast_path, should_use_routine_fast_path, stream_routine_fast_path
from .stream_signals import stream_turn_preamble
from .tool_context import clear_turn_context, set_turn_context
from .task_events import emit_task, reset_turn_tasks, turn_root_id
from .trace import estimate_tokens, trace_recorder


def _compose_message(message: str, context_prefix: Optional[str]) -> str:
    if context_prefix and context_prefix.strip():
        return f"{context_prefix.strip()}\n\n{message}"
    return message


def _apply_mode_system(
    extra_system: str,
    metadata: Optional[dict],
    *,
    routing: str,
    model_id: str,
    engine: str,
) -> str:
    mode_block = build_mode_system_prompt(
        metadata,
        routing=routing,
        model_id=model_id,
        engine=engine,
    )
    if not mode_block:
        return extra_system
    if extra_system:
        return f"{extra_system}\n\n{mode_block}".strip()
    return mode_block


def _resolve_turn_mcp_specs(metadata: Optional[dict]):
    from ..mcp.builder import McpBuilder

    meta = metadata or {}
    raw_servers = meta.get("mcp_servers")
    if not isinstance(raw_servers, list):
        return None

    specs = []
    for entry in raw_servers:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        command = str(entry.get("command") or "").strip()
        if not name or not command:
            continue
        try:
            specs.append(McpBuilder.from_name_command(name, command))
        except ValueError:
            continue
    return specs or None


async def _resolve_turn_metadata(
    user_id: Any,
    metadata: Optional[dict],
    message: Optional[str] = None,
) -> dict:
    """Fill department/section from profile and memory — no hardcoded defaults."""
    from ..automation.routine_mcp import ensure_mcp_in_metadata, mcp_servers_for_user
    from ..automation.routine_memory import recall_user_section
    from ..automation.routine_resolver import normalize_section

    meta = dict(metadata or {})
    uid = int(user_id or 0)

    if uid and not meta.get("department"):
        try:
            from sqlalchemy import select

            from ..core.database import get_session_maker
            from ..models.user import User

            session_maker = get_session_maker()
            if session_maker:
                async with session_maker() as session:
                    row = await session.execute(select(User).where(User.id == uid))
                    user = row.scalar_one_or_none()
                    if user:
                        if user.department:
                            meta["department"] = user.department
                        if user.student_id and not meta.get("student_id"):
                            meta["student_id"] = user.student_id
        except Exception:
            pass

    if meta.get("section"):
        meta["section"] = normalize_section(str(meta["section"])) or None
    elif uid:
        recalled = await recall_user_section(uid)
        if recalled:
            meta["section"] = recalled

    if uid and not meta.get("mcp_servers"):
        servers = mcp_servers_for_user(uid)
        if servers:
            meta["mcp_servers"] = servers

    return ensure_mcp_in_metadata(meta, message)


def _apply_turn_context(
    *,
    user_id: Any,
    metadata: Optional[dict],
) -> None:
    meta = metadata or {}
    telegram_chat_id = meta.get("telegram_chat_id")
    set_turn_context(
        user_id=int(user_id or 0),
        student_id=meta.get("student_id"),
        section=meta.get("section"),
        department=meta.get("department"),
        selected_tools=meta.get("selected_tools") or [],
        telegram_chat_id=int(telegram_chat_id) if telegram_chat_id else None,
        mcp_specs=_resolve_turn_mcp_specs(meta),
    )


async def run_turn(
    message: str,
    *,
    user_id: Any = 0,
    chat_id: Any = "default",
    agent_id: Optional[str] = None,
    context_prefix: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    model_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Run one non-streaming turn through the main agent runtime."""
    resolved_metadata = await _resolve_turn_metadata(user_id, metadata, message)
    _apply_turn_context(user_id=user_id, metadata=resolved_metadata)
    try:
        if should_use_routine_fast_path(message, agent_id):
            return await run_routine_fast_path(
                message, user_id=user_id, metadata=resolved_metadata
            )
        return await _run_turn_inner(
            message,
            user_id=user_id,
            chat_id=chat_id,
            agent_id=agent_id,
            context_prefix=context_prefix,
            attachments=attachments,
            lang=lang,
            model_id=model_id,
            metadata=resolved_metadata,
        )
    finally:
        clear_turn_context()


async def _run_turn_inner(
    message: str,
    *,
    user_id: Any = 0,
    chat_id: Any = "default",
    agent_id: Optional[str] = None,
    context_prefix: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    model_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    resolved_model, was_auto, routing = resolve_model_for_turn(
        model_id=model_id,
        message=message,
        has_attachments=bool(attachments),
    )
    cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)
    recall_block = await memory_service.build_recall_context(
        int(user_id or 0),
        cfg.agent_id,
        message,
        chat_id=chat_id,
    )
    extra_system = cfg.extra_system or ""
    route_hint = route_message(message).hint_block()
    if route_hint:
        extra_system = f"{route_hint}\n\n{extra_system}".strip() if extra_system else route_hint
    if recall_block:
        extra_system = f"{recall_block}\n\n{extra_system}".strip() if extra_system else recall_block
    prompt = _compose_message(message, context_prefix)

    meta = {**(metadata or {}), "_message": message}
    use_hf = should_use_hf_chat(
        model_id=resolved_model,
        attachments=bool(attachments),
        include_tools=cfg.tool_names,
        metadata=meta,
    )
    use_fast_groq = should_use_fast_groq(
        attachments=bool(attachments),
        routing=routing,
        was_auto=was_auto,
        metadata=meta,
        agent_id=cfg.agent_id,
        persona=cfg.persona,
        include_tools=cfg.tool_names,
    ) and not use_hf
    groq_model = groq_model_for_routing(routing) if use_fast_groq else resolved_model
    active_model = groq_model if use_fast_groq else resolved_model
    active_routing = "groq_fast" if use_fast_groq else ("hf_glm" if use_hf else routing)
    engine = "huggingface" if use_hf else ("groq" if use_fast_groq else "antigravity")
    extra_system = _apply_mode_system(
        extra_system,
        metadata,
        routing=active_routing,
        model_id=active_model if use_fast_groq else resolved_model,
        engine=engine,
    )

    if use_hf and hf_chat.is_available():
        result = await hf_chat.chat(
            prompt,
            extra_system=extra_system or None,
            model=resolved_model,
        )
        active_model = resolved_model
    elif use_fast_groq and groq_chat.is_available():
        result = await groq_chat.chat(
            prompt,
            extra_system=extra_system or None,
            model=groq_model,
        )
    else:
        result = await orchestrator.run(
            prompt,
            user_id=user_id,
            chat_id=chat_id,
            persona=cfg.persona,
            attachments=attachments,
            lang=lang,
            agent_id=cfg.agent_id,
            extra_system=extra_system or None,
            model=resolved_model,
            include_tools=cfg.tool_names,
            metadata=meta,
        )

    result["agent_id"] = cfg.agent_id
    result["skill_ids"] = cfg.skill_ids
    result["ruleset_ids"] = cfg.ruleset_ids
    result["model_id"] = active_model
    result["model_mode"] = "auto" if was_auto else "manual"
    result["model_routing"] = active_routing
    result["engine"] = engine
    return result


async def run_turn_stream(
    message: str,
    *,
    user_id: Any = 0,
    chat_id: Any = "default",
    agent_id: Optional[str] = None,
    context_prefix: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    model_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> AsyncIterator[dict]:
    """Stream one turn through the main agent runtime."""
    resolved_metadata = await _resolve_turn_metadata(user_id, metadata, message)
    _apply_turn_context(user_id=user_id, metadata=resolved_metadata)
    try:
        if should_use_routine_fast_path(message, agent_id):
            async for event in stream_routine_fast_path(
                message, user_id=user_id, metadata=resolved_metadata
            ):
                yield event
            return
        async for event in _run_turn_stream_inner(
            message,
            user_id=user_id,
            chat_id=chat_id,
            agent_id=agent_id,
            context_prefix=context_prefix,
            attachments=attachments,
            lang=lang,
            model_id=model_id,
            metadata=resolved_metadata,
        ):
            yield event
    finally:
        clear_turn_context()


async def _run_turn_stream_inner(
    message: str,
    *,
    user_id: Any = 0,
    chat_id: Any = "default",
    agent_id: Optional[str] = None,
    context_prefix: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    model_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> AsyncIterator[dict]:
    resolved_model, was_auto, routing = resolve_model_for_turn(
        model_id=model_id,
        message=message,
        has_attachments=bool(attachments),
    )
    cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)
    recall_block = await memory_service.build_recall_context(
        int(user_id or 0),
        cfg.agent_id,
        message,
        chat_id=chat_id,
    )
    extra_system = cfg.extra_system or ""
    route_hint = route_message(message).hint_block()
    if route_hint:
        extra_system = f"{route_hint}\n\n{extra_system}".strip() if extra_system else route_hint
    if recall_block:
        extra_system = f"{recall_block}\n\n{extra_system}".strip() if extra_system else recall_block
    prompt = _compose_message(message, context_prefix)

    meta = {**(metadata or {}), "_message": message}
    use_hf = should_use_hf_chat(
        model_id=resolved_model,
        attachments=bool(attachments),
        include_tools=cfg.tool_names,
        metadata=meta,
    )
    use_fast_groq = should_use_fast_groq(
        attachments=bool(attachments),
        routing=routing,
        was_auto=was_auto,
        metadata=meta,
        agent_id=cfg.agent_id,
        persona=cfg.persona,
        include_tools=cfg.tool_names,
    ) and not use_hf
    groq_model = groq_model_for_routing(routing) if use_fast_groq else resolved_model
    active_model = groq_model if use_fast_groq else resolved_model
    active_routing = "groq_fast" if use_fast_groq else ("hf_glm" if use_hf else routing)
    engine = "huggingface" if use_hf else ("groq" if use_fast_groq else "antigravity")
    display_model = resolved_model if use_hf else active_model
    extra_system = _apply_mode_system(
        extra_system,
        metadata,
        routing=active_routing,
        model_id=display_model,
        engine=engine,
    )

    yield {
        "type": "model",
        "model_id": display_model,
        "model_mode": "auto" if was_auto else "manual",
        "model_routing": active_routing,
    }

    turn_id = trace_recorder.begin_turn(
        user_id=user_id,
        chat_id=chat_id,
        agent_id=cfg.agent_id,
        model=display_model or "auto",
    )
    trace_recorder.add_tokens(turn_id, estimate_tokens(prompt) + estimate_tokens(extra_system or ""))
    trace_recorder.event(turn_id, type="model", name=display_model or "auto", detail=active_routing or "")
    trace_recorder.event(turn_id, type="agent", name=cfg.agent_id, status="active")

    reset_turn_tasks()
    root_task = emit_task(
        kind="agent",
        name=cfg.agent_id or "main",
        title=f"Orchestrator ({cfg.agent_id or 'main'})",
        status="active",
        agent_id=cfg.agent_id or "main",
        depth=0,
    )
    yield root_task

    if recall_block:
        trace_recorder.event(turn_id, type="memory", name="recall_notes", status="active")
        yield {"type": "memory", "name": "recall_notes", "status": "active"}

    status_lines = mode_status_messages(
        metadata,
        routing=active_routing,
        model_id=display_model,
        engine=engine,
    )
    async for signal in stream_turn_preamble(
        status_lines=status_lines,
        routing=active_routing,
    ):
        stype = signal.get("type")
        if stype in ("thinking", "status"):
            trace_recorder.event(
                turn_id,
                type=stype,
                detail=(signal.get("content", "") or "")[:160],
            )
        yield signal

    async def _stream_orchestrator():
        async for event in orchestrator.run_stream(
            prompt,
            user_id=user_id,
            chat_id=chat_id,
            persona=cfg.persona,
            attachments=attachments,
            lang=lang,
            agent_id=cfg.agent_id,
            extra_system=extra_system or None,
            model=resolved_model,
            include_tools=cfg.tool_names,
            metadata=meta,
        ):
            etype = event.get("type") if isinstance(event, dict) else None
            if etype == "content":
                trace_recorder.add_tokens(turn_id, estimate_tokens(event.get("content", "")))
            elif etype in ("tool", "thinking", "subagent", "status", "memory", "task", "ui"):
                trace_recorder.event(
                    turn_id,
                    type=etype,
                    name=event.get("name", "") or event.get("task_id", ""),
                    status=event.get("status", ""),
                    detail=(event.get("content", "") or event.get("title", "") or "")[:160],
                )
            yield event

    try:
        if use_hf and hf_chat.is_available():
            hf_failed = False
            try:
                async for event in hf_chat.stream_chat(
                    prompt,
                    extra_system=extra_system or None,
                    model=resolved_model,
                ):
                    etype = event.get("type") if isinstance(event, dict) else None
                    if etype == "content":
                        trace_recorder.add_tokens(turn_id, estimate_tokens(event.get("content", "")))
                    yield event
            except Exception as hf_err:
                hf_failed = True
                trace_recorder.event(
                    turn_id,
                    type="status",
                    detail=f"HF fallback: {hf_err}",
                )
                yield {
                    "type": "status",
                    "content": "Switching to full agent runtime for tools and delegation.",
                }
            if hf_failed:
                async for event in _stream_orchestrator():
                    yield event
        elif use_fast_groq and groq_chat.is_available():
            async for event in groq_chat.stream_chat(
                prompt,
                extra_system=extra_system or None,
                model=groq_model,
            ):
                etype = event.get("type") if isinstance(event, dict) else None
                if etype == "content":
                    trace_recorder.add_tokens(turn_id, estimate_tokens(event.get("content", "")))
                yield event
        else:
            async for event in _stream_orchestrator():
                yield event

        trace_recorder.event(turn_id, type="agent", name=cfg.agent_id, status="success")
        yield emit_task(
            task_id=turn_root_id(),
            kind="agent",
            name=cfg.agent_id or "main",
            title=f"Orchestrator ({cfg.agent_id or 'main'})",
            status="success",
            agent_id=cfg.agent_id or "main",
            depth=0,
        )
    finally:
        reset_turn_tasks()
        trace_recorder.end_turn(turn_id)
