"""Short single-line titles for task panel rows."""

from __future__ import annotations

import re

_PREFIX_RE = re.compile(
    r"^(?:Tool|Agent|Parallel|Orchestrator|Search):\s*",
    re.IGNORECASE,
)


def short_title(text: str, *, max_len: int = 48) -> str:
    """Strip common prefixes, collapse whitespace, and truncate with ellipsis."""
    cleaned = _PREFIX_RE.sub("", (text or "").strip())
    cleaned = " ".join(cleaned.split())
    if len(cleaned) <= max_len:
        return cleaned
    if max_len <= 3:
        return cleaned[:max_len]
    return cleaned[: max_len - 3].rstrip() + "..."
