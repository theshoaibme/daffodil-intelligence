"""Agent catalog and per-user agent selection for Telegram chat."""

from __future__ import annotations

from typing import Optional, Tuple

from ....agents.builder import list_agents
from ....agents.registry import AGENT_MAP
from ....skills.store import global_config_store
from ..profiles import TelegramProfile, profile_store
from ..web_auth import parse_web_user_id
from .chat_runtime import agent_display_name, is_known_agent_id

_AUTOMATION_AGENT_IDS = frozenset({"copycat", "computer_use", "routine", "planning"})


def global_default_agent_id() -> str:
    try:
        return (global_config_store.get().default_agent_id or "main").strip()
    except Exception:
        return "main"


def resolve_agent_id(profile: TelegramProfile) -> str:
    """Effective agent for this Telegram user."""
    selected = (profile.selected_agent_id or "").strip().lower()
    default = global_default_agent_id()
    if not selected or selected in ("default", "reset", "main"):
        return default
    if is_known_agent_id(selected):
        return selected
    return default


def set_agent_for_profile(profile: TelegramProfile, agent_key: str) -> Tuple[bool, str]:
    """Set or clear selected agent. Returns (ok, message)."""
    key = (agent_key or "").strip().lower()
    if key in ("", "default", "reset", "main"):
        profile.selected_agent_id = ""
        profile_store.save(profile)
        default = global_default_agent_id()
        return True, f"Using workspace default agent: `{default}`"

    if not is_known_agent_id(key):
        return False, f"Unknown agent `{key}`.\n\nSend /agent to see available agents."

    profile.selected_agent_id = key
    profile_store.save(profile)
    name = agent_display_name(key)
    return True, (
        f"Active agent: *{name}* (`{key}`)\n\n"
        "Your messages now use this agent with tools, MCP, and memory."
    )


def format_agent_list(
    *,
    current_id: Optional[str] = None,
    telegram_id: Optional[int] = None,
) -> str:
    default = global_default_agent_id()
    active = current_id or default
    lines = [
        "*Available agents*",
        f"Current: `{active}` (workspace default: `{default}`)",
        "",
        "Send `/agent <id>` to switch, or `/agent default` to reset.",
        "",
    ]
    for aid, agent in sorted(AGENT_MAP.items()):
        marker = " ← active" if aid == active else ""
        lines.append(f"• `{aid}` — {agent.name}{marker}")

    web_user_id = None
    if telegram_id is not None:
        from ..auth_store import auth_store

        web_user_id = parse_web_user_id(auth_store.get_by_telegram_id(telegram_id))
    custom_agents = list_agents(user_id=web_user_id) if web_user_id else list_agents()
    public_custom = [
        a for a in custom_agents
        if a.is_public or (web_user_id and a.created_by == web_user_id)
    ]
    seen = set(AGENT_MAP.keys())
    hub_rows = [a for a in public_custom if a.id not in seen]
    if hub_rows:
        lines.extend(["", "*Custom agents (Agent Hub)*"])
        for agent in sorted(hub_rows, key=lambda a: a.id):
            marker = " ← active" if agent.id == active else ""
            lines.append(f"• `{agent.id}` — {agent.name}{marker}")
    return "\n".join(lines)


def format_automation_agents() -> str:
    lines = ["*Automation agents*", ""]
    for aid in sorted(_AUTOMATION_AGENT_IDS):
        agent = AGENT_MAP.get(aid)
        if agent:
            lines.append(f"• `{aid}` — {agent.description}")
    lines.append("")
    lines.append("Use `/agent <id>` to chat with a specific agent.")
    return "\n".join(lines)
