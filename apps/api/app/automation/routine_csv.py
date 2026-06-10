"""Parse department class routines from CSV files in data/routines/."""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .routine_resolver import ROUTINE_DATA_ROOT, normalize_department_key, normalize_section

logger = logging.getLogger(__name__)

_DAYS = (
    "SATURDAY",
    "SUNDAY",
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
)
_DAY_RE = re.compile(
    r"\b(" + "|".join(_DAYS) + r")\b",
    re.I,
)
_TIME_RE = re.compile(r"\d{1,2}[.:]\d{2}\s*-\s*\d{1,2}[.:]\d{2}")
_CSE_SECTION_RE = re.compile(r"\((\d{2}_[A-Za-z0-9]+)\)", re.I)
_SWE_SECTION_RE = re.compile(r"-(\d{2})-([A-Za-z0-9]+)$")
_RE_SECTION_RE = re.compile(r"\(RE_[A-Za-z0-9_]+(?:\([^)]*\))?\)", re.I)

_DEPARTMENT_CSV_HINTS: Dict[str, Tuple[str, ...]] = {
    "CSE": ("cse-class-routine", "cse_class"),
    "SWE": ("swe-routine", "software-engineering"),
    "SOFTWARE_ENGINEERING": ("swe-routine",),
}


def _title_case_day(raw: str) -> str:
    return raw.strip().capitalize()


def extract_section_from_course(course: str) -> str:
    """Map a course cell to a section id (e.g. CSE321(66_C) → 66_C)."""
    if not course:
        return ""
    text = course.strip()
    match = _CSE_SECTION_RE.search(text)
    if match:
        return normalize_section(match.group(1))
    match = _RE_SECTION_RE.search(text)
    if match:
        return normalize_section(match.group(0).strip("()"))
    match = _SWE_SECTION_RE.search(text.replace(" ", ""))
    if match:
        return normalize_section(f"{match.group(1)}_{match.group(2)}")
    return ""


def list_csv_routine_files() -> List[Path]:
    if not ROUTINE_DATA_ROOT.is_dir():
        return []
    return sorted(ROUTINE_DATA_ROOT.glob("*.csv"))


def resolve_csv_path(department: Optional[str] = None) -> Optional[Path]:
    """Pick the best CSV for a department, or None to search all files."""
    dept_key = normalize_department_key(department)
    if dept_key:
        hints = _DEPARTMENT_CSV_HINTS.get(dept_key, (dept_key.lower().replace("_", "-"),))
        for path in list_csv_routine_files():
            name = path.name.lower()
            if any(h in name for h in hints):
                return path
    return None


def infer_department_from_csv(path: Path) -> str:
    name = path.name.lower()
    if "cse" in name and "class-routine" in name:
        return "CSE"
    if "swe" in name or "software" in name:
        return "SWE"
    if "exam" in name or "improvement" in name:
        return "EXAM"
    return "GENERAL"


@dataclass
class ParsedCsvRoutine:
    path: str
    department: str
    title: str
    format: str  # cse_grid | swe_grid | generic
    weekly_by_section: Dict[str, Dict[str, List[Dict[str, Any]]]] = field(
        default_factory=dict
    )
    sections: List[str] = field(default_factory=list)


def _add_entry(
    store: Dict[str, Dict[str, List[Dict[str, Any]]]],
    *,
    day: str,
    time: str,
    room: str,
    course: str,
    teacher: str,
) -> None:
    course = (course or "").strip()
    if not course:
        return
    section = extract_section_from_course(course)
    if not section:
        return
    entry = {
        "time": time,
        "room": (room or "").strip(),
        "course": course,
        "teacher": (teacher or "").strip(),
        "type": "class",
    }
    store.setdefault(section, {}).setdefault(day, []).append(entry)


