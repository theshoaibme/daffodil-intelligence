"""MCP orchestration integration tests — server, agent wiring, pipeline, accuracy."""

from __future__ import annotations

from typing import Any, Dict, List, Set
from unittest.mock import patch

import pytest

from app.mcp.builder import McpBuilder, McpProbe, get_local_tool_catalog, mcp_sdk_available
from app.mcp.server import create_mcp_server, get_mcp_server, reset_mcp_server
from app.tools.registry import get_registry
from tests.conftest import run_async


pytestmark = pytest.mark.skipif(not mcp_sdk_available(), reason="MCP SDK not installed")


# ---------------------------------------------------------------------------
# Server ↔ registry parity (100% tool coverage)
# ---------------------------------------------------------------------------


class TestMcpServerRegistryParity:
    """Every registry tool must appear on the live MCP server."""

    @pytest.fixture(autouse=True)
    def _fresh_server(self):
        reset_mcp_server()
        yield
        reset_mcp_server()

    def test_server_builds_non_null(self):
        assert create_mcp_server() is not None

    def test_registered_tool_count_matches_registry(self):
        server = get_mcp_server()
        assert server is not None
        tools = run_async(server.list_tools())
        registry_names = {t["name"] for t in get_registry().list_all()}
        mcp_names = {t.name for t in tools}
        assert len(mcp_names) == len(registry_names)
        assert mcp_names == registry_names

    def test_catalog_matches_registry_exactly(self):
        catalog = get_local_tool_catalog()
        registry = get_registry().list_all()
        assert len(catalog) == len(registry)
        assert {t["name"] for t in catalog} == {t["name"] for t in registry}

    @pytest.mark.parametrize(
        "required_tool",
        [
            "get_class_routine",
            "create_reminder",
            "send_telegram_message",
            "enable_routine_automation",
            "invoke_agent",
            "list_agents",
            "get_cgpa",
            "store_note",
            "recall_notes",
        ],
    )
    def test_automation_and_orchestration_tools_exposed(self, required_tool):
        server = get_mcp_server()
        tools = run_async(server.list_tools())
        names = {t.name for t in tools}
        assert required_tool in names


class TestMcpLiveProbe:
    """End-to-end stdio probe against the self-hosted MCP server."""

    @pytest.fixture(autouse=True)
    def _fresh_server(self):
        reset_mcp_server()
        yield
        reset_mcp_server()

    def test_probe_self_server_lists_all_tools(self):
        registry_count = get_registry().count
        result = run_async(McpProbe.test_self(timeout_seconds=45.0))
        assert result.success, result.error
        assert result.tool_count == registry_count
        assert result.protocol_version
        assert result.latency_ms > 0

    def test_probe_tools_match_registry(self):
        registry_names = {t["name"] for t in get_registry().list_all()}
        result = run_async(McpProbe.test_stdio(
            McpBuilder.daffodil_self_spec(),
            timeout_seconds=45.0,
            max_tools=200,
        ))
        assert set(result.tools) == registry_names


class TestMcpClientExecution:
    """Registry shim executes tools the same path MCP server uses."""

    def test_execute_get_cgpa(self):
        from app.mcp.client import execute_tool

        async def _run():
            return await execute_tool("get_cgpa", student_id="221-15-1234")

        res = run_async(_run())
        assert res["success"]
        assert "cgpa" in res["data"]

    def test_execute_list_agents(self):
        from app.mcp.client import execute_tool

        async def _run():
            return await execute_tool("list_agents")

        res = run_async(_run())
        assert res["success"]
        assert res["data"]["count"] >= 10


# ---------------------------------------------------------------------------
# Agent orchestration wiring
# ---------------------------------------------------------------------------


