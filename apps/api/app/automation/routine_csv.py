"""Parse department class routines from CSV files in data/routines/."""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .routine_intent import course_matches_query
from .routine_resolver import (
    ROUTINE_DATA_ROOT,
    normalize_department_key,
    normalize_section,
    resolve_routine_day,
)

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

    day_key = resolve_routine_day(day) if day else None

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


_IMPROVEMENT_EXAM_TITLE_RE = re.compile(
    r"Final\s+Improvement\s+Exam\s+Routine",
    re.I,
)
_IMPROVEMENT_DATE_RE = re.compile(
    r"Date:\s*([\d-]+)\s*\(([^)]+)\)",
    re.I,
)
_IMPROVEMENT_TIME_RE = re.compile(r"Time:\s*([^,]+)", re.I)
_COURSE_CODE_ROW_RE = re.compile(r"^([A-Z]{2,4}\d{3})", re.I)
_ROOM_HEADER_WORDS = frozenset({"number", "room"})


def find_improvement_exam_csv() -> Optional[Path]:
    for path in list_csv_routine_files():
        if "improvement" in path.name.lower():
            return path
    return None


def _append_room_fragment(room: str, fragment: str) -> str:
    frag = (fragment or "").strip()
    if not frag:
        return room
    return f"{room} {frag}".strip() if room else frag


def _row_cells(row: List[str]) -> List[str]:
    return [(c or "").strip() for c in row]


def _is_course_header_row(line: str) -> bool:
    return "Course Code" in line and "Course Title" in line


def _room_fragments(cells: List[str]) -> List[str]:
    out: List[str] = []
    for cell in cells:
        if not cell or cell.lower() in _ROOM_HEADER_WORDS:
            continue
        if _COURSE_CODE_ROW_RE.match(cell):
            continue
        if "Course Code" in cell or "Students" in cell:
            continue
        out.append(cell)
    return out


def _is_room_fragment_text(text: str) -> bool:
    lower = text.lower()
    return lower in {"knowledge", "tower", "number"} or text.isdigit()


def _build_default_room(fragments: List[str]) -> str:
    nums: List[str] = []
    words: List[str] = []
    for frag in fragments:
        if frag.isdigit():
            if frag not in nums:
                nums.append(frag)
        elif frag.lower() not in _ROOM_HEADER_WORDS and frag.lower() not in {
            w.lower() for w in words
        }:
            words.append(frag)
    return " ".join(nums + words).strip()


def _finalize_improvement_session(session: Dict[str, Any]) -> None:
    """Apply session hall to rows and drop orphan code-only lines."""
    header_frags = list(session.get("room_fragments") or [])
    item_frags: List[str] = []
    for item in session.get("items") or []:
        room = (item.get("room") or "").strip()
        if room:
            for part in room.split():
                if part not in item_frags:
                    item_frags.append(part)

    default_room = _build_default_room(header_frags + item_frags)
    session["default_room"] = default_room

    cleaned: List[Dict[str, Any]] = []
    for item in session.get("items") or []:
        course = (item.get("course") or "").strip()
        if not course:
            continue
        parts = course.split(None, 1)
        if len(parts) == 1 and _COURSE_CODE_ROW_RE.fullmatch(parts[0].replace("/", "")):
            continue

        room = (item.get("room") or "").strip()
        if not room or room in {"Tower", "Knowledge"} or room.isdigit():
            room = default_room
        elif default_room and len(room.split()) < len(default_room.split()):
            room = default_room

        cleaned.append(
            {
                "date": item.get("date") or "",
                "day": item.get("day") or "",
                "time": item.get("time") or "",
                "course": course,
                "room": room or default_room,
            }
        )
    session["items"] = cleaned


