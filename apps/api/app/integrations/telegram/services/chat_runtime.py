"""Build full agent-runtime context for Telegram chat turns."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ....agents.builder import get_agent
from ....agents.registry import AGENT_MAP
from ....core.config import get_settings
from ..auth_store import TelegramAccount
from ..web_auth import resolve_runtime_user_id

_TURN_COUNTERS: Dict[str, int] = {}

_RESEARCH_AGENTS = frozenset({"research", "academic", "library"})
_PLANNING_AGENTS = frozenset({"planning", "routine", "automation"})


def is_known_agent_id(agent_id: str) -> bool:
    key = (agent_id or "").strip().lower()
    if not key:
        return False
    if key in AGENT_MAP:
        return True
    return get_agent(key) is not None


def agent_display_name(agent_id: str) -> str:
    key = (agent_id or "").strip().lower()
    builtin = AGENT_MAP.get(key)
    if builtin:
        return builtin.name
    custom = get_agent(key)
    if custom:
        return custom.name
    return key


def _selected_tools_for_agent(agent_id: str) -> List[str]:
    settings = get_settings()
    tools: List[str] = []
    key = (agent_id or "").strip().lower()

    if settings.MCP_ENABLED:
        tools.append("MCP")

    if key and key not in ("main", "supervisor", "default"):
        tools.append("Agent")

    if key in _PLANNING_AGENTS:
        tools.append("Planning")
    if key in _RESEARCH_AGENTS:
        tools.append("Research")

    return tools


def build_turn_metadata(
    *,
    telegram_id: int,
    account: Optional[TelegramAccount],
    agent_id: str,
) -> Dict[str, Any]:
    student_id = ""
    if account:
        student_id = (account.student_id or "").strip()

    return {
        "student_id": student_id or None,
        "department": (account.department or "").strip() if account else "",
        "selected_tools": _selected_tools_for_agent(agent_id),
        "telegram_chat_id": telegram_id,
        "channel": "telegram",
    }


_SIMPLE_GREETINGS = frozenset({
    "hello",
    "hi",
    "hey",
    "hi there",
    "hello there",
    "hola",
    "salam",
    "assalamu alaikum",
    "assalamualaikum",
})


def is_simple_greeting(text: str) -> bool:
    """True when the message is only a short hello/hi (no other content)."""
    normalized = (text or "").strip().lower().rstrip("!?.")
    return normalized in _SIMPLE_GREETINGS


def telegram_model_id() -> Optional[str]:
    """Concrete model id for Telegram, or None for auto routing."""
    mid = (get_settings().TELEGRAM_CHAT_MODEL or "auto").strip()
    if not mid or mid.lower() == "auto":
        return None
    return mid


def next_turn_index(runtime_user_id: int, chat_id: Any) -> int:
    key = f"{runtime_user_id}:{chat_id}"
    _TURN_COUNTERS[key] = _TURN_COUNTERS.get(key, 0) + 1
    return _TURN_COUNTERS[key]


def build_telegram_turn(
    *,
    telegram_id: int,
    account: Optional[TelegramAccount],
    agent_id: str,
    chat_id: Any,
) -> Tuple[int, Dict[str, Any], Optional[str], int]:
    runtime_user_id = resolve_runtime_user_id(telegram_id, account)
    metadata = build_turn_metadata(
        telegram_id=telegram_id,
        account=account,
        agent_id=agent_id,
    )
    model_id = telegram_model_id()
    turn_index = next_turn_index(runtime_user_id, chat_id)
    return runtime_user_id, metadata, model_id, turn_index
