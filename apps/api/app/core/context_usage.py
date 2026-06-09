"""Context window usage estimation for chats."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from ..memory import memory_service
from ..models.user import Chat, Message
from ..skills.resolver import resolve_runtime_config

# Approximate token limits per model (input context window).
MODEL_CONTEXT_LIMITS: Dict[str, int] = {
    "gemini-2.5-pro": 1_048_576,
    "gemini-2.5-flash": 1_048_576,
    "gemini-2.5-flash-lite": 1_048_576,
    "gemini-2.0-flash": 1_048_576,
    "gemini-2.0-flash-lite": 1_048_576,
    "gemini-3-flash": 1_048_576,
    "gemini-3-pro": 1_048_576,
    "gemini-1.5-flash": 1_048_576,
    "gemini-1.5-pro": 2_097_152,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 128_000,
    "o1": 200_000,
    "o1-mini": 128_000,
    "o3-mini": 200_000,
    "claude-3.5-sonnet": 200_000,
    "claude-3.5-haiku": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "deepseek-chat": 64_000,
    "deepseek-reasoner": 64_000,
}

# Baseline runtime overhead (system prompt, tools, policies).
BASE_SYSTEM_OVERHEAD_TOKENS = 2_500


def estimate_tokens(text: str) -> int:
    """Rough token count from character length (~4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def resolve_context_limit(model_id: Optional[str] = None) -> int:
    settings = get_settings()
    if model_id and model_id in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_id]
    default_model = settings.ANTIGRAVITY_MODEL
    if default_model in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[default_model]
    return getattr(settings, "CONTEXT_WINDOW_TOKENS", 128_000)


def build_context_usage_payload(
    *,
    used_tokens: int,
    max_tokens: int,
    breakdown: Dict[str, int],
    message_count: int,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    ratio = min(1.0, used_tokens / max_tokens) if max_tokens > 0 else 0.0
    return {
        "usage_ratio": round(ratio, 4),
        "used_tokens": used_tokens,
        "max_tokens": max_tokens,
        "usage_percent": round(ratio * 100),
        "breakdown": breakdown,
        "message_count": message_count,
        "model_id": model_id,
    }


async def compute_chat_context_usage(
    db: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    draft_message: str = "",
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute context usage for a chat including memory recall and draft input."""
    chat_row = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat_obj = chat_row.scalar_one_or_none()
    agent_id = chat_obj.agent_type if chat_obj else "main"

    msg_result = await db.execute(
        select(Message)
        .join(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .order_by(Message.created_at)
    )
    messages: List[Message] = list(msg_result.scalars().all())

    message_tokens = sum(estimate_tokens(m.content or "") for m in messages)
    draft_tokens = estimate_tokens(draft_message.strip())

    last_user_message = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_message = m.content or ""
            break
    recall_probe = draft_message.strip() or last_user_message

    recall_text = ""
    try:
        recall_text = await memory_service.build_recall_context(
            user_id,
            agent_id,
            recall_probe,
            chat_id=chat_id,
        )
    except Exception:
        recall_text = ""

    memory_tokens = estimate_tokens(recall_text)

    cfg = await resolve_runtime_config(agent_id=agent_id, user_id=user_id)
    system_tokens = estimate_tokens(cfg.extra_system or "") + BASE_SYSTEM_OVERHEAD_TOKENS

    breakdown = {
        "messages": message_tokens,
        "draft": draft_tokens,
        "memory_recall": memory_tokens,
        "system_overhead": system_tokens,
    }
    used_tokens = sum(breakdown.values())
    max_tokens = resolve_context_limit(model_id)

    return build_context_usage_payload(
        used_tokens=used_tokens,
        max_tokens=max_tokens,
        breakdown=breakdown,
        message_count=len(messages),
        model_id=model_id,
    )
