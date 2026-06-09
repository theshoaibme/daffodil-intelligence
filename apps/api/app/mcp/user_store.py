"""Per-user MCP server definitions configured from the web UI."""

from __future__ import annotations

from threading import Lock
from typing import Any

from .builder import McpBuilder
from .protocol import McpServerSpec

_lock = Lock()
_store: dict[str, list[dict[str, str]]] = {}


def _key(user_id: int | str) -> str:
    return str(int(user_id or 0))


def get_user_server_entries(user_id: int | str = 0) -> list[dict[str, str]]:
    with _lock:
        return list(_store.get(_key(user_id), []))


def set_user_server_entries(user_id: int | str, entries: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        name = (entry.get("name") or "").strip()
        command = (entry.get("command") or "").strip()
        if not name or not command:
            continue
        normalized = name.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append({"name": name, "command": command})
    with _lock:
        _store[_key(user_id)] = cleaned
    return cleaned


def get_user_specs(user_id: int | str = 0) -> list[McpServerSpec]:
    specs: list[McpServerSpec] = []
    for entry in get_user_server_entries(user_id):
        try:
            specs.append(McpBuilder.from_name_command(entry["name"], entry["command"]))
        except ValueError:
            continue
    return specs


def clear_user_servers(user_id: int | str = 0) -> None:
    with _lock:
        _store.pop(_key(user_id), None)


def snapshot() -> dict[str, Any]:
    with _lock:
        return {key: list(value) for key, value in _store.items()}
