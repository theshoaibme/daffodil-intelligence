"""Local file operations with path root enforcement."""

from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .security import get_allowed_roots


class PathPolicyError(Exception):
    pass


def _resolve_allowed(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    roots = [Path(r).expanduser().resolve() for r in get_allowed_roots()]
    for root in roots:
        try:
            p.relative_to(root)
            return p
        except ValueError:
            continue
    raise PathPolicyError(f"Path not in allowed roots: {path}")


def read_file(path: str, max_chars: int = 5000) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    if not p.is_file():
        return {"error": f"Not a file: {path}"}
    text = p.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(p),
        "content": text[:max_chars],
        "truncated": len(text) > max_chars,
        "total_chars": len(text),
        "size_bytes": p.stat().st_size,
    }


def write_file(path: str, content: str, mode: str = "write") -> Dict[str, Any]:
    p = _resolve_allowed(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
    else:
        p.write_text(content, encoding="utf-8")
    return {"path": str(p), "bytes_written": len(content.encode()), "mode": mode}


def list_directory(path: str, recursive: bool = False, limit: int = 200) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}
    entries: List[Dict[str, Any]] = []
    items = sorted(p.rglob("*") if recursive else p.iterdir())[:limit]
    for item in items:
        entries.append({
            "name": item.name,
            "path": str(item.relative_to(p)) if recursive else item.name,
            "type": "dir" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
        })
    return {"path": str(p), "entries": entries, "count": len(entries)}


def create_directory(path: str) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    p.mkdir(parents=True, exist_ok=True)
    return {"path": str(p), "created": True}


def move_path(src: str, dst: str) -> Dict[str, Any]:
    s = _resolve_allowed(src)
    d = _resolve_allowed(dst)
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d))
    return {"from": str(s), "to": str(d)}


def copy_path(src: str, dst: str) -> Dict[str, Any]:
    s = _resolve_allowed(src)
    d = _resolve_allowed(dst)
    if s.is_dir():
        shutil.copytree(str(s), str(d), dirs_exist_ok=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(s), str(d))
    return {"from": str(s), "to": str(d)}


def delete_path(path: str) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    if p.is_dir():
        shutil.rmtree(p)
    elif p.is_file():
        p.unlink()
    else:
        return {"error": f"Not found: {path}"}
    return {"deleted": str(p)}


def file_info(path: str) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    if not p.exists():
        return {"error": f"Not found: {path}"}
    st = p.stat()
    mime, _ = mimetypes.guess_type(str(p))
    return {
        "path": str(p),
        "type": "dir" if p.is_dir() else "file",
        "size_bytes": st.st_size,
        "mtime": st.st_mtime,
        "mime": mime,
    }


def search_files(path: str, glob_pattern: str = "*", limit: int = 100) -> Dict[str, Any]:
    p = _resolve_allowed(path)
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}
    matches = []
    for item in sorted(p.glob(glob_pattern))[:limit]:
        matches.append({
            "name": item.name,
            "path": str(item),
            "type": "dir" if item.is_dir() else "file",
        })
    return {"path": str(p), "pattern": glob_pattern, "matches": matches, "count": len(matches)}
