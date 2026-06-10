"""
Daffodil Intelligence Capabilities
==================================
Configures which Daffodil Intelligence builtin harness tools are enabled alongside
Daffodil's custom ToolRegistry tools.

Daffodil provides its own implementations for overlapping builtins (shell, file
ops, search). Non-overlapping Daffodil Intelligence builtins (edit via harness, image gen,
subagents, ask_question) remain enabled.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from google.antigravity import CapabilitiesConfig
    from google.antigravity.types import BuiltinTools

    _AVAILABLE = True
except Exception:  # pragma: no cover
    CapabilitiesConfig = None  # type: ignore
    BuiltinTools = None  # type: ignore
    _AVAILABLE = False


# Daffodil Intelligence builtins that overlap Daffodil registry tools — disabled to avoid duplicates.
_OVERLAP_DISABLED = [
    "RUN_COMMAND",
    "VIEW_FILE",
    "CREATE_FILE",
    "LIST_DIRECTORY",
    "SEARCH_DIRECTORY",
    "FIND_FILE",
    "EDIT_FILE",
]


def _builtin(name: str) -> Any | None:
    if BuiltinTools is None:
        return None
    return getattr(BuiltinTools, name, None)


def disabled_builtin_tools() -> List[Any]:
    if not settings.ANTIGRAVITY_DISABLE_BUILTIN_OVERLAPS:
        return []
    disabled: List[Any] = []
    for name in _OVERLAP_DISABLED:
        tool = _builtin(name)
        if tool is not None:
            disabled.append(tool)
    return disabled


def build_capabilities(
    *,
    enable_subagents: bool,
    persona: str = "main",
) -> Any | None:
    """Return CapabilitiesConfig for the Daffodil Intelligence agent, or None if SDK missing."""
    if not _AVAILABLE or CapabilitiesConfig is None:
        return None

    disabled = disabled_builtin_tools()
    if persona == "research":
        # Research persona: read-only harness; shell/file writes stay in Daffodil policy layer.
        read_only = getattr(BuiltinTools, "read_only", None)
        if callable(read_only):
            return CapabilitiesConfig(
                enable_subagents=enable_subagents,
                enabled_tools=read_only(),
            )

    kwargs: dict[str, Any] = {"enable_subagents": enable_subagents}
    if disabled:
        kwargs["disabled_tools"] = disabled
        logger.debug("Disabled %d overlapping Daffodil Intelligence builtins", len(disabled))

    return CapabilitiesConfig(**kwargs)
