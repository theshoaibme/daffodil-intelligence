"""Persistent Telegram message queue for downtime and sequential drain."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueuedOutbound:
    """Outbound Telegram notification waiting for the bot to come online."""

    kind: str
    telegram_id: int
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueuedOutbound":
        return cls(
            kind=str(data.get("kind", "")),
            telegram_id=int(data["telegram_id"]),
            payload=dict(data.get("payload") or {}),
            created_at=str(data.get("created_at") or _utc_now()),
        )


class TelegramOutboundQueue:
    """File-backed FIFO queue for bot sends while offline or starting."""

    def __init__(self, path: str = "telegram_outbound_queue.json"):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._items: List[QueuedOutbound] = []
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._items = [
                    QueuedOutbound.from_dict(item)
                    for item in (raw if isinstance(raw, list) else [])
                ]
            except Exception as e:
                logger.warning("Could not load Telegram outbound queue: %s", e)
                self._items = []
        self._loaded = True

    def _save(self) -> None:
        self._path.write_text(
            json.dumps([item.to_dict() for item in self._items], ensure_ascii=False, indent=2),
            "utf-8",
        )

    def enqueue(self, item: QueuedOutbound) -> None:
        with self._lock:
            self._load()
            self._items.append(item)
            self._save()
        logger.info(
            "Queued Telegram %s for user %s (bot offline or starting)",
            item.kind,
            item.telegram_id,
        )

    def pop_all(self) -> List[QueuedOutbound]:
        with self._lock:
            self._load()
            items = list(self._items)
            self._items = []
            if items:
                self._save()
            return items

    def size(self) -> int:
        with self._lock:
            self._load()
            return len(self._items)


outbound_queue = TelegramOutboundQueue()
