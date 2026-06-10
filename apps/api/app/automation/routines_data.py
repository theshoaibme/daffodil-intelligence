"""Class routine lookup — CSV bundles, uploads, agent memory (no hardcoded schedules)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .routine_csv import get_csv_routine
from .routine_pdf_reader import read_department_routine_source
from .routine_resolver import load_uploaded_catalog, normalize_section


def get_uploaded_routine(
    section: str,
    day: Optional[str] = None,
    *,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """Return schedule from bundled CSV, uploads, or department PDF/text."""
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
    if uploaded and key in uploaded:
        weekly = uploaded[key]

    if weekly and any(weekly.values()):
        payload: Dict[str, Any] = {
            "section": key,
            "department": department or None,
            "source": "department_upload",
        }
        if day:
            payload.update({"day": day, "items": weekly.get(day, [])})
        else:
            payload["weekly"] = weekly
        return payload

    csv_data = get_csv_routine(key, day, department=department)
    if csv_data.get("weekly") and any(csv_data["weekly"].values()):
        return csv_data
    if csv_data.get("items"):
        return csv_data

    source_text = read_department_routine_source(department, key)
    payload = {
        "section": key,
        "department": department or None,
        "source": "none",
        "weekly": {},
    }
    if source_text:
        payload["pdf_excerpt"] = source_text[:1200]
        payload["source"] = "department_pdf"

    if day:
        payload.update({"day": day, "items": []})

    if csv_data.get("error") == "section_not_in_csv":
        payload["hint"] = csv_data.get("hint")
        payload["sample_sections"] = csv_data.get("sample_sections")

    return payload


# Backward-compatible alias used by scheduler and university connector.
get_section_routine = get_uploaded_routine
