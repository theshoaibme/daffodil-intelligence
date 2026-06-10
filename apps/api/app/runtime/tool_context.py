"""Per-turn context injected into tool execution (user, tools mode, etc.)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from ..mcp.protocol import McpServerSpec

_user_id: ContextVar[Optional[int]] = ContextVar("tool_user_id", default=None)
_student_id: ContextVar[Optional[str]] = ContextVar("tool_student_id", default=None)
_section: ContextVar[Optional[str]] = ContextVar("tool_section", default=None)
_department: ContextVar[Optional[str]] = ContextVar("tool_department", default=None)
_selected_tools: ContextVar[List[str]] = ContextVar("tool_selected_tools", default=[])
_telegram_chat_id: ContextVar[Optional[int]] = ContextVar("tool_telegram_chat_id", default=None)
_turn_mcp_specs: ContextVar[List[McpServerSpec]] = ContextVar("tool_turn_mcp_specs", default=[])


def set_turn_context(
    *,
    user_id: Optional[int] = None,
    student_id: Optional[str] = None,
    section: Optional[str] = None,
    department: Optional[str] = None,
    selected_tools: Optional[List[str]] = None,
    telegram_chat_id: Optional[int] = None,
    mcp_specs: Optional[List[McpServerSpec]] = None,
) -> None:
    if user_id is not None:
        _user_id.set(int(user_id))
    if student_id is not None:
        _student_id.set(student_id)
    if section is not None:
        _section.set(section)
    if department is not None:
        _department.set(department.strip() or None)
    if selected_tools is not None:
        _selected_tools.set(list(selected_tools))
    if telegram_chat_id is not None:
        _telegram_chat_id.set(int(telegram_chat_id))
    if mcp_specs is not None:
        _turn_mcp_specs.set(list(mcp_specs))


def clear_turn_context() -> None:
    _user_id.set(None)
    _student_id.set(None)
    _section.set(None)
    _department.set(None)
    _selected_tools.set([])
    _telegram_chat_id.set(None)
    _turn_mcp_specs.set([])


def get_turn_mcp_specs() -> List[McpServerSpec]:
    return list(_turn_mcp_specs.get() or [])


def get_user_id(default: int = 0) -> int:
    return _user_id.get() or default


def get_student_id() -> Optional[str]:
    return _student_id.get()


def get_section(default: str = "") -> str:
    from ..automation.routine_resolver import resolve_section

    explicit = _section.get()
    if explicit:
        return resolve_section(section=explicit, department=_department.get()) or default
    return resolve_section(section=None, department=_department.get()) or default


def get_department() -> Optional[str]:
    return _department.get()


def get_selected_tools() -> List[str]:
    return list(_selected_tools.get() or [])


def get_telegram_chat_id() -> Optional[int]:
    return _telegram_chat_id.get()


def context_snapshot() -> Dict[str, Any]:
    return {
        "user_id": get_user_id(),
        "student_id": get_student_id(),
        "section": get_section() or None,
        "department": get_department(),
        "selected_tools": get_selected_tools(),
        "telegram_chat_id": get_telegram_chat_id(),
    }
