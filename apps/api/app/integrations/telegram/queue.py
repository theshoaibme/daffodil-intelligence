"""Persistent Telegram message queue in PostgreSQL."""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select

from ...core.database import is_mock_database
from ...models.telegram import TelegramOutboundMessage
from .pg_sync import sync_session

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
    """PostgreSQL-backed FIFO queue for bot sends while offline or starting."""

    def __init__(self, path: str = ""):
        self._lock = threading.Lock()
        self._memory: List[QueuedOutbound] = []
        self._use_memory = is_mock_database() or bool(path)

    def enqueue(self, item: QueuedOutbound) -> None:
        with self._lock:
            if self._use_memory:
                self._memory.append(item)
            else:
                with sync_session() as db:
                    db.add(
                        TelegramOutboundMessage(
                            kind=item.kind,
                            telegram_id=item.telegram_id,
                            payload=item.payload,
                        )
                    )
        logger.info(
            "Queued Telegram %s for user %s (bot offline or starting)",
            item.kind,
            item.telegram_id,
        )

    def pop_all(self) -> List[QueuedOutbound]:
        with self._lock:
            if self._use_memory:
                items = list(self._memory)
                self._memory = []
                return items
            with sync_session() as db:
                rows = db.execute(
                    select(TelegramOutboundMessage).order_by(TelegramOutboundMessage.id)
                ).scalars().all()
                items = [
                    QueuedOutbound(
                        kind=row.kind,
                        telegram_id=int(row.telegram_id),
                        payload=dict(row.payload or {}),
                        created_at=row.created_at.isoformat() if row.created_at else _utc_now(),
                    )
                    for row in rows
                ]
                for row in rows:
                    db.delete(row)
                return items

    def size(self) -> int:
        with self._lock:
            if self._use_memory:
                return len(self._memory)
            with sync_session() as db:
                return len(db.execute(select(TelegramOutboundMessage)).scalars().all())


outbound_queue = TelegramOutboundQueue()
