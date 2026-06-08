"""MCP server + config wiring tests."""

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


async def test_client_execute_tool_via_registry():
    res = await execute_tool("get_cgpa", student_id="221-15-1234")
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
