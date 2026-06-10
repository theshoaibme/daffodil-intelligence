"""Routine document lookup — resolves department paths, delegates to lib.pdf_reader."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..lib.pdf_reader import read_pdf_fast, slice_by_query
from .routine_resolver import (
    department_data_dir,
    normalize_department_key,
    normalize_section,
)

_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_DAY_RE = re.compile(
    r"^\s*(" + "|".join(_WEEKDAYS) + r")\b",
    re.I | re.M,
)


def slice_by_day(text: str, day: str) -> str:
    if not text or not day:
        return text
    target = day.strip().capitalize()
    if target not in _WEEKDAYS:
        return text

    matches = list(_DAY_RE.finditer(text))
    if not matches:
        return text

    for i, match in enumerate(matches):
        name = match.group(1).capitalize()
        if name != target:
            continue
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return text


def _candidate_paths(department: Optional[str], section: Optional[str]) -> List[Path]:
    dept_dir = department_data_dir(department)
    if not dept_dir.is_dir():
        return []

    sec = normalize_section(section) if section else ""
    paths: List[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        key = str(path)
        if key not in seen and path.is_file():
            seen.add(key)
            paths.append(path)

    if sec:
        add(dept_dir / f"{sec}.pdf")
        add(dept_dir / f"{sec}.pdf.txt")
        add(dept_dir / f"{sec}.txt")
        add(dept_dir / f"{sec}.json")

    for name in ("routine.pdf", "routine.pdf.txt", "routine.txt"):
        add(dept_dir / name)

    return paths


def _read_json_routine(path: Path, max_chars: int) -> Dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(raw.get("weekly") or raw, ensure_ascii=False)
    except Exception:
        text = ""
    excerpt = text[:max_chars]
    return {
        "path": str(path.resolve()),
        "source": "json",
        "text": excerpt,
        "chars": len(excerpt),
        "total_chars": len(text),
        "cached": False,
    }


def read_routine_pdf_fast(
    department: Optional[str],
    section: Optional[str] = None,
    *,
    day: Optional[str] = None,
    query: Optional[str] = None,
    max_chars: int = 4000,
) -> Dict[str, Any]:
    """Find department routine file, then read via fast PDF/text reader."""
    started = time.perf_counter()
    dept_key = normalize_department_key(department) or "GENERAL"
    sec = normalize_section(section) if section else ""

    for path in _candidate_paths(department, sec or None):
        if path.suffix.lower() == ".json":
            payload = _read_json_routine(path, max_chars)
            if not payload.get("text"):
                continue
            payload.update({"department": dept_key, "section": sec or None})
            payload["read_ms"] = round((time.perf_counter() - started) * 1000, 2)
            return payload

        result = read_pdf_fast(path, max_chars=max_chars)
        if result.get("error"):
            continue

        text = result.get("text") or ""
        total = result.get("total_chars") or len(text)
        if day:
            text = slice_by_day(text, day)
        elif query:
            text = slice_by_query(text, query) or text

        excerpt = text[:max_chars]
        return {
            "department": dept_key,
            "section": sec or None,
            "path": result.get("path"),
            "source": result.get("source"),
            "text": excerpt,
            "chars": len(excerpt),
            "total_chars": total,
            "filtered": bool(day or query),
            "cached": result.get("cached", False),
            "read_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    return {
        "department": dept_key,
        "section": sec or None,
        "error": "not_found",
        "read_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def read_department_routine_source(
    department: Optional[str],
    section: Optional[str] = None,
) -> Optional[str]:
    result = read_routine_pdf_fast(department, section, max_chars=12_000)
    return result.get("text") or None
