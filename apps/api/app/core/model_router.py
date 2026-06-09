"""Per-turn model resolution including Auto mode heuristics."""

from __future__ import annotations

from typing import Optional, Tuple

from .config import get_settings
from .models_catalog import AUTO_MODEL_ID

_REASONING_KEYWORDS = (
    "prove",
    "analyze",
    "reason",
    "step by step",
    "debug",
    "algorithm",
    "optimize",
    "architecture",
    "theorem",
    "derive",
    "mathematical",
    "complexity",
    "formal",
    "logic",
    "hypothesis",
)
_CODE_KEYWORDS = (
    "```",
    "function",
    "class ",
    "def ",
    "import ",
    "refactor",
    "typescript",
    "javascript",
    "python",
    "rust",
    "golang",
    "sql query",
    "unit test",
    "lint",
    "compile",
)
_COMPLEX_KEYWORDS = (
    "research",
    "compare",
    "evaluate",
    "design",
    "strategy",
    "comprehensive",
    "detailed analysis",
    "pros and cons",
    "trade-off",
    "multi-step",
    "deep dive",
)
_FAST_KEYWORDS = (
    "what is",
    "define",
    "translate",
    "summarize briefly",
    "hello",
    "thanks",
)


def resolve_model_for_turn(
    *,
    model_id: Optional[str],
    message: str,
    default_model: Optional[str] = None,
    has_attachments: bool = False,
) -> Tuple[str, bool, str]:
    """Resolve the concrete model id for a turn.

    Returns ``(resolved_model_id, was_auto, routing_reason)``.
    """
    settings = get_settings()
    use_groq = settings.GROQ_FAST_CHAT and bool(settings.GROQ_API_KEY)
    groq_fast = settings.GROQ_FAST_MODEL
    groq_strong = settings.GROQ_MODEL
    default = default_model or (groq_fast if use_groq else settings.ANTIGRAVITY_MODEL)

    if model_id and model_id != AUTO_MODEL_ID:
        return model_id, False, "manual"

    text = (message or "").strip()
    lower = text.lower()
    word_count = len(text.split())

    if has_attachments:
        return "gemini-2.5-flash", True, "attachments"

    if "```" in text or any(k in lower for k in _CODE_KEYWORDS):
        if word_count > 80 or "architect" in lower or "refactor" in lower:
            return "gemini-2.5-pro", True, "code_complex"
        return "gemini-2.5-flash", True, "code"

    if any(k in lower for k in _REASONING_KEYWORDS):
        return "gemini-2.5-pro", True, "reasoning"

    if word_count > 350:
        return "gemini-2.5-pro", True, "long_context"

    if any(k in lower for k in _COMPLEX_KEYWORDS) or word_count > 100:
        if use_groq:
            return groq_strong, True, "complex"
        return "gemini-2.5-flash", True, "complex"

    if word_count <= 25 and any(k in lower for k in _FAST_KEYWORDS):
        return groq_fast if use_groq else "gemini-2.0-flash-lite", True, "fast_simple"

    return default, True, "default"
