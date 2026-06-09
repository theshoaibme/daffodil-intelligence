"""Decide when normal chat should use the fast Groq path vs full Antigravity runtime."""

from __future__ import annotations

from typing import Any, List, Optional

from ..core.config import get_settings
from .agent_factory import AgentPersona

_MAIN_AGENTS = frozenset({"main", "supervisor", "default", ""})
# Modes that require Antigravity tool-calling (MCP alone is a hint only).
_TOOL_MODES = frozenset({"Planning", "Research", "Agent"})
_FULL_RUNTIME_ROUTINGS = frozenset({
    "attachments",
    "code",
    "code_complex",
    "reasoning",
    "long_context",
})
# "complex" stays on Groq (larger model) when tools are not required.


def groq_model_for_routing(routing: str) -> str:
    """Pick the Groq model id for a resolved routing reason."""
    settings = get_settings()
    if routing in ("fast_simple", "default"):
        return settings.GROQ_FAST_MODEL
    return settings.GROQ_MODEL


def should_use_fast_groq(
    *,
    attachments: bool = False,
    routing: str = "default",
    was_auto: bool = True,
    metadata: Optional[dict] = None,
    agent_id: Optional[str] = None,
    persona: AgentPersona | str = AgentPersona.MAIN,
    include_tools: Optional[List[str]] = None,
) -> bool:
    """True when a turn is simple enough for Groq-only chat (no tools/MCP)."""
    settings = get_settings()
    if not settings.GROQ_FAST_CHAT or not settings.GROQ_API_KEY:
        return False
    if attachments:
        return False
    if not was_auto:
        return False
    if routing in _FULL_RUNTIME_ROUTINGS:
        return False

    selected = (metadata or {}).get("selected_tools") or []
    if any(mode in _TOOL_MODES for mode in selected):
        return False

    aid = (agent_id or "").strip().lower()
    if aid and aid not in _MAIN_AGENTS:
        return False

    if include_tools:
        return False

    if persona != AgentPersona.MAIN and str(persona) != AgentPersona.MAIN.value:
        return False

    return True
