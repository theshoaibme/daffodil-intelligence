"""Validate assistant text so structured UI blocks are not duplicated in prose."""

from __future__ import annotations

import re
from typing import Any, Dict, List

_COURSE_CODE = re.compile(r"\b[A-Z]{2,4}\d{3}\b", re.I)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _blocks_text_blob(ui_blocks: List[Dict[str, Any]]) -> str:
    parts: List[str] = []

    def walk_rows(rows: Any) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            if isinstance(row, dict):
                parts.extend(str(v) for v in row.values() if v)

    for block in ui_blocks:
        if not isinstance(block, dict):
            continue
        data = block.get("data") or {}
        if block.get("schema") == "data_table":
            walk_rows(data.get("rows"))
            if data.get("title"):
                parts.append(str(data["title"]))
        elif block.get("schema") == "tabs":
            for tab in data.get("tabs") or []:
                if not isinstance(tab, dict):
                    continue
                inner = tab.get("block") or {}
                inner_data = inner.get("data") or {}
                walk_rows(inner_data.get("rows"))
                if inner.get("title"):
                    parts.append(str(inner["title"]))
        elif block.get("schema") == "status_card":
            msg = data.get("message")
            if msg:
                parts.append(str(msg))

    return " ".join(parts)


def has_structured_data_blocks(ui_blocks: List[Dict[str, Any]]) -> bool:
    for block in ui_blocks:
        if not isinstance(block, dict):
            continue
        schema = block.get("schema")
        data = block.get("data") or {}
        if schema == "data_table" and data.get("rows"):
            return True
        if schema == "tabs" and data.get("tabs"):
            return True
    return False


def content_redundant_with_blocks(content: str, ui_blocks: List[Dict[str, Any]]) -> bool:
    """True when prose repeats what tables/tabs already show."""
    text = (content or "").strip()
    if not text:
        return False
    blob = _blocks_text_blob(ui_blocks)
    if not blob.strip():
        return False

    norm_text = _normalize(text)
    norm_blob = _normalize(blob)

    if norm_text in norm_blob or norm_blob in norm_text:
        return True

    # Course code + schedule details already in table
    code_match = _COURSE_CODE.search(text)
    if code_match and code_match.group(0).upper() in blob.upper():
        schedule_hints = ("room", "sunday", "monday", "tuesday", "am", "pm", "—", "-")
        if any(h in norm_text for h in schedule_hints):
            return True

    text_words = {w for w in re.findall(r"[a-z0-9]+", norm_text) if len(w) > 2}
    blob_words = set(re.findall(r"[a-z0-9]+", norm_blob))
    if text_words and len(text_words) <= 12 and text_words.issubset(blob_words):
        return True

    return False


def validate_assistant_response(
    content: str,
    ui_blocks: List[Dict[str, Any]] | None = None,
) -> str:
    """Return content safe to show alongside UI blocks (empty if redundant)."""
    text = (content or "").strip()
    blocks = ui_blocks or []
    if not text or not blocks:
        return text
    if has_structured_data_blocks(blocks) and content_redundant_with_blocks(text, blocks):
        # Keep substantive prose (e.g. research synthesis) even when blocks exist.
        if len(text) > 500 or "\n\n" in text or text.count(".") >= 3:
            return text
        return ""
    return text
