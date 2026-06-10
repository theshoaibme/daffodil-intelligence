"""MCP enablement helpers for routine / automation turns."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.config import get_settings


def routine_turn(message: Optional[str]) -> bool:
    if not message:
        return False
    from ..runtime.chat_router import message_needs_tools
    from ..runtime.intent_router import route_message

    if message_needs_tools(message):
        plan = route_message(message)
        if plan.primary == "routine" or "get_class_routine" in (plan.tools or []):
            return True
        if any(
            k in message.lower()
            for k in (
                "class routine",
                "class schedule",
                "my routine",
                "daily schedule",
                "tomorrow class",
                "tomorrow routine",
                "today class",
            )
        ):
            return True
    return False


def ensure_mcp_in_metadata(meta: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """Ensure MCP mode is active when routine or configured MCP servers need it."""
    if not get_settings().MCP_ENABLED:
        return meta

    tools: List[str] = list(meta.get("selected_tools") or [])
    has_servers = bool(meta.get("mcp_servers"))
    wants_mcp = (
        "MCP" in tools
        or "Agent" in tools
        or "Planning" in tools
        or has_servers
        or routine_turn(message)
    )
    if wants_mcp and "MCP" not in tools:
        tools.append("MCP")
        meta["selected_tools"] = tools
    return meta


def mcp_servers_for_user(user_id: int) -> List[Dict[str, str]]:
    from ..mcp.user_store import get_user_server_entries

    return get_user_server_entries(user_id)


def merge_invoke_metadata(
    agent_key: str,
    message: str,
    user_id: int,
    base: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build metadata for invoke_agent → run_turn with MCP + routine context."""
    from ..runtime.tool_context import get_department, get_section, get_turn_mcp_specs

    meta = dict(base or {})
    meta.setdefault("channel", "invoke_agent")
    meta["_message"] = message
    meta.setdefault("department", get_department())
    sec = get_section(default="")
    if sec:
        meta.setdefault("section", sec)

    tools = list(meta.get("selected_tools") or [])
    if agent_key == "routine":
        for mode in ("MCP", "Agent"):
            if mode not in tools:
                tools.append(mode)
        meta["selected_tools"] = tools

    if not meta.get("mcp_servers"):
        servers = mcp_servers_for_user(user_id)
        if servers:
            meta["mcp_servers"] = servers
        elif get_turn_mcp_specs():
            meta["mcp_servers"] = [
                {
                    "name": spec.name,
                    "command": " ".join([spec.command, *spec.args]).strip(),
                }
                for spec in get_turn_mcp_specs()
            ]

    return ensure_mcp_in_metadata(meta, message)
