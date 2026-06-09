"""
MCP Client (compatibility shim)
==============================
Historically this module held a hard-coded tool catalogue and an HTTP client
pointed at the wrong port. It is now a thin compatibility layer backed by the
real ``ToolRegistry`` so existing imports keep working while pointing at live
tools.

  - ``TOOL_REGISTRY``        : name -> {description, params} built from registry
  - ``execute_tool(name,..)``: executes via the registry
  - ``mcp_client``           : exposes ``registry`` count + no-op ``close()``
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ..tools.registry import get_registry

logger = logging.getLogger(__name__)


def _build_catalog() -> Dict[str, Dict[str, Any]]:
    registry = get_registry()
    catalog: Dict[str, Dict[str, Any]] = {}
    for schema in registry.list_all():
        props = schema.get("inputSchema", {}).get("properties", {})
        catalog[schema["name"]] = {
            "description": schema.get("description", ""),
            "params": list(props.keys()),
            "category": schema.get("category", "general"),
        }
    return catalog


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = _build_catalog()


async def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool by name via the real registry."""
    registry = get_registry()
    result = await registry.execute(tool_name, **kwargs)
    if result.success:
        return {"success": True, "data": result.data, "tool": tool_name}
    return {"success": False, "error": result.error, "tool": tool_name}


class _MCPClientShim:
    """Backwards-compatible stand-in for the old HTTP MCP client."""

    @property
    def registry(self) -> Dict[str, Dict[str, Any]]:
        return TOOL_REGISTRY

    async def get_tools(self):
        return get_registry().list_all()

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any] | None = None):
        return await execute_tool(tool_name, **(arguments or {}))

    async def close(self):
        return None


mcp_client = _MCPClientShim()
