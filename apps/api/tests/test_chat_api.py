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
        return {"content": "Hello world", "tool_calls": [], "engine": "antigravity", "agent_id": "main"}

    monkeypatch.setattr(chat_module, "run_turn_stream", fake_stream)
    monkeypatch.setattr(chat_module, "run_turn", fake_run)

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


def test_health_returns_html(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Server is healthy" in res.text
    assert "healthy" in res.text.lower()


def test_agents_list_from_registry(client):
    res = client.get("/api/agents/list")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 20
    assert any(a["id"] == "academic" for a in data["agents"])


def test_swagger_docs_default_ui(client):
    res = client.get("/docs")
    assert res.status_code == 200
    html = res.text
    assert "swagger-ui-dist" in html
    assert "swagger-ui.css" in html
    assert "SwaggerUIBundle" in html
    assert "/static/docs-theme.css" not in html


def test_tools_endpoint_lists_registry(client):
    res = client.get("/api/agents/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 27
