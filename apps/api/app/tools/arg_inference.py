"""Heuristic extraction of tool kwargs from a natural-language prompt."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseTool

_STUDENT_ID_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4,}\b"),
    re.compile(r"\b\d{10,16}\b"),
)


def _extract_student_id(prompt: str) -> Optional[str]:
    for pattern in _STUDENT_ID_PATTERNS:
        match = pattern.search(prompt)
        if match:
            return match.group(0)
    return None


def infer_tool_kwargs(
    tool: BaseTool,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build keyword arguments for ``registry.execute`` from prompt + session context."""
    context = context or {}
    prompt = (prompt or "").strip()
    kwargs: Dict[str, Any] = {}

    for param in tool.parameters:
        name = param.name

        if name == "student_id":
            value = context.get("student_id") or _extract_student_id(prompt)
            if value:
                kwargs[name] = value
        elif name == "query":
            kwargs[name] = context.get("query") or prompt
        elif name == "path":
            match = re.search(r'(?:^|[\s"\'])([/~][\w./_-]+|\w[\w./_-]*\.\w+)', prompt)
            if match:
                kwargs[name] = match.group(1)
            elif context.get("path"):
                kwargs[name] = context["path"]
        elif name == "route":
            match = re.search(r"(?:route|shuttle|bus)\s+([\w\s-]+)", prompt, re.I)
            if match:
                kwargs[name] = match.group(1).strip()
            elif context.get("route"):
                kwargs[name] = context["route"]
        elif name == "book_id":
            match = re.search(r"\b(?:book[_-]?id[:\s]+)?([A-Za-z0-9-]{4,})\b", prompt, re.I)
            if match and name not in kwargs:
                kwargs[name] = match.group(1)
        elif name == "semester":
            match = re.search(r"\b(Spring|Fall|Summer|Autumn|Winter)\s*\d{4}\b", prompt, re.I)
            if match:
                kwargs[name] = match.group(0)
        elif name == "course_code":
            match = re.search(r"\b[A-Z]{2,4}\d{3}\b", prompt)
            if match:
                kwargs[name] = match.group(0)
        elif name in ("content", "text", "note", "message"):
            kwargs[name] = context.get(name) or prompt
        elif name == "command":
            match = re.search(r"(?:run|execute)\s+(.+)$", prompt, re.I)
            kwargs[name] = match.group(1).strip() if match else prompt
        elif name == "code":
            kwargs[name] = context.get("code") or prompt
        elif name == "url":
            match = re.search(r"https?://\S+", prompt)
            if match:
                kwargs[name] = match.group(0)
        elif param.default is not None:
            kwargs[name] = param.default

    return kwargs


def missing_required(tool: BaseTool, kwargs: Dict[str, Any]) -> List[str]:
    return [p.name for p in tool.parameters if p.required and p.name not in kwargs]
