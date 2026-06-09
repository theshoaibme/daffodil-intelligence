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
from ..skills.resolver import resolve_runtime_config
from . import orchestrator
from .tool_context import clear_turn_context, set_turn_context
from .trace import estimate_tokens, trace_recorder


def _compose_message(message: str, context_prefix: Optional[str]) -> str:
    if context_prefix and context_prefix.strip():
        return f"{context_prefix.strip()}\n\n{message}"
    return message


def _tools_mode_hint(metadata: Optional[dict]) -> str:
    if not metadata:
        return ""
    tools = metadata.get("selected_tools") or []
    if not tools:
        return ""
    lines = ["ACTIVE USER MODES (from chat UI — honor these):"]
    if "Planning" in tools:
        lines.append(
            "- Planning: break goals into steps; use invoke_agent(planning) or create_plan flows."
        )
    if "Research" in tools:
        lines.append("- Research: use invoke_agent(research) and web search tools.")
    if "MCP" in tools:
        lines.append("- MCP tools enabled when configured.")
    if "Agent" in tools:
        lines.append("- Agent dashboard mode: coordinate multiple invoke_agent calls when needed.")
    return "\n".join(lines)


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
    mode_hint = _tools_mode_hint(metadata)
    if mode_hint:
        extra_system = f"{extra_system}\n\n{mode_hint}".strip() if extra_system else mode_hint
    prompt = _compose_message(message, context_prefix)
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
    result["model_id"] = resolved_model
    result["model_mode"] = "auto" if was_auto else "manual"
    result["model_routing"] = routing
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
    yield {
        "type": "model",
        "model_id": resolved_model,
        "model_mode": "auto" if was_auto else "manual",
        "model_routing": routing,
    }
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
    mode_hint = _tools_mode_hint(metadata)
    if mode_hint:
        extra_system = f"{extra_system}\n\n{mode_hint}".strip() if extra_system else mode_hint
    prompt = _compose_message(message, context_prefix)

    turn_id = trace_recorder.begin_turn(
        user_id=user_id,
        chat_id=chat_id,
        agent_id=cfg.agent_id,
        model=resolved_model or "auto",
    )
    trace_recorder.add_tokens(turn_id, estimate_tokens(prompt) + estimate_tokens(extra_system or ""))
    trace_recorder.event(turn_id, type="model", name=resolved_model or "auto", detail=routing or "")
    trace_recorder.event(turn_id, type="agent", name=cfg.agent_id, status="active")
    yield {"type": "agent", "agent_id": cfg.agent_id, "name": cfg.agent_id, "status": "active"}

    try:
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
            elif etype in ("tool", "thinking", "subagent"):
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
