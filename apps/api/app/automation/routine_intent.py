"""Detect class-routine query types from user messages."""

from __future__ import annotations

import re
from typing import Optional

_COURSE_CODE_IN_MSG = re.compile(r"\b([A-Z]{2,4}\d{3})\b", re.I)

_QUERY_STOPWORDS = frozenset(
    {
        "weekly",
        "class",
        "routine",
        "for",
        "improvement",
        "exam",
        "final",
        "schedule",
        "show",
        "me",
        "what",
        "is",
        "the",
        "date",
        "when",
        "time",
        "room",
        "my",
        "a",
        "an",
        "of",
        "on",
        "at",
        "and",
        "or",
        "to",
        "in",
        "tell",
        "about",
    }
)

IMPROVEMENT_EXAM_PHRASES = (
    "improvement exam",
    "improvement routine",
    "final improvement",
    "improvement test",
    "improvement examination",
)

CLASS_ROUTINE_PHRASES = (
    "class routine",
    "class schedule",
    "weekly routine",
    "weekly class routine",
    "today class",
    "tomorrow class",
    "today's class",
    "tomorrow's class",
    "today class routine",
    "tomorrow class routine",
    "today routine",
    "tomorrow routine",
)


def is_improvement_exam_routine(message: str) -> bool:
    lower = (message or "").lower()
    return any(p in lower for p in IMPROVEMENT_EXAM_PHRASES)


def wants_class_routine(message: str) -> bool:
    lower = (message or "").lower()
    if is_improvement_exam_routine(lower):
        return True
    return any(p in lower for p in CLASS_ROUTINE_PHRASES)


def extract_course_search_query(message: str) -> Optional[str]:
    """Course code (CSE421) or title keywords (computer graphics) from a user message."""
    text = (message or "").strip()
    if not text:
        return None
    code_match = _COURSE_CODE_IN_MSG.search(text)
    if code_match:
        return code_match.group(1).upper()
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    kept = [t for t in tokens if t not in _QUERY_STOPWORDS and len(t) > 2]
    if not kept:
        return None
    return " ".join(kept)


def course_matches_query(course_field: str, query: str) -> bool:
    if not query:
        return True
    course = (course_field or "").strip()
    if not course:
        return False
    q = query.strip()
    if _COURSE_CODE_IN_MSG.fullmatch(q):
        return q.upper() in course.upper()
    words = q.lower().split()
    lower = course.lower()
    return bool(words) and all(word in lower for word in words)
