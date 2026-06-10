"""Section normalization and department routine file uploads (no hardcoded departments)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SECTION_CODE = re.compile(r"\b(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\b", re.I)

ROUTINE_DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "routines"


def normalize_department(department: Optional[str]) -> str:
    if not department:
        return ""
    return department.strip().upper().replace("-", " ").replace("  ", " ")


def normalize_department_key(department: Optional[str]) -> str:
    key = normalize_department(department)
    return key.replace(" ", "_") if key else ""


def normalize_section(section: Optional[str]) -> str:
    if not section:
        return ""
    raw = section.strip().upper().replace(" ", "_")
    match = _SECTION_CODE.search(raw)
    return match.group(1).upper() if match else raw


def resolve_section(
    *,
    section: Optional[str] = None,
    department: Optional[str] = None,
) -> str:
    """Explicit section, else default_section from an uploaded department manifest."""
    normalized = normalize_section(section)
    if normalized:
        return normalized

    dept_key = normalize_department_key(department)
    if dept_key:
        manifest = load_department_manifest(dept_key)
        default = manifest.get("default_section")
        if default:
            return normalize_section(str(default))
    return ""


def department_data_dir(department: Optional[str]) -> Path:
    key = normalize_department_key(department) or "GENERAL"
    return ROUTINE_DATA_ROOT / key


def load_department_manifest(department: Optional[str]) -> Dict[str, Any]:
    path = department_data_dir(department) / "manifest.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Invalid routine manifest %s: %s", path, e)
        return {}


def section_catalog_path(department: Optional[str], section: str) -> Optional[Path]:
    sec = normalize_section(section)
    if not sec:
        return None
    dept_dir = department_data_dir(department)
    candidates = [
        dept_dir / f"{sec}.json",
        ROUTINE_DATA_ROOT / "sections" / f"{sec}.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_uploaded_catalog(
    section: str,
    department: Optional[str] = None,
) -> Optional[Dict[str, Dict[str, List[Dict[str, Any]]]]]:
    path = section_catalog_path(department, section)
    if not path:
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        weekly = raw.get("weekly") if isinstance(raw, dict) else raw
        if isinstance(weekly, dict):
            return {normalize_section(section): weekly}
    except Exception as e:
        logger.warning("Failed to load routine catalog %s: %s", path, e)
    return None


def save_routine_upload(
    *,
    department: str,
    section: str,
    filename: str,
    content: bytes,
) -> Dict[str, Any]:
    dept_key = normalize_department_key(department) or "GENERAL"
    sec = resolve_section(section=section, department=department)
    if not sec:
        raise ValueError("section is required for routine upload")
    dest_dir = ROUTINE_DATA_ROOT / dept_key
    dest_dir.mkdir(parents=True, exist_ok=True)

    lower = filename.lower()
    if lower.endswith(".json"):
        dest = dest_dir / f"{sec}.json"
        dest.write_bytes(content)
        parsed = json.loads(content.decode("utf-8", errors="ignore"))
        _update_manifest(dest_dir, sec, source=filename)
        return {"department": dept_key, "section": sec, "format": "json", "path": str(dest), "parsed": bool(parsed)}

    if lower.endswith(".pdf"):
        dest = dest_dir / f"{sec}.pdf"
        dest.write_bytes(content)
        text = _extract_pdf_text(dest)
        if text.strip():
            dest.with_suffix(".pdf.txt").write_text(text[:50000], encoding="utf-8")
        _update_manifest(dest_dir, sec, source=filename)
        return {
            "department": dept_key,
            "section": sec,
            "format": "pdf",
            "path": str(dest),
            "text_chars": len(text),
        }

    dest = dest_dir / f"{sec}.txt"
    dest.write_bytes(content)
    _update_manifest(dest_dir, sec, source=filename)
    return {"department": dept_key, "section": sec, "format": "text", "path": str(dest)}


def _update_manifest(dest_dir: Path, section: str, *, source: str) -> None:
    manifest_path = dest_dir / "manifest.json"
    manifest: Dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    sections = manifest.get("sections") or []
    sec = normalize_section(section)
    if sec and sec not in sections:
        sections.append(sec)
    manifest["sections"] = sections
    if not manifest.get("default_section"):
        manifest["default_section"] = sec
    manifest["last_upload"] = source
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
