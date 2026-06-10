"""Turn-scoped event emitter: wraps legacy events in versioned envelopes."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from ..schemas.ai_events import AiEventEnvelope, legacy_event_to_envelope

logger = logging.getLogger(__name__)


class TurnEventEmitter:
    """Emits versioned envelopes for a single chat turn, with optional persistence."""

    def __init__(
        self,
        *,
        session_id: str,
        turn_id: str,
        correlation_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.turn_id = turn_id
        self.correlation_id = correlation_id or turn_id
        self._seq = 0
        self._buffer: List[AiEventEnvelope] = []

    @property
    def events(self) -> List[AiEventEnvelope]:
        return list(self._buffer)

    @property
    def last_seq(self) -> int:
        return self._seq

    def wrap_legacy(self, event: Dict[str, Any]) -> AiEventEnvelope:
        """Convert a legacy runtime event to an envelope and buffer it."""
        if isinstance(event, str):
            event = {"type": "content", "content": event}
        self._seq += 1
        envelope = legacy_event_to_envelope(
            event,
            session_id=self.session_id,
            turn_id=self.turn_id,
            seq=self._seq,
            correlation_id=self.correlation_id,
        )
        self._buffer.append(envelope)
        return envelope

    def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        source: Optional[Dict[str, str]] = None,
        legacy_type: Optional[str] = None,
    ) -> AiEventEnvelope:
        """Emit a canonical event directly."""
        self._seq += 1
        from ..schemas.ai_events import EventSource

        envelope = AiEventEnvelope(
            seq=self._seq,
            session_id=self.session_id,
            turn_id=self.turn_id,
            source=EventSource(**(source or {})),
            type=event_type,
            payload=payload,
            correlation_id=self.correlation_id,
            legacy_type=legacy_type or _canonical_to_legacy(event_type),
        )
        self._buffer.append(envelope)
        return envelope

    def sse_line(self, envelope: AiEventEnvelope) -> str:
        """Format an envelope as an SSE data line with envelope + legacy fields."""
        data = envelope.to_sse_dict(include_legacy=True)
        data["envelope"] = envelope.model_dump(exclude_none=True)
        return f"data: {json.dumps(data)}\n\n"

    def done_line(self) -> str:
        done = self.emit("stream.done", {})
        return self.sse_line(done)


def _canonical_to_legacy(canonical: str) -> Optional[str]:
    reverse = {
        "message.chunk": "content",
        "message.thinking": "thinking",
        "status.progress": "status",
        "tool.started": "tool",
        "tool.finished": "tool",
        "agent.started": "agent",
        "agent.delegated": "subagent",
        "memory.active": "memory",
        "workflow.node": "task",
        "ui.block": "ui",
        "model.resolved": "model",
        "context.usage": "context",
    }
    return reverse.get(canonical)


async def persist_event_log(
    db,
    envelopes: List[AiEventEnvelope],
) -> None:
    """Best-effort persist envelopes to event_log table."""
    if not envelopes:
        return
    try:
        from ..models.runtime import EventLog

        for env in envelopes:
            row = EventLog(
                session_id=env.session_id,
                turn_id=env.turn_id,
                seq=env.seq,
                envelope=env.model_dump(),
            )
            db.add(row)
        await db.commit()
    except Exception as exc:
        logger.warning("event_log persist failed: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass


async def stream_with_envelopes(
    emitter: TurnEventEmitter,
    source: AsyncIterator[Any],
) -> AsyncIterator[str]:
    """Wrap an async iterator of legacy events into SSE envelope lines."""
    async for event in source:
        if not event:
            continue
        envelope = emitter.wrap_legacy(
            event if isinstance(event, dict) else {"type": "content", "content": event}
        )
        yield emitter.sse_line(envelope)
