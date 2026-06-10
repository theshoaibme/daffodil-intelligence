"""
Tool Adapter
============
Bridges the Daffodil ``BaseTool`` registry to the Google Antigravity SDK.

Antigravity consumes plain Python callables (optionally wrapped with
``ToolWithSchema`` to attach an explicit JSON Schema). Each ``BaseTool`` in
``app.tools.registry`` already produces an MCP-style JSON Schema, so we wrap a
thin async executor with that schema and hand it to the agent. This means the
15+ existing tools become Antigravity tools with zero rewrites.
"""

import json
import logging
from typing import Any, Callable, List, Optional

from ..tools.registry import get_registry
from ..tools.base import BaseTool

logger = logging.getLogger(__name__)

try:
    from google.antigravity.tools.tool_runner import ToolWithSchema
    _ANTIGRAVITY_AVAILABLE = True
except Exception as e:  # pragma: no cover - import guard
    ToolWithSchema = None  # type: ignore
    _ANTIGRAVITY_AVAILABLE = False
    logger.warning(f"Antigravity tool runner unavailable: {e}")


def _serialize(result_data: Any) -> str:
    """Serialize a tool result payload to a string the model can read."""
    if isinstance(result_data, str):
        return result_data
    try:
        return json.dumps(result_data, ensure_ascii=False, default=str)
    except Exception:
        return str(result_data)


def _make_callable(tool: BaseTool) -> Callable[..., Any]:
    """Create an async callable that runs a single registry tool by name."""
    registry = get_registry()
    tool_name = tool.name

    async def _runner(**kwargs: Any) -> str:
        from .task_events import stash_pending_tool_events, take_nested_events

        take_nested_events()
        result = await registry.execute(tool_name, **kwargs)
        nested = take_nested_events()
        if nested:
            stash_pending_tool_events(nested)
        if result.success:
            return _serialize(result.data)
        return f"ERROR ({tool_name}): {result.error}"

    _runner.__name__ = tool_name
    _runner.__doc__ = tool.description or tool_name
    return _runner


def _input_schema(tool: BaseTool) -> dict:
    """Return a JSON Schema object for the tool's parameters."""
    schema = tool.get_schema()
    return schema.get("inputSchema", {"type": "object", "properties": {}, "required": []})


def adapt_tool(tool: BaseTool):
    """Adapt a single ``BaseTool`` into an Antigravity tool."""
    fn = _make_callable(tool)
    if _ANTIGRAVITY_AVAILABLE and ToolWithSchema is not None:
        return ToolWithSchema(fn, _input_schema(tool))
    return fn


def get_antigravity_tools(
    categories: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
) -> List[Any]:
    """Return Antigravity-ready tools from the registry.

    Args:
        categories: If provided, only include tools in these categories.
        exclude: Tool names to skip.
        include: If provided, only these tool names are exposed (skills overlay).

    Returns:
        A list of Antigravity tool callables/wrappers.
    """
    registry = get_registry()
    exclude = set(exclude or [])
    include_set = set(include) if include else None
    tools: List[Any] = []
    for schema in registry.list_all():
        name = schema["name"]
        if name in exclude:
            continue
        if include_set is not None and name not in include_set:
            continue
        if categories is not None and schema.get("category") not in categories:
            continue
        base_tool = registry.get(name)
        if base_tool is None:
            continue
        tools.append(adapt_tool(base_tool))
    logger.info(f"Adapted {len(tools)} tools for Antigravity (categories={categories})")
    return tools


def list_tool_names(categories: Optional[List[str]] = None) -> List[str]:
    """List registry tool names, optionally filtered by category."""
    registry = get_registry()
    names = []
    for schema in registry.list_all():
        if categories is not None and schema.get("category") not in categories:
            continue
        names.append(schema["name"])
    return names
