"""Tests for unified memory repository and types."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.memory.repository import MemoryRepository
from app.memory.types import compute_content_hash, resolve_scope, canonical_embed_text


def test_compute_content_hash_stable():
    h1 = compute_content_hash("fact", "main", "hello", {"a": 1})
    h2 = compute_content_hash("fact", "main", "hello", {"a": 1})
    h3 = compute_content_hash("fact", "main", "world", {"a": 1})
    assert h1 == h2
    assert h1 != h3


def test_resolve_scope():
    assert resolve_scope("main") == "root"
    assert resolve_scope("academic") == "agent"
    assert resolve_scope("sub-1", parent_agent_id="main") == "subagent"


def test_canonical_embed_text():
    text = canonical_embed_text("skill", "Movie picker", {"name": "Movies"})
    assert "[skill]" in text
    assert "Movie picker" in text


def test_tool_definition_hash_matches_stored_content():
    content = "web_search: Search the web"
    payload = {
        "tool_name": "web_search",
        "description": "Search the web",
        "parameters": {"type": "object"},
        "category": "browser",
    }
    h1 = compute_content_hash("tool_definition", "main", content, payload)
    h2 = compute_content_hash("tool_definition", "main", content, payload)
    assert h1 == h2

    buggy_hash = compute_content_hash("tool_definition", "main", "web_search", {"name": "web_search"})
    assert h1 != buggy_hash


def test_mcp_server_hash_matches_stored_content():
    content = "MCP server: local-tools"
    payload = {"server_name": "local-tools", "transport": "stdio", "tools": []}
    h1 = compute_content_hash("mcp_server", "main", content, payload)
    h2 = compute_content_hash("mcp_server", "main", content, payload)
    assert h1 == h2

    buggy_hash = compute_content_hash("mcp_server", "main", "local-tools", payload)
    assert h1 != buggy_hash


@pytest.mark.asyncio
async def test_new_memory_qdrant_has_memory_id(monkeypatch):
    upsert_payloads = []

    async def capture_upsert(point_id, text, payload):
        upsert_payloads.append(payload)
        return point_id

    monkeypatch.setattr("app.memory.repository.qdrant_store.upsert", capture_upsert)

    session = MagicMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    added_rows = []

    def fake_add(row):
        row.id = "pg-mem-123"
        added_rows.append(row)

    session.add = fake_add
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    repo = MemoryRepository(session)
    await repo.upsert(
        user_id=1,
        agent_id="main",
        content="User prefers concise answers",
        memory_type="fact",
    )

    assert len(upsert_payloads) == 1
    assert upsert_payloads[0]["memory_id"] == "pg-mem-123"
    assert len(added_rows) == 1
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_filtered_clear_deletes_qdrant_points(monkeypatch):
    deleted_points = []

    def capture_delete_many(point_ids):
        deleted_points.extend(point_ids)

    monkeypatch.setattr("app.memory.repository.qdrant_store.delete_many", capture_delete_many)

    row1 = MagicMock()
    row1.qdrant_point_id = "point-a"
    row2 = MagicMock()
    row2.qdrant_point_id = "point-b"
    row3 = MagicMock()
    row3.qdrant_point_id = None

    select_result = MagicMock()
    select_result.scalars.return_value.all.return_value = [row1, row2, row3]

    delete_result = MagicMock()
    delete_result.rowcount = 2

    session = MagicMock()
    session.execute = AsyncMock(side_effect=[select_result, delete_result])
    session.commit = AsyncMock()

    repo = MemoryRepository(session)
    count = await repo.clear(1, memory_type="fact")

    assert count == 2
    assert deleted_points == ["point-a", "point-b"]
    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_memory_service_remember_recall_mock():
    from app.memory import memory_service

    note = await memory_service.remember("Test fact about exams", user_id=99, memory_type="fact")
    assert note.get("id") or note.get("text")
    found = await memory_service.recall("exams", user_id=99, k=3)
    assert isinstance(found, list)
