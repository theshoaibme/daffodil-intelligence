"""Hugging Face Inference (OpenAI-compatible) chat for GLM and other HF models."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

from ..core.config import get_settings
from ..core.hf_models import resolve_hf_model_id
from ..prompts.manager import get_system_instructions

logger = logging.getLogger(__name__)
settings = get_settings()


def is_available() -> bool:
    return bool(settings.HUGGINGFACE_API_KEY) and settings.HUGGINGFACE_ENABLED


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
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json",
    }


def _resolve_model(model: Optional[str]) -> str:
    raw = model or settings.HUGGINGFACE_MODEL
    return resolve_hf_model_id(raw)


async def chat(
    message: str,
    *,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Non-streaming Hugging Face chat completion."""
    if not is_available():
        raise RuntimeError("HUGGINGFACE_API_KEY is not configured or HF is disabled")

    base = settings.HUGGINGFACE_BASE_URL.rstrip("/")
    payload = {
        "model": _resolve_model(model),
        "messages": _build_messages(message, extra_system),
        "temperature": 0.7,
        "max_tokens": settings.HUGGINGFACE_MAX_TOKENS,
    }

    async with httpx.AsyncClient(timeout=settings.HUGGINGFACE_TIMEOUT_SEC) as client:
        resp = await client.post(
            f"{base}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content or "", "tool_calls": [], "engine": "huggingface"}


async def stream_chat(
    message: str,
    *,
    extra_system: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield content events from Hugging Face chat completions stream."""
    if not is_available():
        return

    base = settings.HUGGINGFACE_BASE_URL.rstrip("/")
    payload = {
        "model": _resolve_model(model),
        "messages": _build_messages(message, extra_system),
        "stream": True,
        "temperature": 0.7,
        "max_tokens": settings.HUGGINGFACE_MAX_TOKENS,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.HUGGINGFACE_TIMEOUT_SEC) as client:
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
        logger.error("Hugging Face stream failed: %s", e)
        raise
