"""Workspace sandbox helpers for shell and file tools."""

from __future__ import annotations

import os
from pathlib import Path

from ...core.config import get_settings


def workspace_root() -> Path:
    settings = get_settings()
    root = getattr(settings, "WORKSPACE_ROOT", "") or os.getcwd()
    return Path(root).resolve()


def resolve_workspace_path(path: str, *, must_exist: bool = False) -> Path:
    """Resolve a path and ensure it stays inside the workspace root."""
    root = workspace_root()
    candidate = Path(path).expanduser()
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()

    try:
        resolved.relative_to(root)
    except ValueError as e:
        raise ValueError(f"Path outside workspace ({root}): {path}") from e

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path not found: {resolved}")
    return resolved


SHELL_DENY_PATTERNS = (
    "rm -rf /",
    "rm -rf /*",
    ":(){",
    "mkfs.",
    "dd if=/dev/zero",
    "> /dev/sd",
    "chmod -r /",
    "curl | sh",
    "wget | sh",
)


def is_shell_command_allowed(command: str) -> tuple[bool, str | None]:
    lowered = (command or "").strip().lower()
    if not lowered:
        return False, "Empty command"
    for pattern in SHELL_DENY_PATTERNS:
        if pattern in lowered:
            return False, f"Command blocked by safety policy: matched '{pattern}'"
    return True, None
