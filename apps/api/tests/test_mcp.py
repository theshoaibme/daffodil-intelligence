"""MCP server + config wiring tests."""

from app.mcp import McpBuilder, get_local_tool_catalog
from app.mcp.server import get_mcp_server, create_mcp_server
from app.mcp.servers import get_mcp_server_configs, daffodil_self_server
from app.mcp.client import TOOL_REGISTRY, execute_tool


def test_mcp_server_builds_with_all_tools():
    server = get_mcp_server()
    assert server is not None  # mcp SDK installed


def test_client_catalog_matches_registry():
    from app.tools.registry import get_registry
    assert len(TOOL_REGISTRY) == get_registry().count
    assert "get_cgpa" in TOOL_REGISTRY


def test_client_execute_tool_via_registry():
    from tests.conftest import run_async
    from app.mcp.client import execute_tool

    async def _run():
        return await execute_tool("get_cgpa", student_id="221-15-1234")

    res = run_async(_run())
    assert res["success"]
    assert "cgpa" in res["data"]


def test_external_configs_default_empty():
    # No MCP_EXTERNAL_SERVERS set -> no external servers.
    assert get_mcp_server_configs() == []


def test_self_server_config():
    cfg = daffodil_self_server()
    # Available when the Antigravity SDK is installed.
    if cfg is not None:
        assert cfg.name == "daffodil"


def test_builder_self_spec_matches_server_module():
    spec = McpBuilder.daffodil_self_spec()
    assert spec.name == "daffodil"
    assert spec.args[-1] == "stdio"


def test_local_catalog_via_package():
    assert len(get_local_tool_catalog()) == len(TOOL_REGISTRY)
