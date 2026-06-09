"""Helpers for PostgreSQL-backed memory (INTEGER user_id, FK to users.id)."""

from __future__ import annotations

from typing import Any, Optional

# PostgreSQL INTEGER / SQLAlchemy Integer upper bound.
PG_INT_MAX = 2_147_483_647


def pg_memory_user_id(user_id: Any) -> Optional[int]:
    """Return user_id when it fits agent_memories.user_id; else None (use JSON fallback)."""
    try:
        uid = int(user_id or 0)
    except (TypeError, ValueError):
        return None
    if uid <= 0 or uid > PG_INT_MAX:
        return None
    return uid
