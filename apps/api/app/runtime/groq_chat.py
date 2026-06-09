"""Groq OpenAI-compatible chat for fast normal turns and Antigravity fallback."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

from ..core.config import get_settings
from ..prompts.manager import get_system_instructions

logger = logging.getLogger(__name__)
settings = get_settings()


def is_available() -> bool:
    return bool(settings.GROQ_API_KEY)


def _build_messages(message: str, extra_system: Optional[str] = None) -> list[dict[str, str]]:
    system = get_system_instructions()
    if extra_system:
        system = f"{system}\n\n{extra_system}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": message},
    ]


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }


async def chat(
    message: str,
    *,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Non-streaming Groq completion."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    base = settings.GROQ_BASE_URL.rstrip("/")
    payload = {
        "model": model or settings.GROQ_FAST_MODEL,
        "messages": _build_messages(message, extra_system),
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{base}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content or "", "tool_calls": [], "engine": "groq"}


async def stream_chat(
    message: str,
    *,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield content events from Groq's chat completions stream."""
    if not settings.GROQ_API_KEY:
        return

    base = settings.GROQ_BASE_URL.rstrip("/")
    payload = {
        "model": model or settings.GROQ_FAST_MODEL,
        "messages": _build_messages(message, extra_system),
        "stream": True,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{base}/chat/completions",
                headers=_headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content")
                    if text:
                        yield {"type": "content", "content": text}
    except Exception as e:
        logger.error("Groq stream failed: %s", e)
        raise
