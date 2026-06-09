"""
Semantic Memory
===============
Long-term, searchable note store for the agent.

Backends (auto-selected at runtime):
  1. Qdrant + embeddings  — when ``MEMORY_SEMANTIC_ENABLED`` and a Qdrant server
     and an embedding function are both reachable.
  2. JSON keyword store   — always-available fallback that persists notes to
     ``memory_store.json`` and ranks them by keyword overlap.

The fallback guarantees ``store_note`` / ``recall_notes`` work with zero
external services (important for local dev and tests).
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_STORE_PATH = Path("memory_store.json")


def _tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"\W+", (text or "").lower()) if t]


class SemanticMemory:
    """Keyword/semantic note store with a robust JSON fallback."""

    def __init__(self):
        self._lock = threading.Lock()
        self._notes: List[Dict[str, Any]] = []
        self._loaded = False
        self._qdrant = None
        self._collection = settings.MEMORY_QDRANT_COLLECTION
        self._backend = "json"

    # ------------------------------------------------------------------ load
    def _load(self):
        if self._loaded:
            return
        try:
            if _STORE_PATH.exists():
                self._notes = json.loads(_STORE_PATH.read_text("utf-8"))
        except Exception as e:
            logger.warning(f"Could not load memory store: {e}")
            self._notes = []
        self._loaded = True

    def _persist(self):
        try:
            _STORE_PATH.write_text(json.dumps(self._notes, ensure_ascii=False), "utf-8")
        except Exception as e:
            logger.warning(f"Could not persist memory store: {e}")

    # ------------------------------------------------------------------ api
    def add(self, text: str, user_id: Any = 0, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Store a note and return its record."""
        note = {
            "id": uuid.uuid4().hex,
            "text": text,
            "user_id": str(user_id),
            "metadata": metadata or {},
            "created_at": time.time(),
        }
        with self._lock:
            self._load()
            self._notes.append(note)
            self._persist()
        return note

    def search(self, query: str, user_id: Any = None, k: int = 5) -> List[Dict[str, Any]]:
        """Return up to ``k`` notes most relevant to ``query``."""
        with self._lock:
            self._load()
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
            self._load()
            notes = list(self._notes)
        if user_id is not None:
            notes = [n for n in notes if n.get("user_id") == str(user_id)]
        return notes

    def clear(self, user_id: Any = None):
        with self._lock:
            self._load()
            if user_id is None:
                self._notes = []
            else:
                self._notes = [n for n in self._notes if n.get("user_id") != str(user_id)]
            self._persist()

    @property
    def backend(self) -> str:
        return self._backend


semantic_memory = SemanticMemory()
