"""WebSocket session event bus for persistent chat sessions."""

from __future__ import annotations

import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.runtime import EventLog
from ..models.user import Chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    def _key(self, chat_id: int) -> str:
        return str(chat_id)

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        key = self._key(chat_id)
        self._connections.setdefault(key, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: int):
        key = self._key(chat_id)
        conns = self._connections.get(key)
        if conns:
            conns.discard(websocket)
            if not conns:
                del self._connections[key]

    async def broadcast(self, chat_id: int, message: str):
        key = self._key(chat_id)
        dead: Set[WebSocket] = set()
        for ws in self._connections.get(key, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws, chat_id)


session_manager = SessionConnectionManager()


@router.get("/{chat_id}/events")
async def replay_events(
    chat_id: int,
    from_seq: int = 0,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Replay event log for session sync after reconnect."""
    user_id = int(user.get("sub"))
    chat_row = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    if not chat_row.scalar_one_or_none():
        return {"events": [], "last_seq": from_seq}

    result = await db.execute(
        select(EventLog)
        .where(EventLog.session_id == str(chat_id), EventLog.seq > from_seq)
        .order_by(EventLog.seq)
        .limit(limit)
    )
    rows = result.scalars().all()
    events = [row.envelope for row in rows]
    last_seq = rows[-1].seq if rows else from_seq
    return {"events": events, "last_seq": last_seq}


@router.websocket("/{chat_id}/events/ws")
async def session_events_ws(websocket: WebSocket, chat_id: int):
    await session_manager.connect(websocket, chat_id)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "sync.request":
                from_seq = int(msg.get("from_seq", 0))
                await websocket.send_text(json.dumps({
                    "type": "sync.ack",
                    "from_seq": from_seq,
                    "chat_id": chat_id,
                }))
            elif msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        session_manager.disconnect(websocket, chat_id)
        logger.info("Session WS disconnected chat_id=%s", chat_id)
