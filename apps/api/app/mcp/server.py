"""
MCP Server
==========
Exposes every tool in the Daffodil ``ToolRegistry`` over the Model Context
Protocol so external clients (other agents, Cursor, the Antigravity runtime,
etc.) can discover and call them.

Run standalone:
    python -m app.mcp.server            # stdio (default)
    python -m app.mcp.server http       # streamable-http on MCP_SERVER_PORT
"""

import json
import logging
import sys
from typing import Any

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    FastMCP = None  # type: ignore
    MCP_AVAILABLE = False
    logger.warning("mcp package not available")


def create_mcp_server():
    """Create and configure the MCP server with all registered tools."""
    if not MCP_AVAILABLE:
        logger.error("MCP SDK not installed. Run: pip install mcp")
        return None

    mcp = FastMCP(
        name="Daffodil Intelligence Tool Server",
        instructions=(
            "Daffodil Intelligence tool server. Provides computer control, "
            "file system, web browser, shell execution, university data and "
            "memory tools."
        ),
        host="0.0.0.0",
        port=settings.MCP_SERVER_PORT,
    )

    _register_tools_with_mcp(mcp)
    return mcp


def _register_tools_with_mcp(mcp):
    """Register every tool in the ToolRegistry as an MCP tool."""
    try:
        from ..tools.registry import get_registry
        registry = get_registry()

        for tool_schema in registry.list_all():
            tool_name = tool_schema["name"]
            tool_description = tool_schema["description"]

            def make_executor(name: str):
                async def tool_executor(**kwargs: Any) -> str:
                    result = await registry.execute(name, **kwargs)
                    if result.success:
                        return json.dumps(result.data, ensure_ascii=False, default=str)
                    return f"ERROR: {result.error}"
                tool_executor.__name__ = name
                tool_executor.__doc__ = tool_description
                return tool_executor

            executor = make_executor(tool_name)
            mcp.tool(name=tool_name, description=tool_description)(executor)

        logger.info(f"MCP server registered {registry.count} tools")
    except Exception as e:
        logger.error(f"Failed to register tools with MCP: {e}")


_mcp_server = None


def get_mcp_server():
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


def run(transport: str = "stdio"):
    """Run the MCP server with the given transport ('stdio' or 'http')."""
    server = get_mcp_server()
    if server is None:
        raise RuntimeError("MCP SDK not available")
    sdk_transport = "streamable-http" if transport in ("http", "streamable-http") else "stdio"
    logger.info(f"Starting Daffodil MCP server (transport={sdk_transport})")
    server.run(transport=sdk_transport)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else settings.MCP_TRANSPORT
    run(arg)
