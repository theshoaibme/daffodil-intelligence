"""Text embeddings for memory recall (OpenAI when available, hash fallback)."""

from __future__ import annotations

import hashlib
import logging
import struct
from typing import List

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_DIM = 384


def _hash_embed(text: str, dim: int = _DIM) -> List[float]:
    """Deterministic pseudo-embedding for dev/tests without an API key."""
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    values: List[float] = []
    while len(values) < dim:
        for i in range(0, len(digest) - 3, 4):
            chunk = struct.unpack(">I", digest[i : i + 4])[0]
            values.append((chunk % 10000) / 5000.0 - 1.0)
            if len(values) >= dim:
                break
        digest = hashlib.sha256(digest).digest()
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return [v / norm for v in values]


async def embed_text(text: str) -> List[float]:
    if not text or not text.strip():
        return _hash_embed("empty")

    if settings.OPENAI_API_KEY:
        try:
            return await _openai_embed(text)
        except Exception as e:
            logger.warning("OpenAI embedding failed, using hash fallback: %s", e)

    return _hash_embed(text)


async def _openai_embed(text: str) -> List[float]:
    import httpx

    base = (settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{base}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": settings.EMBEDDING_MODEL, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


def embedding_dim() -> int:
    return _DIM
