"""
MCP Server Configs
==================
Builds the list of MCP servers the Antigravity main agent should consume.

The agent already has Daffodil's own tools natively (via the tool adapter), so
by default we do NOT re-add Daffodil's own MCP server (avoids duplicate tools).
Instead this wires EXTERNAL MCP servers declared in ``MCP_EXTERNAL_SERVERS``,
plus optionally Daffodil's own stdio server when explicitly requested.

``MCP_EXTERNAL_SERVERS`` format (comma-separated):
    name=command arg1 arg2, other=command ...
e.g.  fs=npx -y @modelcontextprotocol/server-filesystem /tmp
"""

from __future__ import annotations

import logging
import shlex
import sys
from typing import Any, List

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from google.antigravity.types import McpStdioServer
    _AVAILABLE = True
except Exception as e:  # pragma: no cover
    McpStdioServer = None  # type: ignore
    _AVAILABLE = False
    logger.debug(f"Antigravity MCP types unavailable: {e}")


def _parse_external(spec: str) -> List[Any]:
    servers: List[Any] = []
    if not spec or not _AVAILABLE:
        return servers
    for entry in spec.split(","):
        entry = entry.strip()
        if not entry or "=" not in entry:
            continue
        name, command_line = entry.split("=", 1)
        parts = shlex.split(command_line.strip())
        if not parts:
            continue
        command, args = parts[0], parts[1:]
        try:
            servers.append(McpStdioServer(name=name.strip(), command=command, args=args))
        except Exception as e:
            logger.warning(f"Could not build MCP server '{name}': {e}")
    return servers


def daffodil_self_server() -> Any:
    """An McpStdioServer that launches Daffodil's own tool server over stdio."""
    if not _AVAILABLE:
        return None
    return McpStdioServer(
        name="daffodil",
        command=sys.executable,
        args=["-m", "app.mcp.server", "stdio"],
    )


def get_mcp_server_configs(include_self: bool = False) -> List[Any]:
    """Return MCP server configs for the agent to consume."""
    if not settings.MCP_ENABLED or not _AVAILABLE:
        return []
    servers = _parse_external(settings.MCP_EXTERNAL_SERVERS)
    if include_self:
        self_server = daffodil_self_server()
        if self_server is not None:
            servers.append(self_server)
    return servers
