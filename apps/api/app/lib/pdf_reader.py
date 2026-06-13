"""Fast PDF text extraction — sidecar cache, in-memory LRU, query/page filters."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MAX_CACHE_ENTRIES = 128
_MAX_SIDECAR_CHARS = 120_000


@dataclass
class _CacheEntry:
    mtime_ns: int
    text: str
    source: str


_text_cache: Dict[str, _CacheEntry] = {}


def _cache_key(path: Path) -> str:
    return str(path.resolve())


def _cache_get(path: Path) -> Optional[_CacheEntry]:
    key = _cache_key(path)
    entry = _text_cache.get(key)
    if not entry:
        return None
    try:
        if path.stat().st_mtime_ns != entry.mtime_ns:
            _text_cache.pop(key, None)
            return None
    except OSError:
        _text_cache.pop(key, None)
        return None
    return entry


def _cache_set(path: Path, text: str, source: str) -> None:
    if len(_text_cache) >= _MAX_CACHE_ENTRIES:
        _text_cache.pop(next(iter(_text_cache)))
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0
    _text_cache[_cache_key(path)] = _CacheEntry(mtime_ns=mtime_ns, text=text, source=source)


def extract_pdf_text(
    path: Path,
    *,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
) -> str:
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(str(path))
        total = len(reader.pages)
        start = max(1, int(page_start or 1))
        end = min(total, int(page_end or total))
        if start > end:
            return ""
        chunks: List[str] = []
        for index in range(start - 1, end):
            chunks.append(reader.pages[index].extract_text() or "")
        return "\n".join(chunks)
    except Exception as e:
        logger.debug("PDF extract failed %s: %s", path, e)
        return ""


def ensure_pdf_sidecar(pdf_path: Path) -> Path:
    """Write `{file}.pdf.txt` once; later reads skip PDF parsing."""
    sidecar = pdf_path.with_suffix(pdf_path.suffix + ".txt")
    try:
        if sidecar.is_file() and sidecar.stat().st_mtime >= pdf_path.stat().st_mtime:
            return sidecar
    except OSError:
        return sidecar

    text = extract_pdf_text(pdf_path)
    if text.strip():
        sidecar.write_text(text[:_MAX_SIDECAR_CHARS], encoding="utf-8")
    return sidecar


def slice_by_query(text: str, query: str, *, max_lines: int = 50) -> str:
    if not text or not query:
        return text
    q = query.strip().lower()
    if not q:
        return text

    hits = [line for line in text.splitlines() if q in line.lower()]
    if hits:
        return "\n".join(hits[:max_lines]).strip()

    words = [w for w in q.split() if len(w) > 2]
    if not words:
        return text
    hits = [
        line
        for line in text.splitlines()
        if any(w in line.lower() for w in words)
    ]
    return "\n".join(hits[:max_lines]).strip()


def read_pdf_fast(
    file_path: str | Path,
    *,
    query: Optional[str] = None,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
    max_chars: int = 8000,
) -> Dict[str, Any]:
    """Read any PDF or plain-text file with cache + sidecar acceleration."""
    started = time.perf_counter()
    path = Path(file_path).expanduser()
    if not path.is_file():
        return {
            "path": str(path),
            "error": "not_found",
            "read_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    suffix = path.suffix.lower()
    source = "text"
    was_cached = False

    if suffix == ".pdf":
        sidecar = ensure_pdf_sidecar(path)
        if sidecar.is_file():
            read_path = sidecar
            source = "pdf_sidecar"
        else:
            read_path = path
            source = "pdf"
    else:
        read_path = path
        source = "text"

    text = ""
    cached = _cache_get(read_path)
    if cached:
        text = cached.text
        was_cached = True
        source = cached.source
    elif source == "pdf":
        text = extract_pdf_text(path, page_start=page_start, page_end=page_end)
        if text.strip():
            _cache_set(read_path, text, source)
    else:
        try:
            text = read_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {
                "path": str(path.resolve()),
                "error": str(e),
                "read_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        text = text.strip()
        if text:
            _cache_set(read_path, text, source)

    if not text:
        return {
            "path": str(path.resolve()),
            "error": "empty_document",
            "read_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    if source == "pdf_sidecar" and (page_start or page_end):
        text = extract_pdf_text(path, page_start=page_start, page_end=page_end) or text

    total_chars = len(text)
    if query:
        text = slice_by_query(text, query) or text

    excerpt = text[:max_chars]
    return {
        "path": str(path.resolve()),
        "source": source,
        "text": excerpt,
        "chars": len(excerpt),
        "total_chars": total_chars,
        "truncated": len(excerpt) < len(text),
        "filtered": bool(query),
        "cached": was_cached,
        "read_ms": round((time.perf_counter() - started) * 1000, 2),
    }
