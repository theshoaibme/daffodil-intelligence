"""Class routine lookup — uploads and agent memory only (no hardcoded catalogs)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .routine_pdf_reader import read_department_routine_source
from .routine_resolver import load_uploaded_catalog, normalize_section


def get_uploaded_routine(
    section: str,
    day: Optional[str] = None,
    *,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """Return schedule from department-uploaded JSON/PDF only."""
    key = normalize_section(section)
    if not key:
        return {
            "section": None,
            "department": department,
            "source": "none",
            "error": "section_required",
            "hint": "Ask the user for their section, or save it with store_note (tag=section).",
        }

    uploaded = load_uploaded_catalog(key, department)
    weekly: Dict[str, List[Dict[str, Any]]] = {}
    source = "none"
    if uploaded and key in uploaded:
        weekly = uploaded[key]
        source = "department_upload"

    source_text = read_department_routine_source(department, key)
    payload: Dict[str, Any] = {
        "section": key,
        "department": department or None,
        "source": source,
    }
    if source_text:
        payload["pdf_excerpt"] = source_text[:1200]
        if source == "none":
            payload["source"] = "department_pdf"

    if day:
        payload.update({"day": day, "items": weekly.get(day, [])})
        return payload

    payload["weekly"] = weekly
    return payload


# Backward-compatible alias used by scheduler and university connector.
get_section_routine = get_uploaded_routine
