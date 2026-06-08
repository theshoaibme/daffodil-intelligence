"""Chat API integration test (SSE) with the runtime mocked for determinism."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    # Mock the runtime so the chat endpoint is deterministic and offline.
    import app.api.chat as chat_module

    async def fake_stream(message, **kwargs):
        for tok in ["Hello", " ", "world"]:
            yield tok

    async def fake_run(message, **kwargs):
        return {"content": "Hello world", "tool_calls": [], "engine": "antigravity"}

    monkeypatch.setattr(chat_module.orchestrator, "run_stream", fake_stream)
    monkeypatch.setattr(chat_module.orchestrator, "run", fake_run)

    from app.main import app
    with TestClient(app) as c:
        yield c


def test_create_chat_and_stream_message(client):
    # Create a chat (dev mode allows anonymous auth).
    res = client.post("/api/chats/", json={"title": "Test", "agent_type": "supervisor"})
    assert res.status_code == 200, res.text
    chat_id = res.json()["id"]

    # Send a message; response is an SSE stream.
    res = client.post(f"/api/chats/{chat_id}/messages", json={"content": "hi", "metadata": {}})
    assert res.status_code == 200
    body = res.text
    assert "Hello" in body
    assert "[DONE]" in body


def test_health_reports_runtime(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "tools" in data and data["tools"] >= 27


def test_tools_endpoint_lists_registry(client):
    res = client.get("/api/agents/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 27
