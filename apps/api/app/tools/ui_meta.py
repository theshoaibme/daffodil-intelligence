"""UI metadata for tool → card rendering on the frontend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolUiMeta:
    tool_name: str
    card_type: str
    widget_type: str
    icon: str = "wrench"
    streaming: bool = False
    input_schema: Dict[str, Any] = field(default_factory=dict)
    result_schema: Dict[str, Any] = field(default_factory=dict)


# Built-in tool → UI mappings
BUILTIN_TOOL_UI: Dict[str, ToolUiMeta] = {
    "google_search": ToolUiMeta(
        tool_name="google_search",
        card_type="search",
        widget_type="search_results",
        icon="search",
    ),
    "web_search": ToolUiMeta(
        tool_name="web_search",
        card_type="search",
        widget_type="search_results",
        icon="search",
    ),
    "browser_navigate": ToolUiMeta(
        tool_name="browser_navigate",
        card_type="browser",
        widget_type="browser_session",
        icon="globe",
        streaming=True,
    ),
    "shell_execute": ToolUiMeta(
        tool_name="shell_execute",
        card_type="terminal",
        widget_type="terminal_output",
        icon="terminal",
    ),
    "read_file": ToolUiMeta(
        tool_name="read_file",
        card_type="file",
        widget_type="file_preview",
        icon="file",
    ),
    "write_file": ToolUiMeta(
        tool_name="write_file",
        card_type="file",
        widget_type="file_preview",
        icon="file",
    ),
    "generate_image": ToolUiMeta(
        tool_name="generate_image",
        card_type="image",
        widget_type="image_gallery",
        icon="image",
    ),
    "execute_code": ToolUiMeta(
        tool_name="execute_code",
        card_type="code",
        widget_type="code_viewer",
        icon="code",
    ),
}


def infer_ui_meta_from_schema(tool_name: str, schema: Dict[str, Any]) -> ToolUiMeta:
    """Heuristic UI meta inference for MCP-discovered tools."""
    props = (schema.get("inputSchema") or schema.get("properties") or {})
    if isinstance(props, dict) and "properties" in props:
        props = props["properties"]
    prop_keys = set(props.keys()) if isinstance(props, dict) else set()
    name_lower = tool_name.lower()

    if "query" in prop_keys or "search" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="search", widget_type="search_results", icon="search")
    if "url" in prop_keys or "browser" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="browser", widget_type="browser_session", icon="globe", streaming=True)
    if "sql" in prop_keys or "query" in name_lower and "database" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="database", widget_type="table_viewer", icon="database")
    if "path" in prop_keys or "file" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="file", widget_type="file_preview", icon="file")
    if "image" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="image", widget_type="image_gallery", icon="image")
    if "chart" in name_lower or "plot" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="chart", widget_type="chart_viewer", icon="chart")
    if "map" in name_lower or "location" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="map", widget_type="map_viewer", icon="map")
    if "email" in name_lower or "mail" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="email", widget_type="email_preview", icon="mail")
    if "calendar" in name_lower or "event" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="calendar", widget_type="calendar_view", icon="calendar")
    if "code" in name_lower or "execute" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="code", widget_type="code_viewer", icon="code")
    if "terminal" in name_lower or "shell" in name_lower:
        return ToolUiMeta(tool_name=tool_name, card_type="terminal", widget_type="terminal_output", icon="terminal")

    return ToolUiMeta(tool_name=tool_name, card_type="result", widget_type="generic_result", icon="wrench")


def resolve_tool_ui_meta(tool_name: str, schema: Optional[Dict[str, Any]] = None) -> ToolUiMeta:
    if tool_name in BUILTIN_TOOL_UI:
        return BUILTIN_TOOL_UI[tool_name]
    return infer_ui_meta_from_schema(tool_name, schema or {})