def _parse_cse_grid(rows: List[List[str]], path: Path) -> ParsedCsvRoutine:
    title = ""
    for row in rows[:4]:
        joined = ",".join(row)
        if "Class Routine" in joined:
            title = joined.strip(", ")
            break

    store: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    current_day = ""
    slot_starts: List[int] = []
    slot_times: List[str] = []
    time_row: List[str] = []
    in_block = False

    for row in rows:
        if not any((c or "").strip() for c in row):
            continue

        day_match = _DAY_RE.search(",".join(row))
        if day_match:
            current_day = _title_case_day(day_match.group(1))
            slot_starts = []
            slot_times = []
            time_row = []
            in_block = False
            continue

        if not current_day:
            continue

        times_found: List[Tuple[int, str]] = []
        for idx, cell in enumerate(row):
            cell_text = (cell or "").strip()
            if _TIME_RE.search(cell_text):
                times_found.append((idx, cell_text.replace(" ", "")))

        if times_found and (row[0] or "").strip().lower() != "room":
            time_row = row
            in_block = False
            continue

        if (row[0] or "").strip().lower() == "room" and "course" in ",".join(row).lower():
            slot_starts = [
                idx for idx, cell in enumerate(row) if (cell or "").strip().lower() == "room"
            ]
            slot_times = []
            for start in slot_starts:
                time_cell = ""
                if time_row and start + 1 < len(time_row):
                    time_cell = (time_row[start + 1] or "").strip()
                slot_times.append(time_cell.replace(" ", ""))
            in_block = True
            continue

        if not in_block or not slot_starts:
            continue

        first = (row[0] or "").strip()
        if first.startswith("(COM LAB)") or first == "(COM LAB)":
            continue

        for slot_idx, start in enumerate(slot_starts):
            time = slot_times[slot_idx] if slot_idx < len(slot_times) else ""
            room = row[start].strip() if start < len(row) else ""
            course = row[start + 1].strip() if start + 1 < len(row) else ""
            teacher = row[start + 2].strip() if start + 2 < len(row) else ""
            if not course:
                continue
            _add_entry(
                store,
                day=current_day,
                time=time,
                room=room,
                course=course,
                teacher=teacher,
            )

    sections = sorted(store.keys())
    return ParsedCsvRoutine(
        path=str(path),
        department=infer_department_from_csv(path),
        title=title or path.stem,
        format="cse_grid",
        weekly_by_section=store,
        sections=sections,
    )


def _parse_swe_grid(rows: List[List[str]], path: Path) -> ParsedCsvRoutine:
    title = "Software Engineering class routine"
    for row in rows[:6]:
        if any("Software Engineering" in (c or "") for c in row):
            title = "Department of Software Engineering — class routine"
            break

    store: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    current_day = ""
    slot_times: List[str] = []
    time_cols: List[int] = []

    for row in rows:
        if not any((c or "").strip() for c in row):
            continue

        times_found: List[Tuple[int, str]] = []
        for idx, cell in enumerate(row):
            cell_text = (cell or "").strip()
            if _TIME_RE.search(cell_text):
                times_found.append((idx, cell_text.replace(" ", "")))

        if times_found and (row[0] or "").strip().lower() != "class":
            time_cols = [i for i, _ in times_found]
            slot_times = [t for _, t in times_found]
            continue

        first = (row[0] or "").strip()
        if first and _DAY_RE.fullmatch(first.upper().strip()):
            current_day = _title_case_day(first)
            continue

        if not current_day or not time_cols:
            continue

        if first.lower() == "class":
            continue

        room = first
        for slot_idx, col in enumerate(time_cols):
            time = slot_times[slot_idx] if slot_idx < len(slot_times) else ""
            course_col = col
            teacher_col = col + 1
            course = row[course_col].strip() if course_col < len(row) else ""
            teacher = row[teacher_col].strip() if teacher_col < len(row) else ""
            _add_entry(
                store,
                day=current_day,
                time=time,
                room=room,
                course=course,
                teacher=teacher,
            )

    sections = sorted(store.keys())
    return ParsedCsvRoutine(
        path=str(path),
        department="SWE",
        title=title,
        format="swe_grid",
        weekly_by_section=store,
        sections=sections,
    )


