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
from . import groq_chat, orchestrator
from .chat_router import groq_model_for_routing, should_use_fast_groq
from .stream_signals import stream_turn_preamble
from .tool_context import clear_turn_context, set_turn_context
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
        section=meta.get("section") or "64_I",
        selected_tools=meta.get("selected_tools") or [],
        telegram_chat_id=int(telegram_chat_id) if telegram_chat_id else None,
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
    _apply_turn_context(user_id=user_id, metadata=metadata)
    try:
        return await _run_turn_inner(
            message,
            user_id=user_id,
            chat_id=chat_id,
            agent_id=agent_id,
            context_prefix=context_prefix,
            attachments=attachments,
            lang=lang,
            model_id=model_id,
            metadata=metadata,
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
    if recall_block:
        extra_system = f"{recall_block}\n\n{extra_system}".strip() if extra_system else recall_block
    prompt = _compose_message(message, context_prefix)

    use_fast_groq = should_use_fast_groq(
        attachments=bool(attachments),
        routing=routing,
        was_auto=was_auto,
        metadata=metadata,
        agent_id=cfg.agent_id,
        persona=cfg.persona,
        include_tools=cfg.tool_names,
    )
    groq_model = groq_model_for_routing(routing) if use_fast_groq else resolved_model
    active_model = groq_model if use_fast_groq else resolved_model
    active_routing = "groq_fast" if use_fast_groq else routing
    engine = "groq" if use_fast_groq else "antigravity"
    extra_system = _apply_mode_system(
        extra_system,
        metadata,
        routing=active_routing,
        model_id=active_model,
        engine=engine,
    )

    if use_fast_groq and groq_chat.is_available():
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
    _apply_turn_context(user_id=user_id, metadata=metadata)
    try:
        async for event in _run_turn_stream_inner(
            message,
            user_id=user_id,
            chat_id=chat_id,
            agent_id=agent_id,
            context_prefix=context_prefix,
            attachments=attachments,
            lang=lang,
            model_id=model_id,
            metadata=metadata,
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
    if recall_block:
        extra_system = f"{recall_block}\n\n{extra_system}".strip() if extra_system else recall_block
    prompt = _compose_message(message, context_prefix)

    use_fast_groq = should_use_fast_groq(
        attachments=bool(attachments),
        routing=routing,
        was_auto=was_auto,
        metadata=metadata,
        agent_id=cfg.agent_id,
        persona=cfg.persona,
        include_tools=cfg.tool_names,
    )
    groq_model = groq_model_for_routing(routing) if use_fast_groq else resolved_model
    active_model = groq_model if use_fast_groq else resolved_model
    active_routing = "groq_fast" if use_fast_groq else routing
    engine = "groq" if use_fast_groq else "antigravity"
    extra_system = _apply_mode_system(
        extra_system,
        metadata,
        routing=active_routing,
        model_id=active_model,
        engine=engine,
    )

    yield {
        "type": "model",
        "model_id": active_model,
        "model_mode": "auto" if was_auto else "manual",
        "model_routing": active_routing,
    }

    turn_id = trace_recorder.begin_turn(
        user_id=user_id,
        chat_id=chat_id,
        agent_id=cfg.agent_id,
        model=active_model or "auto",
    )
    trace_recorder.add_tokens(turn_id, estimate_tokens(prompt) + estimate_tokens(extra_system or ""))
    trace_recorder.event(turn_id, type="model", name=active_model or "auto", detail=active_routing or "")
    trace_recorder.event(turn_id, type="agent", name=cfg.agent_id, status="active")
    yield {"type": "agent", "agent_id": cfg.agent_id, "name": cfg.agent_id, "status": "active"}

    status_lines = mode_status_messages(
        metadata,
        routing=active_routing,
        model_id=active_model,
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

    try:
        if use_fast_groq and groq_chat.is_available():
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
            ):
                etype = event.get("type") if isinstance(event, dict) else None
                if etype == "content":
                    trace_recorder.add_tokens(turn_id, estimate_tokens(event.get("content", "")))
                elif etype in ("tool", "thinking", "subagent", "status"):
                    trace_recorder.event(
                        turn_id,
                        type=etype,
                        name=event.get("name", ""),
                        status=event.get("status", ""),
                        detail=(event.get("content", "") or "")[:160],
                    )
                yield event
    finally:
        trace_recorder.event(turn_id, type="agent", name=cfg.agent_id, status="success")
        trace_recorder.end_turn(turn_id)
