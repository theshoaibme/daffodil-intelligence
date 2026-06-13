"""Turn complexity policy for task-tree emission and runtime routing."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from .chat_router import message_needs_tools, should_force_full_runtime

_MULTI_STEP_SIGNALS = (
    " then ",
    " after that ",
    " and then ",
    " next ",
    " finally ",
    " first ",
    " second ",
    " step ",
    "তারপর",
    "পরে",
    "এরপর",
    "multiple",
    "also",
    "additionally",
    "furthermore",
)

_RESEARCH_KEYWORDS = (
    "deep_research",
    "compare ",
    "versus",
    " vs ",
    "research ",
    "find sources",
    "literature review",
)


class TurnComplexity(str, Enum):
    SIMPLE = "simple"
    TOOL = "tool"
    RESEARCH = "research"
    PLANNING = "planning"
    MULTI_AGENT = "multi_agent"


def should_emit_task_tree(complexity: TurnComplexity) -> bool:
    """Simple fast-path turns should not stream a task tree."""
    return complexity != TurnComplexity.SIMPLE


def _is_multi_step_message(message: str) -> bool:
    lower = (message or "").lower()
    return any(signal in lower for signal in _MULTI_STEP_SIGNALS)


def _is_research_message(message: str) -> bool:
    lower = (message or "").lower()
    return any(k in lower for k in _RESEARCH_KEYWORDS)


def classify_turn(
    message: str,
    metadata: Optional[dict],
    routing: str,
    use_fast_groq: bool,
    use_hf: bool,
) -> TurnComplexity:
    """Classify turn complexity for task UI and runtime hints."""
    meta = metadata or {}
    selected = meta.get("selected_tools") or []
    text = (message or "").strip()
    lower = text.lower()

    if (use_fast_groq or use_hf) and not should_force_full_runtime(meta):
        if not message_needs_tools(text):
            return TurnComplexity.SIMPLE

    if "Agent" in selected or "parallel_invoke" in lower:
        return TurnComplexity.MULTI_AGENT

    if "Research" in selected or _is_research_message(text):
        return TurnComplexity.RESEARCH

    if "Planning" in selected or _is_multi_step_message(text):
        return TurnComplexity.PLANNING

    if message_needs_tools(text):
        if "parallel_invoke" in lower or lower.count("invoke_agent") > 1:
            return TurnComplexity.MULTI_AGENT
        return TurnComplexity.TOOL

    if routing in ("code", "code_complex", "reasoning", "long_context", "attachments"):
        return TurnComplexity.TOOL

    return TurnComplexity.TOOL
