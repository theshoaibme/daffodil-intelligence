"""Agent hub API tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "1", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


def test_hub_list_includes_builtins(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.core.database._use_mock", True)

    res = client.get("/api/agents/hub", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    kinds = {a["kind"] for a in data["agents"]}
    assert "builtin" in kinds
