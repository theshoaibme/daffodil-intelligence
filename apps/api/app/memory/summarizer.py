"""Conversation turn storage and rolling summaries."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .repository import MemoryRepository

logger = logging.getLogger(__name__)

TURN_SNIP_LEN = 500
SUMMARY_EVERY_N_TURNS = 6


def _snip(text: str, limit: int = TURN_SNIP_LEN) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


async def summarize_turn(
    repo: MemoryRepository,
    *,
    user_id: int,
    agent_id: str,
    chat_id: Any,
    user_msg: str,
    assistant_msg: str,
    turn_index: int = 0,
) -> Dict[str, Any]:
    """Store a conversation_turn memory after each chat turn."""
    user_snip = _snip(user_msg)
    assistant_snip = _snip(assistant_msg)
    content = f"User: {user_snip}\nAssistant: {assistant_snip}"

    return await repo.upsert(
        user_id=user_id,
        agent_id=agent_id,
        content=content,
        memory_type="conversation_turn",
        visibility="agent_tree",
        source="system",
        payload={
            "chat_id": str(chat_id),
            "turn_index": turn_index,
            "user_snip": user_snip,
            "assistant_snip": assistant_snip,
        },
        metadata={"chat_id": str(chat_id), "turn_index": turn_index},
    )


async def maybe_rolling_summary(
    repo: MemoryRepository,
    *,
    user_id: int,
    agent_id: str,
    chat_id: Any,
    turn_index: int,
) -> Optional[Dict[str, Any]]:
    """Create a rolling conversation_summary every N turns."""
    if turn_index <= 0 or turn_index % SUMMARY_EVERY_N_TURNS != 0:
        return None

    turns, _ = await repo.list_memories(
        user_id,
        agent_id=agent_id,
        memory_type="conversation_turn",
        chat_id=chat_id,
        limit=SUMMARY_EVERY_N_TURNS,
    )
    if not turns:
        return None

    snippets = []
    for t in reversed(turns):
        p = t.get("payload", {})
        snippets.append(f"U: {p.get('user_snip', '')}\nA: {p.get('assistant_snip', '')}")

    summary_text = await _generate_summary(snippets)
    return await repo.upsert(
        user_id=user_id,
        agent_id=agent_id,
        content=summary_text,
        memory_type="conversation_summary",
        visibility="shared" if agent_id == "main" else "agent_tree",
        source="system",
        payload={
            "chat_id": str(chat_id),
            "message_count": len(turns),
            "summary": summary_text,
        },
        metadata={"chat_id": str(chat_id), "turn_index": turn_index},
    )


async def _generate_summary(snippets: list[str]) -> str:
    """LLM summary when API key available; otherwise concatenate snippets."""
    combined = "\n---\n".join(snippets)
    if len(combined) <= 800:
        return combined

    from ..core.config import get_settings

    cfg = get_settings()
    if cfg.OPENAI_API_KEY or cfg.GEMINI_API_KEY:
        try:
            return await _llm_summarize(combined)
        except Exception as e:
            logger.warning("LLM summary failed: %s", e)

    return combined[:800] + "..."


async def _llm_summarize(text: str) -> str:
    from ..core.config import get_settings

    cfg = get_settings()
    prompt = (
        "Summarize this conversation in 2-4 sentences. "
        "Focus on topics discussed, decisions, and user preferences.\n\n"
        f"{text[:6000]}"
    )

    if cfg.GEMINI_API_KEY:
        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{cfg.GEMINI_MODEL_NAME}:generateContent?key={cfg.GEMINI_API_KEY}"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    if cfg.OPENAI_API_KEY:
        import httpx

        base = (cfg.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {cfg.OPENAI_API_KEY}"},
                json={
                    "model": cfg.OPENAI_MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    return text[:800]
