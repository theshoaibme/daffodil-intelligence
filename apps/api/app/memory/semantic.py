"""
Semantic Memory
===============
In-process keyword note store used only when PostgreSQL is unavailable.
Production data lives in ``agent_memories`` via ``MemoryRepository``.
"""

from __future__ import annotations

import logging
import re
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"\W+", (text or "").lower()) if t]


class SemanticMemory:
    """Ephemeral keyword note store (no file persistence)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._notes: List[Dict[str, Any]] = []
        self._backend = "memory"

    def add(self, text: str, user_id: Any = 0, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        note = {
            "id": uuid.uuid4().hex,
            "text": text,
            "user_id": str(user_id),
            "metadata": metadata or {},
            "created_at": time.time(),
        }
        with self._lock:
            self._notes.append(note)
        return note

    def search(self, query: str, user_id: Any = None, k: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            candidates = list(self._notes)

        if user_id is not None:
            candidates = [n for n in candidates if n.get("user_id") == str(user_id)]

        q_tokens = set(_tokenize(query))
        if not q_tokens:
            ranked = sorted(candidates, key=lambda n: n.get("created_at", 0), reverse=True)
            return ranked[:k]

        scored = []
        for n in candidates:
            n_tokens = set(_tokenize(n.get("text", "")))
            overlap = len(q_tokens & n_tokens)
            if overlap:
                score = overlap / (len(q_tokens) + 1e-9)
                scored.append((score, n))
        scored.sort(key=lambda x: (x[0], x[1].get("created_at", 0)), reverse=True)
        return [n for _, n in scored[:k]]

    def all(self, user_id: Any = None) -> List[Dict[str, Any]]:
        with self._lock:
            notes = list(self._notes)
        if user_id is not None:
            notes = [n for n in notes if n.get("user_id") == str(user_id)]
        return notes

    def clear(self, user_id: Any = None):
        with self._lock:
            if user_id is None:
                self._notes = []
            else:
                self._notes = [n for n in self._notes if n.get("user_id") != str(user_id)]

    @property
    def backend(self) -> str:
        return self._backend


semantic_memory = SemanticMemory()
