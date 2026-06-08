"""Memory agent tools tests."""

import pytest

from app.tools.memory.store import StoreNoteTool, RecallNotesTool, ListMemoriesTool


@pytest.mark.asyncio
async def test_store_note_tool():
    tool = StoreNoteTool()
    result = await tool.execute(text="Favorite color is blue", user_id="7", tag="preference")
    assert result.success
    assert result.data["stored"] is True


@pytest.mark.asyncio
async def test_recall_notes_tool():
    store = StoreNoteTool()
    await store.execute(text="Exam room is A-301", user_id="8")

    recall = RecallNotesTool()
    result = await recall.execute(query="exam room", user_id="8", k=3)
    assert result.success
    assert result.data["count"] >= 0


@pytest.mark.asyncio
async def test_list_memories_tool(monkeypatch):
    async def fake_list(user_id, **kwargs):
        return {"items": [{"id": "1", "content": "test"}], "total": 1}

    monkeypatch.setattr(
        "app.tools.memory.store.memory_service.list_memories",
        fake_list,
    )
    tool = ListMemoriesTool()
    result = await tool.execute(user_id="9", limit=5)
    assert result.success
    assert result.data["total"] == 1
