"""MCP builder, probe, and API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mcp.builder import McpBuilder, McpProbe, get_local_tool_catalog, mcp_sdk_available
from app.mcp.protocol import McpTransport
from app.mcp.servers import daffodil_self_server, get_mcp_server_configs
from app.tools.registry import get_registry


# ---------------------------------------------------------------------------
# Parsing & validation
# ---------------------------------------------------------------------------


def test_parse_entry_stdio_server():
    spec = McpBuilder.parse_entry("fs=npx -y @modelcontextprotocol/server-filesystem /tmp")
    assert spec is not None
    assert spec.name == "fs"
    assert spec.command == "npx"
    assert "-y" in spec.args
    assert spec.transport == McpTransport.STDIO


def test_parse_external_spec_multiple():
    raw = "a=echo hello, b=python -m app.mcp.server stdio"
    specs = McpBuilder.parse_external_spec(raw)
    assert len(specs) == 2
    assert specs[0].name == "a"
    assert specs[1].name == "b"


def test_parse_entry_invalid_returns_none():
    assert McpBuilder.parse_entry("") is None
    assert McpBuilder.parse_entry("noequals") is None
    assert McpBuilder.parse_entry("name=") is None


def test_from_name_command():
    spec = McpBuilder.from_name_command("daffodil", "python -m app.mcp.server stdio")
    assert spec.name == "daffodil"
    assert spec.command == "python"
    assert spec.args[-1] == "stdio"


def test_validate_rejects_empty_name():
    from app.mcp.protocol import McpServerSpec

    result = McpBuilder.validate(McpServerSpec(name="", command="echo"))
    assert not result.valid
    assert "name is required" in result.errors[0]


def test_validate_accepts_valid_stdio():
    spec = McpBuilder.daffodil_self_spec()
    result = McpBuilder.validate(spec)
    assert result.valid
    assert result.errors == []


def test_serialize_roundtrip():
    specs = [
        McpBuilder.from_name_command("fs", "npx -y @mcp/server-filesystem /tmp"),
        McpBuilder.daffodil_self_spec(),
    ]
    serialized = McpBuilder.serialize_specs(specs)
    reparsed = McpBuilder.parse_external_spec(serialized)
    assert len(reparsed) == 2
    assert reparsed[0].name == "fs"
    assert reparsed[1].name == "daffodil"


def test_to_stdio_parameters():
    if not mcp_sdk_available():
        pytest.skip("mcp SDK not installed")
    spec = McpBuilder.daffodil_self_spec()
    params = McpBuilder.to_stdio_parameters(spec)
    assert params.command == spec.command
    assert params.args == spec.args


# ---------------------------------------------------------------------------
# Status & wiring
# ---------------------------------------------------------------------------


def test_status_detail_includes_local_tools():
    detail = McpBuilder.status_detail()
    assert detail.local_tool_count == get_registry().count
    assert detail.sdk_available == mcp_sdk_available()


def test_get_configured_specs_respects_env(monkeypatch):
    monkeypatch.setenv("MCP_EXTERNAL_SERVERS", "echo_srv=echo mcp-test")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        specs = McpBuilder.get_configured_specs()
        assert len(specs) == 1
        assert specs[0].name == "echo_srv"
    finally:
        monkeypatch.delenv("MCP_EXTERNAL_SERVERS", raising=False)
        get_settings.cache_clear()


def test_external_configs_default_empty():
    assert get_mcp_server_configs() == []


def test_self_server_config():
    cfg = daffodil_self_server()
    if cfg is not None:
        assert cfg.name == "daffodil"


def test_local_catalog_matches_registry():
    catalog = get_local_tool_catalog()
    assert len(catalog) == get_registry().count
    names = {t["name"] for t in catalog}
    assert "get_cgpa" in names


# ---------------------------------------------------------------------------
# Live probe (official mcp ClientSession over stdio)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_probe_self_server():
    if not mcp_sdk_available():
        pytest.skip("mcp SDK not installed")

    result = await McpProbe.test_self(timeout_seconds=30.0)
    assert result.success, result.error
    assert result.tool_count >= get_registry().count
    assert result.protocol_version
    assert result.latency_ms > 0
    assert "get_cgpa" in result.tools


@pytest.mark.asyncio
async def test_probe_invalid_command_fails():
    if not mcp_sdk_available():
        pytest.skip("mcp SDK not installed")

    from app.mcp.protocol import McpServerSpec

    bad = McpServerSpec(name="bad", command="/nonexistent/mcp-server-binary", args=[])
    result = await McpProbe.test_stdio(bad, timeout_seconds=5.0)
    assert not result.success
    assert result.error


# ---------------------------------------------------------------------------
# HTTP API
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_status(client):
    res = client.get("/api/mcp/status")
    assert res.status_code == 200
    data = res.json()
    assert "sdk_available" in data
    assert "local_tool_count" in data
    assert data["local_tool_count"] == get_registry().count


def test_api_catalog(client):
    res = client.get("/api/mcp/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == get_registry().count
    assert any(t["name"] == "get_cgpa" for t in data["tools"])


def test_api_parse_valid(client):
    res = client.post(
        "/api/mcp/parse",
        json={"entry": "fs=npx -y @modelcontextprotocol/server-filesystem /tmp"},
    )
    assert res.status_code == 200
    assert res.json()["spec"]["name"] == "fs"
    assert res.json()["validation"]["valid"] is True


def test_api_parse_invalid(client):
    res = client.post("/api/mcp/parse", json={"entry": "not-valid"})
    assert res.status_code == 400


def test_api_validate(client):
    res = client.post(
        "/api/mcp/validate",
        json={"name": "daffodil", "command": "python -m app.mcp.server stdio"},
    )
    assert res.status_code == 200
    assert res.json()["valid"] is True


@pytest.mark.asyncio
async def test_api_test_self(client):
    if not mcp_sdk_available():
        pytest.skip("mcp SDK not installed")

    res = client.post("/api/mcp/test", json={"test_self": True, "timeout_seconds": 30})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["tool_count"] >= get_registry().count