class TestMcpAgentOrchestration:
    """MCP is wired into pipeline, routine turns, and agent factory."""

    def test_routine_turn_enables_mcp_mode(self, monkeypatch):
        from app.automation.routine_mcp import ensure_mcp_in_metadata, routine_turn
        from app.core.config import get_settings

        monkeypatch.setattr(get_settings(), "MCP_ENABLED", True)
        msg = "Set up Telegram notifications for my class routine tomorrow"
        assert routine_turn(msg) is True
        meta = ensure_mcp_in_metadata({"selected_tools": ["Agent"]}, msg)
        assert "MCP" in meta["selected_tools"]

    def test_merge_invoke_metadata_for_routine_agent(self, monkeypatch):
        from app.automation.routine_mcp import merge_invoke_metadata
        from app.core.config import get_settings

        monkeypatch.setattr(get_settings(), "MCP_ENABLED", True)
        meta = merge_invoke_metadata("routine", "class routine Monday", user_id=7)
        assert "MCP" in meta.get("selected_tools", [])
        assert "Agent" in meta.get("selected_tools", [])

    def test_agent_factory_wires_mcp_when_mode_selected(self, monkeypatch):
        from app.runtime.agent_factory import _get_mcp_servers
        from app.runtime.tool_context import clear_turn_context, set_turn_context

        monkeypatch.setenv("MCP_ENABLED", "true")
        from app.core.config import get_settings

        get_settings.cache_clear()
        set_turn_context(user_id=1, selected_tools=["MCP", "Agent"])
        try:
            with patch("app.mcp.builder.antigravity_mcp_available", return_value=True), patch(
                "app.mcp.builder.McpBuilder.build_antigravity_servers",
                return_value=[{"name": "daffodil"}],
            ):
                servers = _get_mcp_servers()
            assert len(servers) >= 1
        finally:
            clear_turn_context()
            get_settings.cache_clear()

    def test_agent_factory_skips_mcp_when_disabled(self, monkeypatch):
        from app.runtime.agent_factory import _get_mcp_servers
        from app.runtime.tool_context import clear_turn_context, set_turn_context

        monkeypatch.setenv("MCP_ENABLED", "false")
        from app.core.config import get_settings

        get_settings.cache_clear()
        set_turn_context(user_id=1, selected_tools=["MCP"])
        try:
            assert _get_mcp_servers() == []
        finally:
            clear_turn_context()
            get_settings.cache_clear()

    def test_pipeline_resolves_mcp_specs_from_metadata(self):
        pytest.importorskip("langchain")
        from app.runtime.pipeline import _resolve_turn_mcp_specs

        meta = {
            "mcp_servers": [
                {"name": "daffodil", "command": "python -m app.mcp.server stdio"},
            ]
        }
        specs = _resolve_turn_mcp_specs(meta)
        assert len(specs) == 1
        assert specs[0].name == "daffodil"


class TestMcpBuilderAccuracy:
    """Builder parse/validate/serialize must be exact."""

    def test_daffodil_self_spec_uses_current_interpreter(self):
        import sys

        spec = McpBuilder.daffodil_self_spec()
        assert spec.name == "daffodil"
        assert spec.command == sys.executable
        assert spec.args == ["-m", "app.mcp.server", "stdio"]

    def test_status_detail_reports_registry_count(self):
        detail = McpBuilder.status_detail()
        assert detail.local_tool_count == get_registry().count
        assert detail.sdk_available is True

    def test_external_spec_roundtrip(self):
        raw = "fs=npx -y @modelcontextprotocol/server-filesystem /tmp"
        specs = McpBuilder.parse_external_spec(raw)
        reserialized = McpBuilder.serialize_specs(specs)
        reparsed = McpBuilder.parse_external_spec(reserialized)
        assert reparsed[0].name == specs[0].name
        assert reparsed[0].command == specs[0].command


class TestMcpOrchestrationReport:
    """Single aggregate check — all integration surfaces aligned."""

    def test_full_mcp_integration_matrix(self):
        reset_mcp_server()
        registry: Set[str] = {t["name"] for t in get_registry().list_all()}
        catalog: Set[str] = {t["name"] for t in get_local_tool_catalog()}
        server = get_mcp_server()
        mcp_tools: Set[str] = {t.name for t in run_async(server.list_tools())}
        probe = run_async(McpProbe.test_stdio(
            McpBuilder.daffodil_self_spec(),
            timeout_seconds=45.0,
            max_tools=200,
        ))

        assert registry == catalog == mcp_tools == set(probe.tools)
        assert probe.success
        assert len(registry) >= 50
        reset_mcp_server()