def parse_improvement_exam_sessions(path: Path) -> List[Dict[str, Any]]:
    """Parse bundled improvement-exam CSV into dated exam sessions."""
    try:
        with path.open(encoding="utf-8", errors="ignore", newline="") as handle:
            rows = list(csv.reader(handle))
    except Exception as e:
        logger.warning("Failed to read improvement exam CSV %s: %s", path, e)
        return []

    sessions: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    title = path.stem.replace("-", " ").title()
    after_course_header = False

    for row in rows:
        cells = _row_cells(row)
        col0 = cells[0] if cells else ""
        col1 = cells[1] if len(cells) > 1 else ""
        col2 = cells[2] if len(cells) > 2 else ""
        line = ",".join(row)

        if _IMPROVEMENT_EXAM_TITLE_RE.search(line):
            if current and current.get("items"):
                _finalize_improvement_session(current)
                sessions.append(current)
            current = {
                "title": "Final Improvement Exam Routine",
                "time": "",
                "reporting_time": "",
                "date": "",
                "day": "",
                "room_fragments": [],
                "items": [],
            }
            after_course_header = False
            if "Spring" in line or "Fall" in line:
                current["title"] = line.strip('", ')
            continue

        if not current:
            continue

        date_match = _IMPROVEMENT_DATE_RE.search(line)
        if date_match:
            current["date"] = date_match.group(1).strip()
            current["day"] = _title_case_day(date_match.group(2))
            continue

        time_match = _IMPROVEMENT_TIME_RE.search(line)
        if time_match and "Reporting" not in line:
            current["time"] = time_match.group(1).strip()
            continue

        if "Reporting time" in line:
            current["reporting_time"] = line.split("Reporting time", 1)[-1].strip(" ,")
            continue

        if col0.startswith("***"):
            continue

        if _is_course_header_row(line):
            current["room_fragments"] = []
            after_course_header = True
            continue

        course_match = _COURSE_CODE_ROW_RE.match(col0) if col0 else None

        if not col0 and col1 and current["items"] and not _is_room_fragment_text(col1):
            if not col2 and not col1.lower().startswith("course"):
                current["items"][-1]["course"] = (
                    f"{current['items'][-1]['course']} {col1}".strip()
                )
                continue

        if course_match and not col1.strip() and current["items"]:
            prev = current["items"][-1]
            prev_code = (prev.get("course") or "").split()[0]
            if "/" in prev_code or prev_code.endswith("/"):
                title_rest = " ".join((prev.get("course") or "").split()[1:])
                merged = f"{prev_code.rstrip('/')}/{col0.strip().upper()} {title_rest}".strip()
                prev["course"] = merged
                continue

        if course_match:
            after_course_header = False
            code = course_match.group(1).upper()
            title_cell = col1
            if col0.endswith("/"):
                course_name = f"{col0.upper()} {title_cell}".strip()
            else:
                course_name = f"{code} {title_cell}".strip()

            current["items"].append(
                {
                    "course": course_name,
                    "room": col2,
                    "time": current.get("time") or "",
                    "date": current.get("date") or "",
                    "day": current.get("day") or "",
                }
            )
            continue

        frags = _room_fragments(cells)
        if not frags:
            continue

        if after_course_header and not current["items"]:
            current["room_fragments"].extend(frags)
            continue

        if current["items"] and all(_is_room_fragment_text(f) for f in frags):
            last = current["items"][-1]
            last["room"] = _append_room_fragment(last.get("room") or "", " ".join(frags))

    if current and current.get("items"):
        _finalize_improvement_session(current)
        sessions.append(current)

    if not title and sessions:
        title = sessions[0].get("title") or title
    for sess in sessions:
        sess.setdefault("title", title)
    return sessions


def _filter_improvement_items(
    items: List[Dict[str, Any]], course_query: Optional[str]
) -> List[Dict[str, Any]]:
    if not course_query:
        return items
    return [
        item
        for item in items
        if course_matches_query(str(item.get("course") or ""), course_query)
    ]


def get_improvement_exam_routine(
    day: Optional[str] = None,
    course_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Load improvement exam routine from data/routines/*improvement*.csv (no section)."""
    path = find_improvement_exam_csv()
    if not path:
        return {
            "source": "none",
            "routine_type": "improvement_exam",
            "error": "not_found",
            "hint": "No improvement exam CSV in data/routines/.",
        }

    sessions = parse_improvement_exam_sessions(path)
    if not sessions:
        return {
            "source": "none",
            "routine_type": "improvement_exam",
            "csv_file": path.name,
            "error": "parse_failed",
            "hint": f"Could not parse {path.name}.",
        }

    title = sessions[0].get("title") or "Final Improvement Exam Routine"
    all_items: List[Dict[str, Any]] = []
    weekly: Dict[str, List[Dict[str, Any]]] = {}
    for sess in sessions:
        for item in sess["items"]:
            row = dict(item)
            row.setdefault("time", sess.get("time") or "")
            row.setdefault("date", sess.get("date") or "")
            row.setdefault("day", sess.get("day") or "")
            all_items.append(row)
            day_key = row.get("day") or "Unknown"
            weekly.setdefault(day_key, []).append(row)

    query = (course_query or "").strip() or None
    if query:
        all_items = _filter_improvement_items(all_items, query)
        weekly = {}
        for item in all_items:
            day_name = item.get("day") or "Unknown"
            weekly.setdefault(day_name, []).append(item)
        if not all_items:
            return {
                "source": "none",
                "routine_type": "improvement_exam",
                "course_query": query,
                "error": "course_not_found",
                "hint": f"No improvement exam entry matching '{query}' in {path.name}.",
                "csv_file": path.name,
            }

    day_key = resolve_routine_day(day) if day else None
    payload: Dict[str, Any] = {
        "source": "csv",
        "routine_type": "improvement_exam",
        "csv_file": path.name,
        "title": title,
        "sessions": sessions,
        "weekly": weekly,
    }
    if query:
        payload["course_query"] = query
    if day_key:
        payload["day"] = day_key
        payload["items"] = weekly.get(day_key, [])
        return payload

    payload["items"] = all_items
    return payload


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
