"""
MCP Server Configs
==================
Builds the list of MCP servers the Antigravity main agent should consume.

Delegates parsing and materialization to :class:`McpBuilder`.
"""

from __future__ import annotations

from typing import Any, List

from .builder import McpBuilder, antigravity_mcp_available

# Backwards-compatible alias used by health checks and tests.
_AVAILABLE = antigravity_mcp_available()


def daffodil_self_server() -> Any:
    """An McpStdioServer that launches Daffodil's own tool server over stdio."""
    if not _AVAILABLE:
        return None
    return McpBuilder.to_antigravity_server(McpBuilder.daffodil_self_spec())


def get_mcp_server_configs(include_self: bool = False) -> List[Any]:
    """Return MCP server configs for the agent to consume."""
    return McpBuilder.build_antigravity_servers(include_self=include_self)
