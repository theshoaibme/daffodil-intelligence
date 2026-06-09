"""Central guard — reject user input RPC while CopyCat replay/record is active."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .audit import log_event
from .input_lock import COPYCAT_MESSAGE, is_locked, lock_mode

BLOCKED_METHODS = frozenset({
    "mouse.move",
    "mouse.click",
    "mouse.scroll",
    "mouse.drag",
    "keyboard.type",
    "keyboard.hotkey",
    "keyboard.press",
})

ALLOWED_DURING_LOCK = frozenset({
    "ping",
    "status",
    "permissions.status",
    "record.stop",
    "record.stop_replay",
    "record.status",
    "audit.tail",
    "audit.system_log",
    "screenshot",
})


def check_method_allowed(method: str, *, source: str = "user") -> Optional[Dict[str, Any]]:
    """Return error dict if blocked, else None."""
    if not is_locked():
        return None
    if method in ALLOWED_DURING_LOCK:
        return None
    if method in BLOCKED_METHODS:
        log_event(
            "copycat.rpc_blocked",
            detail={"method": method, "source": source, "mode": lock_mode()},
            level="warn",
        )
        return {
            "error": "copycat_running",
            "message": COPYCAT_MESSAGE,
            "mode": lock_mode(),
            "blocked": True,
        }
    return None
