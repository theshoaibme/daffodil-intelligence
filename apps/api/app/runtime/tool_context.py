"""Per-turn context injected into tool execution (user, tools mode, etc.)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict, List, Optional

_user_id: ContextVar[Optional[int]] = ContextVar("tool_user_id", default=None)
_student_id: ContextVar[Optional[str]] = ContextVar("tool_student_id", default=None)
_section: ContextVar[Optional[str]] = ContextVar("tool_section", default=None)
_selected_tools: ContextVar[List[str]] = ContextVar("tool_selected_tools", default=[])
_telegram_chat_id: ContextVar[Optional[int]] = ContextVar("tool_telegram_chat_id", default=None)


def set_turn_context(
    *,
    user_id: Optional[int] = None,
    student_id: Optional[str] = None,
    section: Optional[str] = None,
    selected_tools: Optional[List[str]] = None,
    telegram_chat_id: Optional[int] = None,
) -> None:
    if user_id is not None:
        _user_id.set(int(user_id))
    if student_id is not None:
        _student_id.set(student_id)
    if section is not None:
        _section.set(section)
    if selected_tools is not None:
        _selected_tools.set(list(selected_tools))
    if telegram_chat_id is not None:
        _telegram_chat_id.set(int(telegram_chat_id))


def clear_turn_context() -> None:
    _user_id.set(None)
    _student_id.set(None)
    _section.set(None)
    _selected_tools.set([])
    _telegram_chat_id.set(None)


def get_user_id(default: int = 0) -> int:
    return _user_id.get() or default


def get_student_id() -> Optional[str]:
    return _student_id.get()


def get_section(default: str = "64_I") -> str:
    return _section.get() or default


def get_selected_tools() -> List[str]:
    return list(_selected_tools.get() or [])


def get_telegram_chat_id() -> Optional[int]:
    return _telegram_chat_id.get()


def context_snapshot() -> Dict[str, Any]:
    return {
        "user_id": get_user_id(),
        "student_id": get_student_id(),
        "section": get_section(),
        "selected_tools": get_selected_tools(),
        "telegram_chat_id": get_telegram_chat_id(),
    }
