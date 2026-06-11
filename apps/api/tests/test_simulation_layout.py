"""Tests for simulation canvas layout API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_simulation_layout_roundtrip(auth_headers):
    transport = ASGITransport(app=app)
    payload = {
        "custom": {"root-main": {"x": 100, "y": 200}},
        "default": {"root-main": {"x": 100, "y": 200}, "output-memory": {"x": 900, "y": 80}},
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        put = await client.put(
            "/api/agents/simulation-layout",
            json=payload,
            headers=auth_headers,
        )
        assert put.status_code == 200
        saved = put.json()
        assert saved["custom"]["root-main"]["x"] == 100
        assert saved["default"]["output-memory"]["y"] == 80

        get = await client.get("/api/agents/simulation-layout", headers=auth_headers)
        assert get.status_code == 200
        loaded = get.json()
        assert loaded["custom"] == saved["custom"]
        assert loaded["default"] == saved["default"]
