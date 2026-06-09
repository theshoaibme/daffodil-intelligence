"""Tests for PG memory user_id guards and embedding provider detection."""

import pytest

from app.memory.embeddings import _remote_embeddings_available
from app.memory.pg_user import PG_INT_MAX, pg_memory_user_id


def test_pg_memory_user_id_accepts_normal_ids():
    assert pg_memory_user_id(1) == 1
    assert pg_memory_user_id(PG_INT_MAX) == PG_INT_MAX


def test_pg_memory_user_id_rejects_telegram_ids():
    assert pg_memory_user_id(5_187_786_663) is None
    assert pg_memory_user_id(0) is None
    assert pg_memory_user_id(-1) is None
    assert pg_memory_user_id("web:42") is None


def test_remote_embeddings_skip_gemini_compat(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        s,
        "OPENAI_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    assert _remote_embeddings_available() is False

    monkeypatch.setattr(s, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    assert _remote_embeddings_available() is True


@pytest.mark.asyncio
async def test_remember_telegram_user_uses_semantic_fallback(monkeypatch):
    from app.memory import memory_service

    calls = []

    def fake_add(text, user_id=0, metadata=None):
        calls.append((text, user_id, metadata))
        return {"id": "sem-1", "text": text, "user_id": str(user_id)}

    monkeypatch.setattr(memory_service.semantic, "add", fake_add)

    note = await memory_service.remember(
        "Profile line",
        user_id=5_187_786_663,
        metadata={"source": "telegram"},
    )
    assert calls
    assert calls[0][1] == 5_187_786_663
    assert note["id"] == "sem-1"
