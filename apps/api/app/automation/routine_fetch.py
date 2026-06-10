"""Single source for class routines — memory, data/routines CSV, uploads, PDF only."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .routine_memory import recall_class_routine
from .routine_pdf_reader import read_routine_pdf_fast
from .routine_resolver import normalize_section, resolve_routine_day
from .routines_data import get_uploaded_routine
from ..runtime.tool_context import get_user_id


async def fetch_class_routine(
    *,
    user_id: Optional[int] = None,
    section: str,
    day: Optional[str] = None,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load a class routine from real sources only (never synthesized):
    1. Agent memory / skills
    2. data/routines/*.csv and section uploads
    3. data/routines/{department}/{section}.pdf (or .txt)
    """
    uid = int(user_id or 0) or get_user_id()
    sec = normalize_section(section)
    if not sec:
        return {
            "section": None,
            "source": "none",
            "error": "section_required",
            "hint": "Provide a section code (e.g. 64_I).",
        }

    day_name = resolve_routine_day(day)

    if uid:
        memory_data = await recall_class_routine(
            uid, section=sec, department=department, day=day_name
        )
        if memory_data and (memory_data.get("weekly") or memory_data.get("items")):
            return {**memory_data, "source": memory_data.get("source") or "memory"}

    data = get_uploaded_routine(sec, day_name, department=department)
    if data.get("weekly") and any(data["weekly"].values()):
        return data
    if data.get("items"):
        return data
    if data.get("source") == "csv":
        return data

    pdf = read_routine_pdf_fast(
        department,
        sec,
        day=day_name,
        max_chars=6000,
    )
    if pdf.get("text") and not pdf.get("error"):
        payload: Dict[str, Any] = {
            **pdf,
            "section": sec,
            "department": department,
            "source": "data_folder_pdf",
        }
        if day_name:
            payload.setdefault("day", day_name)
        return payload

    if data.get("pdf_excerpt"):
        return {**data, "source": "department_pdf"}

    return {
        "section": sec,
        "department": department,
        "source": "none",
        "day": day_name,
        "items": [],
        "error": "not_found",
        "hint": (
            "No routine in data/routines for this section. "
            "Add a CSV under data/routines/ or upload {dept}/{section}.pdf."
        ).format(dept=department or "department"),
        "sample_sections": data.get("sample_sections"),
        "csv_files_searched": data.get("csv_files_searched"),
    }


def routine_has_schedule(data: Dict[str, Any]) -> bool:
    if data.get("weekly") and any(data["weekly"].values()):
        return True
    if data.get("items"):
        return True
    if data.get("text") and data.get("source") in ("data_folder_pdf", "department_pdf"):
        return True
    if data.get("pdf_excerpt"):
        return True
    return False
