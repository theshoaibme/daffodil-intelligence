"""Turn trace recorder — powers /flow, /logs, and the web live agent flow.

Captures the ordered events of a single runtime turn (model selection, agent
activation, thinking, tool calls, sub-agent delegation, content, and a rough
running context-token estimate) keyed by ``(user_id, chat_id)``. Kept in memory
with a small JSON-backed tail so recent turns survive a restart.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)

_MAX_TURNS_PER_KEY = 10
_MAX_PERSISTED_TURNS = 60


def _now() -> float:
    return time.time()


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token) for context tracking."""
    return max(0, (len(text or "") + 3) // 4)


@dataclass
class TraceEvent:
    type: str  # model | agent | thinking | tool | subagent | content | context
    name: str = ""
    status: str = ""  # active | success
    detail: str = ""
    at: float = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TurnTrace:
    turn_id: str
    key: str
    user_id: str
    chat_id: str
    agent_id: str = "main"
    model: str = ""
    started_at: float = field(default_factory=_now)
    ended_at: Optional[float] = None
    events: List[TraceEvent] = field(default_factory=list)
    used_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "agent_id": self.agent_id,
            "model": self.model,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "used_tokens": self.used_tokens,
            "duration_ms": (
                int((self.ended_at - self.started_at) * 1000) if self.ended_at else None
            ),
            "events": [e.to_dict() for e in self.events],
        }


def _key(user_id: Any, chat_id: Any) -> str:
    return f"u{user_id}-c{chat_id}"


class TraceRecorder:
    def __init__(self, path: Optional[Path] = None):
        settings = get_settings()
        base = Path(settings.ANTIGRAVITY_SAVE_DIR)
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._path = path or (base / "turn_traces.json")
        self._lock = threading.RLock()
        self._turns: Dict[str, TurnTrace] = {}
        self._by_key: Dict[str, Deque[str]] = {}
        self._order: Deque[str] = deque(maxlen=_MAX_PERSISTED_TURNS)

    def begin_turn(
        self, *, user_id: Any, chat_id: Any, agent_id: str = "main", model: str = ""
    ) -> str:
        turn_id = uuid.uuid4().hex[:12]
        key = _key(user_id, chat_id)
        turn = TurnTrace(
            turn_id=turn_id,
            key=key,
            user_id=str(user_id),
            chat_id=str(chat_id),
            agent_id=agent_id or "main",
            model=model or "",
        )
        with self._lock:
            self._turns[turn_id] = turn
            dq = self._by_key.setdefault(key, deque(maxlen=_MAX_TURNS_PER_KEY))
            if len(dq) == dq.maxlen:
                evicted = dq[0]
                self._turns.pop(evicted, None)
            dq.append(turn_id)
            self._order.append(turn_id)
        return turn_id

    def event(
        self,
        turn_id: Optional[str],
        *,
        type: str,
        name: str = "",
        status: str = "",
        detail: str = "",
    ) -> None:
        if not turn_id:
            return
        with self._lock:
            turn = self._turns.get(turn_id)
            if not turn:
                return
            turn.events.append(
                TraceEvent(type=type, name=name, status=status, detail=detail)
            )

    def add_tokens(self, turn_id: Optional[str], tokens: int) -> None:
        if not turn_id or tokens <= 0:
            return
        with self._lock:
            turn = self._turns.get(turn_id)
            if turn:
                turn.used_tokens += tokens

    def end_turn(self, turn_id: Optional[str]) -> None:
        if not turn_id:
            return
        with self._lock:
            turn = self._turns.get(turn_id)
            if not turn:
                return
            turn.ended_at = _now()
            self._persist_locked()

    def recent(self, *, user_id: Any, chat_id: Any, limit: int = 5) -> List[Dict[str, Any]]:
        key = _key(user_id, chat_id)
        with self._lock:
            ids = list(self._by_key.get(key, deque()))[-limit:]
            return [self._turns[i].to_dict() for i in ids if i in self._turns]

    def last(self, *, user_id: Any, chat_id: Any) -> Optional[Dict[str, Any]]:
        items = self.recent(user_id=user_id, chat_id=chat_id, limit=1)
        return items[-1] if items else None

    def all_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            ids = list(self._order)[-limit:]
            return [self._turns[i].to_dict() for i in ids if i in self._turns]

    def _persist_locked(self) -> None:
        try:
            ids = list(self._order)
            data = [self._turns[i].to_dict() for i in ids if i in self._turns]
            self._path.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
        except Exception as e:
            logger.debug("Could not persist turn traces: %s", e)


trace_recorder = TraceRecorder()
