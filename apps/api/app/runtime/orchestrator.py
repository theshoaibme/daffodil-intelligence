"""
Orchestrator
============
The single function the API/Telegram/voice layers call to get an answer.

Primary path: the Antigravity main agent (native tool-calling + sub-agents).
Fallback path: the legacy keyword supervisor (used when the Antigravity SDK or
GEMINI_API_KEY is unavailable, or if a runtime error occurs), so the product
keeps working in every environment.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, List, Optional

from .session_manager import session_manager
from ..core.config import get_settings
from ..core.hf_models import GLM_5_1_CATALOG_ID, is_hf_model
from .agent_factory import AgentPersona, should_run_antigravity

logger = logging.getLogger(__name__)


async def _legacy_run(message: str, user_id: Any, metadata: Optional[dict] = None) -> dict:
    from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
    from .intent_router import route_message
    from .task_events import pop_pending_ui_events

    plan = route_message(message)
    agents = detect_intent(message)
    ctx = {"user_id": user_id, "section": (metadata or {}).get("section") or plan.section}
    results = await process_with_agents(message, agents, ctx)
    content = await synthesize_response(results, message)
    ui_events = pop_pending_ui_events()
    ui_blocks = [e["block"] for e in ui_events if isinstance(e.get("block"), dict)]
    return {
        "content": content,
        "tool_calls": plan.tools,
        "agents": agents,
        "engine": "legacy",
        "ui_events": ui_events,
        "ui_blocks": ui_blocks,
    }


async def run(
    message: str,
    user_id: Any = 0,
    chat_id: Any = "default",
    persona: AgentPersona | str = AgentPersona.MAIN,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    agent_id: Optional[str] = None,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
    include_tools: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Run one turn and return {content, tool_calls/agents, engine}."""
    if extra_system is None and agent_id:
        from ..skills.resolver import resolve_runtime_config
        cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)
        extra_system = cfg.extra_system or None
        persona = cfg.persona
        if include_tools is None:
            include_tools = cfg.tool_names

    if should_run_antigravity(model):
        try:
            res = await session_manager.chat(
                message, user_id=user_id, chat_id=chat_id,
                persona=persona, attachments=attachments, lang=lang,
                extra_system=extra_system, model=model,
                include_tools=include_tools,
            )
            res["engine"] = "antigravity"
            return res
        except Exception as e:
            logger.error(f"Antigravity run failed, falling back to legacy: {e}")

    from .chat_router import message_needs_tools
    from . import hf_chat

    glm_model = model if model and is_hf_model(model) else GLM_5_1_CATALOG_ID
    if hf_chat.is_available() and is_hf_model(glm_model) and not message_needs_tools(message):
        try:
            res = await hf_chat.chat(
                message,
                extra_system=extra_system,
                model=glm_model,
            )
            res["engine"] = "huggingface"
            res["model_id"] = glm_model
            return res
        except Exception as e:
            logger.error("GLM orchestration chat failed, falling back to legacy: %s", e)

    return await _legacy_run(message, user_id, metadata)


async def run_stream(
    message: str,
    user_id: Any = 0,
    chat_id: Any = "default",
    persona: AgentPersona | str = AgentPersona.MAIN,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
    agent_id: Optional[str] = None,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
    include_tools: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> AsyncIterator[dict]:
    """Yield structured stream events for one turn (Antigravity, else legacy)."""
    if extra_system is None and agent_id:
        from ..skills.resolver import resolve_runtime_config
        cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)
        extra_system = cfg.extra_system or None
        persona = cfg.persona
        if include_tools is None:
            include_tools = cfg.tool_names

    if should_run_antigravity(model):
        try:
            async for event in session_manager.stream(
                message, user_id=user_id, chat_id=chat_id,
                persona=persona, attachments=attachments, lang=lang,
                extra_system=extra_system, model=model,
                include_tools=include_tools,
            ):
                yield event
            return
        except Exception as e:
            logger.error(f"Antigravity stream failed, falling back: {e}")

    from .chat_router import message_needs_tools
    from . import hf_chat

    glm_model = model if model and is_hf_model(model) else GLM_5_1_CATALOG_ID
    if hf_chat.is_available() and is_hf_model(glm_model) and not message_needs_tools(message):
        try:
            async for event in hf_chat.stream_chat(
                message,
                extra_system=extra_system,
                model=glm_model,
            ):
                yield event
            return
        except Exception as e:
            logger.error("GLM orchestration stream failed, falling back: %s", e)

    from .groq_chat import is_available as groq_available, stream_chat as groq_stream

    if groq_available() and not message_needs_tools(message):
        try:
            async for event in groq_stream(
                message,
                extra_system=extra_system,
                model=model,
            ):
                yield event
            return
        except Exception as e:
            logger.error(f"Groq stream failed, falling back to legacy: {e}")

    result = await _legacy_run(message, user_id, metadata)
    for ui_event in result.get("ui_events") or []:
        yield ui_event
    content = result["content"] or ""
    for word in content.split(" "):
        yield {"type": "content", "content": word + " "}
