"""
Unified Chat Pipeline
=====================
Single entry for web chat, Telegram, WebSocket, and messaging webhooks.

Resolves global + per-agent skills/rulesets, then delegates to the orchestrator.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, List, Optional

from ..memory import memory_service
from ..skills.resolver import resolve_runtime_config
from . import orchestrator


def _compose_message(message: str, context_prefix: Optional[str]) -> str:
    if context_prefix and context_prefix.strip():
        return f"{context_prefix.strip()}\n\n{message}"
    return message


async def run_turn(
    message: str,
    *,
    user_id: Any = 0,
    chat_id: Any = "default",
    agent_id: Optional[str] = None,
    context_prefix: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
) -> dict:
    """Run one non-streaming turn through the main agent runtime."""
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
    result = await orchestrator.run(
        prompt,
        user_id=user_id,
        chat_id=chat_id,
        persona=cfg.persona,
        attachments=attachments,
        lang=lang,
        agent_id=cfg.agent_id,
        extra_system=extra_system or None,
    )
    result["agent_id"] = cfg.agent_id
    result["skill_ids"] = cfg.skill_ids
    result["ruleset_ids"] = cfg.ruleset_ids
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
) -> AsyncIterator[dict]:
    """Stream one turn through the main agent runtime."""
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
    async for event in orchestrator.run_stream(
        prompt,
        user_id=user_id,
        chat_id=chat_id,
        persona=cfg.persona,
        attachments=attachments,
        lang=lang,
        agent_id=cfg.agent_id,
        extra_system=extra_system or None,
    ):
        yield event
