"""Recall class routine and section preferences from agent memory."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from ..memory import memory_service
from .routine_resolver import normalize_section

_SECTION_CODE = re.compile(r"\b(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\b", re.I)
_ROUTINE_AGENT = "routine"


async def recall_user_section(user_id: int) -> str:
    """Section from memory (preference/fact) — no hardcoded defaults."""
    if not user_id:
        return ""
    notes = await memory_service.recall(
        "class section routine",
        user_id=user_id,
        agent_id=_ROUTINE_AGENT,
        memory_types=["preference", "fact"],
        k=6,
    )
    for note in notes:
        meta = note.get("metadata") or {}
        if meta.get("section"):
            return normalize_section(str(meta["section"]))
        payload = note.get("payload") or {}
        if isinstance(payload, dict) and payload.get("section"):
            return normalize_section(str(payload["section"]))
        text = (note.get("content") or note.get("text") or "").strip()
        match = _SECTION_CODE.search(text)
        if match:
            return match.group(1).upper()
    return ""


def _weekly_from_note(note: Dict[str, Any]) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    payload = note.get("payload") or {}
    if isinstance(payload, dict):
        weekly = payload.get("weekly")
        if isinstance(weekly, dict):
            return weekly
    text = (note.get("content") or note.get("text") or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            weekly = parsed.get("weekly")
            if isinstance(weekly, dict):
                return weekly
    except json.JSONDecodeError:
        pass
    return None


async def recall_class_routine(
    user_id: int,
    *,
    section: str = "",
    department: Optional[str] = None,
    day: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Structured weekly schedule stored in agent memory or skills context."""
    if not user_id:
        return None

    query_parts = ["class routine", "weekly schedule"]
    if section:
        query_parts.append(section)
    if department:
        query_parts.append(department)

    notes = await memory_service.recall(
        " ".join(query_parts),
        user_id=user_id,
        agent_id=_ROUTINE_AGENT,
        memory_types=["fact", "preference", "skill"],
        k=8,
    )

    sec = normalize_section(section)
    for note in notes:
        meta = note.get("metadata") or {}
        note_section = normalize_section(str(meta.get("section") or ""))
        note_dept = (meta.get("department") or "").strip().upper()
        if sec and note_section and note_section != sec:
            continue
        if department and note_dept and note_dept != department.strip().upper():
            continue

        weekly = _weekly_from_note(note)
        if not weekly:
            continue

        payload: Dict[str, Any] = {
            "section": sec or note_section or None,
            "department": department or meta.get("department"),
            "source": "memory",
            "memory_id": note.get("id"),
        }
        if day:
            payload.update({"day": day, "items": weekly.get(day, [])})
        else:
            payload["weekly"] = weekly
        return payload

    return None
