"""
MCP v2 Server
=============
Exposes all registered tools via the Model Context Protocol v2.
Uses the official `mcp` Python SDK (installed via google-antigravity).

The server runs on :8001 and is used by agents to discover and execute tools.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("mcp package not available")


def create_mcp_server():
    """Create and configure the MCP server with all registered tools."""
    if not MCP_AVAILABLE:
        logger.error("MCP SDK not installed. Run: pip install mcp")
        return None

    mcp = FastMCP(
        name="Daffodil Intelligence Tool Server",
        version="2.0.0",
        instructions=(
            "This is the Daffodil Intelligence tool server. "
            "It provides access to computer control, file system, "
            "web browser, shell execution, and domain-specific tools."
        ),
    )

    # Register all tools from the tool registry
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

            # Create a closure to capture tool_name
            def make_executor(name: str):
                async def tool_executor(**kwargs: Any) -> str:
                    result = await registry.execute(name, **kwargs)
                    if result.success:
                        import json
                        return json.dumps(result.data, ensure_ascii=False, default=str)
                    else:
                        return f"ERROR: {result.error}"
                tool_executor.__name__ = name
                tool_executor.__doc__ = tool_description
                return tool_executor

            executor = make_executor(tool_name)
            # Register with MCP
            mcp.tool(name=tool_name, description=tool_description)(executor)

        logger.info(f"MCP server registered {registry.count} tools")

    except Exception as e:
        logger.error(f"Failed to register tools with MCP: {e}")


# Singleton MCP server instance
_mcp_server = None


def get_mcp_server():
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server
