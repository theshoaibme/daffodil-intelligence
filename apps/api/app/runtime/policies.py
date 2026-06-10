"""
Agent Policies
==============
Declarative tool-execution policies for the Antigravity runtime using
``google.antigravity.hooks.policy``.

Read-only and domain tools are allowed freely. Destructive tools (shell, file
writes/deletes) and computer-control tools (mouse/keyboard) are routed through
an approval handler when ``COMPUTER_USE_REQUIRE_CONFIRM`` is enabled.

The approval handler is intentionally pluggable: a real UI/Telegram confirm
flow can register its own callback via :func:`set_approval_handler`. The default
handler approves (the operator owns the machine and explicitly enabled computer
use) while logging every gated action for auditing.
"""

import logging
from typing import Any, Awaitable, Callable, List, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from google.antigravity.hooks import policy as _policy
    _POLICY_AVAILABLE = True
except Exception as e:  # pragma: no cover - import guard
    _policy = None  # type: ignore
    _POLICY_AVAILABLE = False
    logger.warning(f"Antigravity policy module unavailable: {e}")


# Tools that may mutate the host or the world (Daffodil + Antigravity builtin names).
DESTRUCTIVE_TOOLS = [
    "run_shell_command",
    "run_command",
    "run_python",
    "write_file",
    "create_file",
    "edit_file",
    "delete_file",
]
# Tools that drive the physical desktop.
COMPUTER_CONTROL_TOOLS = [
    "mouse_move",
    "mouse_click",
    "mouse_scroll",
    "keyboard_type",
    "keyboard_hotkey",
]

# Pluggable approval callback. Receives the Antigravity ToolCall, returns bool.
ApprovalHandler = Callable[[Any], "bool | Awaitable[bool]"]
_approval_handler: Optional[ApprovalHandler] = None


def set_approval_handler(handler: Optional[ApprovalHandler]) -> None:
    """Register a custom approval handler for gated tools."""
    global _approval_handler
    _approval_handler = handler


async def _default_approval(tool_call: Any) -> bool:
    name = getattr(tool_call, "name", "<unknown>")
    if _approval_handler is not None:
        result = _approval_handler(tool_call)
        if hasattr(result, "__await__"):
            result = await result  # type: ignore
        logger.info(f"[policy] gated tool '{name}' -> {'approved' if result else 'denied'} (custom handler)")
        return bool(result)
    logger.info(f"[policy] gated tool '{name}' auto-approved (no handler registered)")
    return True


def build_policies(persona: str = "main") -> List[Any]:
    """Build the policy list for a given agent persona.

    Args:
        persona: "main", "computer_use", "planning", etc.

    Returns:
        A list of Antigravity ``Policy`` objects (empty if SDK unavailable).
    """
    if not _POLICY_AVAILABLE or _policy is None:
        return []

    policies: List[Any] = [_policy.allow("*")]

    require_confirm = settings.COMPUTER_USE_REQUIRE_CONFIRM

    if require_confirm:
        for tool_name in DESTRUCTIVE_TOOLS:
            policies.append(_policy.ask_user(tool_name, handler=_default_approval, name=f"confirm:{tool_name}"))

    # Computer control is gated for every persona except the dedicated
    # computer_use agent when confirmation is disabled.
    if require_confirm:
        for tool_name in COMPUTER_CONTROL_TOOLS:
            policies.append(_policy.ask_user(tool_name, handler=_default_approval, name=f"confirm:{tool_name}"))

    return policies
