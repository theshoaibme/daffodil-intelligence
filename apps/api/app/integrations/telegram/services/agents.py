"""Agent catalog and per-user agent selection for Telegram chat."""

from __future__ import annotations

from typing import Optional, Tuple

from ....agents.registry import AGENT_MAP
from ....skills.store import global_config_store
from ..profiles import TelegramProfile, profile_store

_AUTOMATION_AGENT_IDS = frozenset({"copycat", "computer_use", "routine", "planning"})


def global_default_agent_id() -> str:
    return (global_config_store.get().default_agent_id or "main").strip()


def resolve_agent_id(profile: TelegramProfile) -> str:
    """Effective agent for this Telegram user."""
    selected = (profile.selected_agent_id or "").strip().lower()
    default = global_default_agent_id()
    if not selected or selected in ("default", "reset", "main"):
        return default
    if selected in AGENT_MAP:
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

    if key not in AGENT_MAP:
        return False, f"Unknown agent `{key}`.\n\nSend /agent to see available agents."

    agent = AGENT_MAP[key]
    profile.selected_agent_id = key
    profile_store.save(profile)
    return True, f"Active agent: *{agent.name}* (`{key}`)\n\nYour messages will use this agent until you change it."


def format_agent_list(*, current_id: Optional[str] = None) -> str:
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
