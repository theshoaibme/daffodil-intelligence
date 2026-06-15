"""Connections API tests."""

import uuid

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    email = f"conn-test-{uuid.uuid4().hex[:12]}@example.com"
    password = "testpass123"
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Conn Test"},
    )
    assert res.status_code == 200, res.text
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_connections_network_public(client):
    res = client.get("/api/connections/network")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "stats" in data
    assert "researchers" in data["stats"]


def test_request_and_message_connection(client, auth_headers):
    network = client.get("/api/connections/network", headers=auth_headers).json()
    assert network["items"], "expected at least one connection node from research papers"
    target_id = network["items"][0]["id"]

    res = client.post(f"/api/connections/{target_id}/request", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "pending"

    res = client.post(
        f"/api/connections/{target_id}/messages",
        headers=auth_headers,
        json={"body": "Hello there"},
    )
    assert res.status_code == 403

    res = client.post(f"/api/connections/{target_id}/accept", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "connected"

    res = client.post(
        f"/api/connections/{target_id}/messages",
        headers=auth_headers,
        json={
            "body": "I would like to discuss shared research interests.",
            "message_type": "chat",
        },
    )
    assert res.status_code == 201
    created = res.json()
    assert len(created) == 2
    assert created[0]["direction"] == "outgoing"
    assert created[1]["direction"] == "incoming"

    res = client.get(f"/api/connections/{target_id}/messages", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2

    res = client.get("/api/connections/conversations", headers=auth_headers)
    assert res.status_code == 200
    conversations = res.json()
    assert any(item["target_id"] == target_id for item in conversations)

    summary = client.get("/api/connections/me/summary", headers=auth_headers).json()
    assert summary["connected"] >= 1
