"""
MCP package — server, client shim, builder, and protocol models.

Imports are lazy so ``python -m app.mcp.server`` stays lightweight in subprocesses.
"""

from .builder import (
    McpBuilder,
    McpProbe,
    antigravity_mcp_available,
    get_local_tool_catalog,
    mcp_sdk_available,
)
from .protocol import (
    McpServerSpec,
    McpServerTestResult,
    McpStatusDetail,
    McpToolInfo,
    McpTransport,
    McpValidationResult,
)

__all__ = [
    "McpBuilder",
    "McpProbe",
    "McpServerSpec",
    "McpServerTestResult",
    "McpStatusDetail",
    "McpToolInfo",
    "McpTransport",
    "McpValidationResult",
    "TOOL_REGISTRY",
    "antigravity_mcp_available",
    "create_mcp_server",
    "daffodil_self_server",
    "execute_tool",
    "get_local_tool_catalog",
    "get_mcp_server",
    "get_mcp_server_configs",
    "mcp_client",
    "mcp_sdk_available",
    "run",
]


def __getattr__(name: str):
    if name in ("TOOL_REGISTRY", "execute_tool", "mcp_client"):
        from .client import TOOL_REGISTRY, execute_tool, mcp_client

        return {"TOOL_REGISTRY": TOOL_REGISTRY, "execute_tool": execute_tool, "mcp_client": mcp_client}[name]
    if name in ("create_mcp_server", "get_mcp_server", "run"):
        from .server import create_mcp_server, get_mcp_server, run

        return {"create_mcp_server": create_mcp_server, "get_mcp_server": get_mcp_server, "run": run}[name]
    if name in ("daffodil_self_server", "get_mcp_server_configs"):
        from .servers import daffodil_self_server, get_mcp_server_configs

        return {
            "daffodil_self_server": daffodil_self_server,
            "get_mcp_server_configs": get_mcp_server_configs,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
