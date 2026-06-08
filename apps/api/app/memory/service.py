"""
Memory Service v2
=================
Façade over durable history, unified agent_memories (PG + Qdrant),
runtime snapshots, and conversation summarization.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..core.database import get_session_maker, MockSession
from ..models.user import Chat, Message
from .context_builder import build_turn_memory_context
from .repository import MemoryRepository
from .semantic import semantic_memory
from .summarizer import maybe_rolling_summary, summarize_turn
from .types import ROOT_AGENT_ID

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _session():
    maker = get_session_maker()
    if maker is None:
        yield MockSession()
        return
    async with maker() as session:
        yield session


def _repo(session) -> MemoryRepository:
    return MemoryRepository(session)


class MemoryService:
    def __init__(self):
        self.semantic = semantic_memory

    # ----------------------------------------------------------- durable
    async def ensure_chat(
        self, user_id: int, title: str = "Conversation", agent_type: str = "main"
    ) -> Optional[int]:
        try:
            async with _session() as db:
                chat = Chat(user_id=user_id, title=title[:255], agent_type=agent_type)
                db.add(chat)
                await db.commit()
                await db.refresh(chat)
                return chat.id
        except Exception as e:
            logger.warning("ensure_chat failed: %s", e)
            return None

    async def save_message(
        self,
        chat_id: int,
        role: str,
        content: str,
        meta: Optional[Dict] = None,
    ) -> Optional[int]:
        try:
            async with _session() as db:
                msg = Message(chat_id=chat_id, role=role, content=content, meta=meta or {})
                db.add(msg)
                await db.commit()
                await db.refresh(msg)
                return msg.id
        except Exception as e:
            logger.warning("save_message failed: %s", e)
            return None

    async def get_history(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            async with _session() as db:
                result = await db.execute(
                    select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
                )
                rows = result.scalars().all()
                rows = rows[-limit:]
                return [{"role": r.role, "content": r.content, "meta": r.meta} for r in rows]
        except Exception as e:
            logger.warning("get_history failed: %s", e)
            return []

    async def verify_chat_owner(self, chat_id: int, user_id: int) -> bool:
        try:
            async with _session() as db:
                result = await db.execute(
                    select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
                )
                return result.scalar_one_or_none() is not None
        except Exception:
            return False

    # ----------------------------------------------------------- unified memories
    async def remember(
        self,
        text: str,
        user_id: Any = 0,
        *,
        agent_id: str = ROOT_AGENT_ID,
        memory_type: str = "fact",
        visibility: str = "private",
        source: str = "user",
        metadata: Optional[Dict] = None,
        payload: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        uid = int(user_id or 0)
        try:
            async with _session() as db:
                if hasattr(db, "commit"):
                    row = await _repo(db).upsert(
                        user_id=uid,
                        agent_id=agent_id,
                        content=text,
                        memory_type=memory_type,
                        visibility=visibility,
                        source=source,
                        metadata=metadata,
                        payload=payload,
                    )
                    return row
        except Exception as e:
            logger.warning("remember PG failed, falling back to JSON: %s", e)

        return self.semantic.add(text, user_id=uid, metadata=metadata or {})

    async def recall(
        self,
        query: str,
        user_id: Any = None,
        *,
        agent_id: str = ROOT_AGENT_ID,
        memory_types: Optional[List[str]] = None,
        chat_id: Optional[Any] = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        uid = int(user_id or 0)
        try:
            async with _session() as db:
                if hasattr(db, "commit"):
                    return await _repo(db).recall(
                        query,
                        uid,
                        caller_agent_id=agent_id,
                        memory_types=memory_types,
                        chat_id=chat_id,
                        k=k,
                    )
        except Exception as e:
            logger.warning("recall PG failed, falling back to JSON: %s", e)

        return self.semantic.search(query, user_id=uid, k=k)

    async def list_memories(
        self,
        user_id: int,
        *,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        chat_id: Optional[Any] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        async with _session() as db:
            if not hasattr(db, "commit"):
                notes = self.semantic.all(user_id=user_id)
                return {"items": notes, "total": len(notes)}
            items, total = await _repo(db).list_memories(
                user_id,
                agent_id=agent_id,
                memory_type=memory_type,
                scope=scope,
                chat_id=chat_id,
                limit=limit,
                offset=offset,
            )
            return {"items": items, "total": total}

    async def delete_memory(self, memory_id: str, user_id: int) -> bool:
        async with _session() as db:
            if not hasattr(db, "commit"):
                return False
            return await _repo(db).delete_one(memory_id, user_id)

    async def clear_memories(
        self,
        user_id: int,
        *,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        chat_id: Optional[Any] = None,
        clear_all: bool = False,
    ) -> int:
        async with _session() as db:
            if not hasattr(db, "commit"):
                self.semantic.clear(user_id=user_id)
                return 0
            return await _repo(db).clear(
                user_id,
                agent_id=agent_id,
                memory_type=memory_type,
                chat_id=chat_id,
                clear_all=clear_all,
            )

    async def stats(self, user_id: int) -> Dict[str, Any]:
        async with _session() as db:
            if not hasattr(db, "commit"):
                notes = self.semantic.all(user_id=user_id)
                return {"total": len(notes), "by_type": {"fact": len(notes)}, "by_agent": {}, "qdrant_available": False}
            return await _repo(db).stats(user_id)

    async def get_context_snapshots(self, user_id: int, agent_id: str) -> List[Dict[str, Any]]:
        async with _session() as db:
            if not hasattr(db, "commit"):
                return []
            return await _repo(db).latest_config_snapshots(user_id, agent_id)

    async def build_recall_context(
        self,
        user_id: int,
        agent_id: str,
        message: str,
        *,
        chat_id: Optional[Any] = None,
    ) -> str:
        return await build_turn_memory_context(
            user_id, agent_id, message, chat_id=chat_id
        )

    async def process_turn_memory(
        self,
        *,
        user_id: int,
        agent_id: str,
        chat_id: Any,
        user_msg: str,
        assistant_msg: str,
        turn_index: int = 0,
    ) -> None:
        """Store turn + maybe rolling summary after a chat completes."""
        try:
            async with _session() as db:
                if not hasattr(db, "commit"):
                    return
                repo = _repo(db)
                await summarize_turn(
                    repo,
                    user_id=user_id,
                    agent_id=agent_id,
                    chat_id=chat_id,
                    user_msg=user_msg,
                    assistant_msg=assistant_msg,
                    turn_index=turn_index,
                )
                await maybe_rolling_summary(
                    repo,
                    user_id=user_id,
                    agent_id=agent_id,
                    chat_id=chat_id,
                    turn_index=turn_index,
                )
        except Exception as e:
            logger.warning("process_turn_memory failed: %s", e)

    async def store_subagent_event(
        self,
        *,
        user_id: int,
        parent_agent_id: str,
        subagent_id: str,
        name: str,
        task: str,
        result_summary: Optional[str] = None,
        chat_id: Optional[Any] = None,
    ) -> None:
        try:
            async with _session() as db:
                if not hasattr(db, "commit"):
                    return
                repo = _repo(db)
                await repo.upsert(
                    user_id=user_id,
                    agent_id=subagent_id,
                    parent_agent_id=parent_agent_id,
                    content=f"Sub-agent {name}: {task[:500]}",
                    memory_type="subagent_definition",
                    visibility="agent_tree",
                    source="subagent",
                    payload={
                        "subagent_id": subagent_id,
                        "name": name,
                        "task": task,
                        "parent_agent_id": parent_agent_id,
                    },
                    metadata={"chat_id": str(chat_id) if chat_id else None},
                )
                if result_summary:
                    await repo.upsert(
                        user_id=user_id,
                        agent_id=subagent_id,
                        parent_agent_id=parent_agent_id,
                        content=result_summary[:1000],
                        memory_type="subagent_result",
                        visibility="agent_tree",
                        source="subagent",
                        payload={
                            "subagent_id": subagent_id,
                            "task": task[:200],
                            "result_summary": result_summary,
                        },
                        metadata={"chat_id": str(chat_id) if chat_id else None},
                    )
        except Exception as e:
            logger.warning("store_subagent_event failed: %s", e)

    async def consolidate(self, user_id: int) -> Dict[str, Any]:
        """Promote sub-agent memories with agent_tree visibility to shared."""
        promoted = 0
        try:
            async with _session() as db:
                if not hasattr(db, "commit"):
                    return {"promoted": 0}
                from ..models.memory import AgentMemory

                result = await db.execute(
                    select(AgentMemory).where(
                        AgentMemory.user_id == user_id,
                        AgentMemory.scope == "subagent",
                        AgentMemory.visibility == "agent_tree",
                    )
                )
                rows = result.scalars().all()
                for row in rows:
                    row.visibility = "shared"
                    row.scope = "shared"
                    promoted += 1
                await db.commit()
        except Exception as e:
            logger.warning("consolidate failed: %s", e)
        return {"promoted": promoted}


memory_service = MemoryService()
