"""
Memory Service
==============
Façade over the three memory layers used across the app:

  - durable:   PostgreSQL ``Chat`` / ``Message`` rows (conversation history)
  - semantic:  long-term notes (``SemanticMemory``)
  - short-term: handled by the Antigravity conversation store (session_manager)

Designed to be usable both inside FastAPI request handlers and standalone
contexts (Telegram bot, voice, workers), so it manages its own DB session when
needed and degrades gracefully when the database is unavailable.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from ..core.database import get_session_maker, MockSession
from ..models.user import Chat, Message
from sqlalchemy import select

from .semantic import semantic_memory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _session():
    """Yield a DB session (real or mock) outside of FastAPI dependency injection."""
    maker = get_session_maker()
    if maker is None:
        yield MockSession()
        return
    async with maker() as session:
        yield session


class MemoryService:
    def __init__(self):
        self.semantic = semantic_memory

    # ----------------------------------------------------------- durable
    async def ensure_chat(self, user_id: int, title: str = "Conversation", agent_type: str = "main") -> Optional[int]:
        """Create a chat row and return its id (best-effort)."""
        try:
            async with _session() as db:
                chat = Chat(user_id=user_id, title=title[:255], agent_type=agent_type)
                db.add(chat)
                await db.commit()
                await db.refresh(chat)
                return chat.id
        except Exception as e:
            logger.warning(f"ensure_chat failed: {e}")
            return None

    async def save_message(
        self,
        chat_id: int,
        role: str,
        content: str,
        meta: Optional[Dict] = None,
    ) -> Optional[int]:
        """Persist a chat message; returns its id or None on failure."""
        try:
            async with _session() as db:
                msg = Message(chat_id=chat_id, role=role, content=content, meta=meta or {})
                db.add(msg)
                await db.commit()
                await db.refresh(msg)
                return msg.id
        except Exception as e:
            logger.warning(f"save_message failed: {e}")
            return None

    async def get_history(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent messages for a chat as plain dicts."""
        try:
            async with _session() as db:
                result = await db.execute(
                    select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
                )
                rows = result.scalars().all()
                rows = rows[-limit:]
                return [
                    {"role": r.role, "content": r.content, "meta": r.meta}
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"get_history failed: {e}")
            return []

    # ----------------------------------------------------------- semantic
    def remember(self, text: str, user_id: Any = 0, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        return self.semantic.add(text, user_id=user_id, metadata=metadata)

    def recall(self, query: str, user_id: Any = None, k: int = 5) -> List[Dict[str, Any]]:
        return self.semantic.search(query, user_id=user_id, k=k)


memory_service = MemoryService()