def _detect_format(path: Path, rows: List[List[str]]) -> str:
    name = path.name.lower()
    if "swe" in name or "software" in name:
        return "swe_grid"
    joined = "\n".join(",".join(r) for r in rows[:12])
    if "Department of Software Engineering" in joined:
        return "swe_grid"
    if "Class Routine for CSE" in joined or "cse-class-routine" in name:
        return "cse_grid"
    if _DAY_RE.search(joined) and "Room,Course,Teacher" in joined.replace(" ", ""):
        return "cse_grid"
    return "generic"


@lru_cache(maxsize=8)
def load_parsed_csv(path_str: str) -> ParsedCsvRoutine:
    path = Path(path_str)
    if not path.is_file():
        return ParsedCsvRoutine(
            path=path_str,
            department="",
            title="",
            format="missing",
        )

    try:
        with path.open(encoding="utf-8", errors="ignore", newline="") as handle:
            rows = list(csv.reader(handle))
    except Exception as e:
        logger.warning("Failed to read routine CSV %s: %s", path, e)
        return ParsedCsvRoutine(
            path=str(path),
            department="",
            title="",
            format="error",
        )

    fmt = _detect_format(path, rows)
    if fmt == "swe_grid":
        return _parse_swe_grid(rows, path)
    if fmt == "cse_grid":
        return _parse_cse_grid(rows, path)

    return ParsedCsvRoutine(
        path=str(path),
        department=infer_department_from_csv(path),
        title=path.stem,
        format="generic",
    )


def get_csv_routine(
    section: str,
    day: Optional[str] = None,
    *,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """Return structured routine for a section from bundled CSV data."""
    sec = normalize_section(section)
    if not sec:
        return {
            "section": None,
            "source": "none",
            "error": "section_required",
        }

    paths: List[Path] = []
    preferred = resolve_csv_path(department)
    if preferred:
        paths.append(preferred)
    for path in list_csv_routine_files():
        if path not in paths:
            paths.append(path)

    day_key = _title_case_day(day) if day else None

    for path in paths:
        parsed = load_parsed_csv(str(path.resolve()))
        weekly = parsed.weekly_by_section.get(sec)
        if not weekly:
            continue

        payload: Dict[str, Any] = {
            "section": sec,
            "department": parsed.department or department,
            "source": "csv",
            "csv_file": path.name,
            "title": parsed.title,
            "format": parsed.format,
        }
        if day_key:
            payload.update({"day": day_key, "items": weekly.get(day_key, [])})
            return payload

        payload["weekly"] = weekly
        return payload

    # Section not found — report what CSVs we searched
    available: List[str] = []
    for path in paths:
        parsed = load_parsed_csv(str(path.resolve()))
        available.extend(parsed.sections[:20])

    return {
        "section": sec,
        "department": department,
        "source": "none",
        "error": "section_not_in_csv",
        "hint": "Section not found in bundled CSV routines. Check section code (e.g. 66_C).",
        "csv_files_searched": [p.name for p in paths],
        "sample_sections": sorted(set(available))[:15],
    }


def list_csv_routine_catalog(department: Optional[str] = None) -> Dict[str, Any]:
    """Summarize available CSV routine files and section counts."""
    paths = [resolve_csv_path(department)] if resolve_csv_path(department) else list_csv_routine_files()
    paths = [p for p in paths if p]

    files: List[Dict[str, Any]] = []
    for path in paths:
        parsed = load_parsed_csv(str(path.resolve()))
        files.append(
            {
                "file": path.name,
                "department": parsed.department,
                "title": parsed.title,
                "format": parsed.format,
                "section_count": len(parsed.sections),
                "sections_sample": parsed.sections[:12],
            }
        )
    return {"source": "csv", "files": files}
