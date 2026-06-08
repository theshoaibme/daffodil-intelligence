"""Unified memory tests (semantic store + service)."""

import pytest

from app.memory.semantic import SemanticMemory
from app.memory import memory_service


def test_semantic_add_and_search():
    mem = SemanticMemory()
    mem.clear()
    mem.add("The exam is on May 20 in room A-301", user_id=7)
    mem.add("User prefers replies in Bangla", user_id=7)
    mem.add("Unrelated note about pizza", user_id=7)

    hits = mem.search("when is the exam", user_id=7, k=3)
    assert hits
    assert any("exam" in h["text"].lower() for h in hits)


def test_semantic_user_scoping():
    mem = SemanticMemory()
    mem.clear()
    mem.add("user one secret", user_id=1)
    mem.add("user two secret", user_id=2)
    assert all(h["user_id"] == "1" for h in mem.search("secret", user_id=1, k=5))


async def test_memory_service_history_mock():
    # Without a real DB this returns [] gracefully (mock store).
    history = await memory_service.get_history(99999, limit=10)
    assert isinstance(history, list)


def test_memory_service_remember_recall():
    note = memory_service.remember("Capstone deadline is June 30", user_id=42)
    assert note["id"]
    found = memory_service.recall("capstone deadline", user_id=42, k=3)
    assert any("capstone" in n["text"].lower() for n in found)
