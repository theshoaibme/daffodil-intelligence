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
from .agent_factory import AgentPersona

logger = logging.getLogger(__name__)


async def _legacy_run(message: str, user_id: Any) -> dict:
    from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
    agents = detect_intent(message)
    results = await process_with_agents(message, agents, {"user_id": user_id})
    content = await synthesize_response(results, message)
    return {"content": content, "tool_calls": [], "agents": agents, "engine": "legacy"}


async def run(
    message: str,
    user_id: Any = 0,
    chat_id: Any = "default",
    persona: AgentPersona | str = AgentPersona.MAIN,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
) -> dict:
    """Run one turn and return {content, tool_calls/agents, engine}."""
    if session_manager.available():
        try:
            res = await session_manager.chat(
                message, user_id=user_id, chat_id=chat_id,
                persona=persona, attachments=attachments, lang=lang,
            )
            res["engine"] = "antigravity"
            return res
        except Exception as e:
            logger.error(f"Antigravity run failed, falling back to legacy: {e}")
    return await _legacy_run(message, user_id)


async def run_stream(
    message: str,
    user_id: Any = 0,
    chat_id: Any = "default",
    persona: AgentPersona | str = AgentPersona.MAIN,
    attachments: Optional[List[Any]] = None,
    lang: Optional[str] = None,
) -> AsyncIterator[str]:
    """Yield text tokens for one turn (Antigravity, else legacy word-stream)."""
    if session_manager.available():
        try:
            async for token in session_manager.stream(
                message, user_id=user_id, chat_id=chat_id,
                persona=persona, attachments=attachments, lang=lang,
            ):
                yield token
            return
        except Exception as e:
            logger.error(f"Antigravity stream failed, falling back to legacy: {e}")

    result = await _legacy_run(message, user_id)
    content = result["content"] or ""
    for word in content.split(" "):
        yield word + " "
