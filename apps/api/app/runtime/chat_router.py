"""Decide when normal chat should use the fast Groq path vs full Antigravity runtime."""

from __future__ import annotations

import re
from typing import Any, List, Optional

from ..core.config import get_settings
from ..core.hf_models import is_hf_model
from .agent_factory import AgentPersona

_SECTION_CODE = re.compile(r"\b(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\b")
_TOOL_KEYWORDS = (
    "class routine",
    "class schedule",
    "my routine",
    "cgpa",
    "gpa",
    "grade",
    "result",
    "attendance",
    "shuttle",
    "bus route",
    "remind",
    "reminder",
    "exam schedule",
    "fee",
    "tuition",
    "library",
    "book",
    "internship",
    "job",
    "invoke_agent",
    "get_class_routine",
    "deep_research",
    "google_web_search",
    "search_papers",
    "research",
)

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


def message_needs_tools(message: str) -> bool:
    """True when a turn needs tool-calling (not plain Groq chat)."""
    text = (message or "").strip()
    if not text:
        return False
    if _SECTION_CODE.search(text):
        return True
    lower = text.lower()
    return any(k in lower for k in _TOOL_KEYWORDS)


def should_use_hf_chat(
    *,
    model_id: str,
    attachments: bool = False,
    include_tools: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """True when a turn should use Hugging Face Inference (e.g. GLM-5.1)."""
    settings = get_settings()
    if not settings.HUGGINGFACE_ENABLED or not settings.HUGGINGFACE_API_KEY:
        return False
    if attachments or include_tools:
        return False
    meta = metadata or {}
    if meta.get("channel") == "telegram":
        return False
    if message_needs_tools(meta.get("_message", "")):
        return False
    selected = meta.get("selected_tools") or []
    if any(mode in _TOOL_MODES for mode in selected):
        return False
    if settings.MCP_ENABLED and (meta.get("mcp_servers") or "MCP" in selected):
        return False
    return is_hf_model(model_id)


def groq_model_for_routing(routing: str) -> str:
    """Pick the Groq model id for a resolved routing reason."""
    settings = get_settings()
    if routing in ("fast_simple", "default"):
        return settings.GROQ_FAST_MODEL
    if routing == "complex":
        return settings.GROQ_MODEL
    return settings.GROQ_FAST_MODEL


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

    meta = metadata or {}
    if meta.get("channel") == "telegram":
        return False
    if message_needs_tools(meta.get("_message", "")):
        return False

    selected = meta.get("selected_tools") or []
    if settings.MCP_ENABLED and ("MCP" in selected or meta.get("mcp_servers")):
        return False
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
