"""PostgreSQL + Qdrant repository for unified agent memories."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.memory import AgentMemory
from .qdrant_store import qdrant_store
from .types import (
    ALL_MEMORY_TYPES,
    ROOT_AGENT_ID,
    canonical_embed_text,
    compute_content_hash,
    resolve_scope,
)

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"\W+", (text or "").lower()) if t]


def _row_to_dict(row: AgentMemory) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "agent_id": row.agent_id,
        "scope": row.scope,
        "parent_agent_id": row.parent_agent_id,
        "content": row.content,
        "memory_type": row.memory_type,
        "visibility": row.visibility,
        "source": row.source,
        "payload": row.payload or {},
        "metadata": row.memory_metadata or {},
        "qdrant_point_id": row.qdrant_point_id,
        "content_hash": row.content_hash,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _permission_filter(caller_agent_id: str):
    """SQLAlchemy filter for permission-aware reads."""
    if caller_agent_id == ROOT_AGENT_ID:
        return True

    return or_(
        AgentMemory.agent_id == caller_agent_id,
        AgentMemory.visibility == "global",
        AgentMemory.visibility == "agent_tree",
        AgentMemory.scope == "shared",
    )


class MemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        *,
        user_id: int,
        agent_id: str,
        content: str,
        memory_type: str = "fact",
        visibility: str = "private",
        source: str = "system",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_agent_id: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        if memory_type not in ALL_MEMORY_TYPES:
            memory_type = "fact"

        payload = payload or {}
        metadata = metadata or {}
        scope = resolve_scope(agent_id, parent_agent_id)
        chash = content_hash or compute_content_hash(memory_type, agent_id, content, payload)

        existing = await self.session.execute(
            select(AgentMemory).where(
                AgentMemory.user_id == user_id,
                AgentMemory.content_hash == chash,
            )
        )
        row = existing.scalar_one_or_none()

        embed_text = canonical_embed_text(memory_type, content, payload)
        qdrant_payload = {
            "user_id": user_id,
            "agent_id": agent_id,
            "memory_type": memory_type,
            "scope": scope,
            "chat_id": str(metadata.get("chat_id", "")),
            "memory_id": str(row.id) if row else "",
        }

        if row:
            row.content = content
            row.payload = payload
            row.memory_metadata = metadata
            row.updated_at = datetime.now(timezone.utc)
            point_id = await qdrant_store.upsert(
                row.qdrant_point_id or str(row.id),
                embed_text,
                {**qdrant_payload, "memory_id": str(row.id)},
            )
            row.qdrant_point_id = point_id
            await self.session.commit()
            await self.session.refresh(row)
            return _row_to_dict(row)

        row = AgentMemory(
            user_id=user_id,
            agent_id=agent_id,
            scope=scope,
            parent_agent_id=parent_agent_id,
            content=content,
            memory_type=memory_type,
            visibility=visibility,
            source=source,
            payload=payload,
            memory_metadata=metadata,
            content_hash=chash,
        )
        self.session.add(row)
        await self.session.flush()

        qdrant_payload["memory_id"] = str(row.id)
        point_id = str(uuid.uuid4())
        qdrant_point_id = await qdrant_store.upsert(point_id, embed_text, qdrant_payload)
        row.qdrant_point_id = qdrant_point_id

        await self.session.commit()
        await self.session.refresh(row)
        return _row_to_dict(row)

    async def list_memories(
        self,
        user_id: int,
        *,
        caller_agent_id: str = ROOT_AGENT_ID,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        chat_id: Optional[Any] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        stmt = select(AgentMemory).where(AgentMemory.user_id == user_id)
        count_stmt = select(func.count()).select_from(AgentMemory).where(AgentMemory.user_id == user_id)

        if caller_agent_id != ROOT_AGENT_ID:
            perm = _permission_filter(caller_agent_id)
            stmt = stmt.where(perm)
            count_stmt = count_stmt.where(perm)

        if agent_id:
            stmt = stmt.where(AgentMemory.agent_id == agent_id)
            count_stmt = count_stmt.where(AgentMemory.agent_id == agent_id)
        if memory_type:
            stmt = stmt.where(AgentMemory.memory_type == memory_type)
            count_stmt = count_stmt.where(AgentMemory.memory_type == memory_type)
        if scope:
            stmt = stmt.where(AgentMemory.scope == scope)
            count_stmt = count_stmt.where(AgentMemory.scope == scope)
        if chat_id is not None:
            stmt = stmt.where(AgentMemory.memory_metadata["chat_id"].as_string() == str(chat_id))
            count_stmt = count_stmt.where(AgentMemory.memory_metadata["chat_id"].as_string() == str(chat_id))

        total = (await self.session.execute(count_stmt)).scalar() or 0
        stmt = stmt.order_by(AgentMemory.created_at.desc()).limit(limit).offset(offset)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_row_to_dict(r) for r in rows], int(total)

    async def recall(
        self,
        query: str,
        user_id: int,
        *,
        caller_agent_id: str = ROOT_AGENT_ID,
        memory_types: Optional[List[str]] = None,
        chat_id: Optional[Any] = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        qdrant_hits = await qdrant_store.search(
            query,
            user_id=user_id,
            agent_id=None if caller_agent_id == ROOT_AGENT_ID else caller_agent_id,
            memory_types=memory_types,
            chat_id=chat_id,
            k=k * 2,
        )

        if qdrant_hits:
            ids = [h["payload"].get("memory_id") for h in qdrant_hits if h["payload"].get("memory_id")]
            if ids:
                stmt = select(AgentMemory).where(
                    AgentMemory.user_id == user_id,
                    AgentMemory.id.in_(ids),
                )
                if caller_agent_id != ROOT_AGENT_ID:
                    stmt = stmt.where(_permission_filter(caller_agent_id))
                rows = (await self.session.execute(stmt)).scalars().all()
                by_id = {str(r.id): _row_to_dict(r) for r in rows}
                results = []
                for hit in qdrant_hits:
                    mid = hit["payload"].get("memory_id")
                    if mid and mid in by_id:
                        item = by_id[mid]
                        item["score"] = hit.get("score", 0)
                        results.append(item)
                        if len(results) >= k:
                            break
                if results:
                    return results

        return await self._keyword_recall(
            query,
            user_id,
            caller_agent_id=caller_agent_id,
            memory_types=memory_types,
            chat_id=chat_id,
            k=k,
        )

    async def _keyword_recall(
        self,
        query: str,
        user_id: int,
        *,
        caller_agent_id: str,
        memory_types: Optional[List[str]],
        chat_id: Optional[Any],
        k: int,
    ) -> List[Dict[str, Any]]:
        stmt = select(AgentMemory).where(AgentMemory.user_id == user_id)
        if caller_agent_id != ROOT_AGENT_ID:
            stmt = stmt.where(_permission_filter(caller_agent_id))
        if memory_types:
            stmt = stmt.where(AgentMemory.memory_type.in_(memory_types))
        if chat_id is not None:
            stmt = stmt.where(AgentMemory.memory_metadata["chat_id"].as_string() == str(chat_id))

        rows = (await self.session.execute(stmt.order_by(AgentMemory.created_at.desc()).limit(200))).scalars().all()
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return [_row_to_dict(r) for r in rows[:k]]

        scored = []
        for row in rows:
            tokens = set(_tokenize(row.content))
            overlap = len(q_tokens & tokens)
            if overlap:
                scored.append((overlap / len(q_tokens), row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [_row_to_dict(r) for _, r in scored[:k]]

    async def get_by_id(self, memory_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        row = await self.session.get(AgentMemory, memory_id)
        if not row or row.user_id != user_id:
            return None
        return _row_to_dict(row)

    async def delete_one(self, memory_id: str, user_id: int) -> bool:
        row = await self.session.get(AgentMemory, memory_id)
        if not row or row.user_id != user_id:
            return False
        if row.qdrant_point_id:
            qdrant_store.delete(row.qdrant_point_id)
        await self.session.delete(row)
        await self.session.commit()
        return True

    async def clear(
        self,
        user_id: int,
        *,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        chat_id: Optional[Any] = None,
        clear_all: bool = False,
    ) -> int:
        if clear_all:
            result = await self.session.execute(
                delete(AgentMemory).where(AgentMemory.user_id == user_id)
            )
            await self.session.commit()
            qdrant_store.delete_by_user(user_id)
            return result.rowcount or 0

        select_stmt = select(AgentMemory).where(AgentMemory.user_id == user_id)
        if agent_id:
            select_stmt = select_stmt.where(AgentMemory.agent_id == agent_id)
        if memory_type:
            select_stmt = select_stmt.where(AgentMemory.memory_type == memory_type)
        if chat_id is not None:
            select_stmt = select_stmt.where(
                AgentMemory.memory_metadata["chat_id"].as_string() == str(chat_id)
            )

        rows = (await self.session.execute(select_stmt)).scalars().all()
        qdrant_ids = [r.qdrant_point_id for r in rows if r.qdrant_point_id]

        delete_stmt = delete(AgentMemory).where(AgentMemory.user_id == user_id)
        if agent_id:
            delete_stmt = delete_stmt.where(AgentMemory.agent_id == agent_id)
        if memory_type:
            delete_stmt = delete_stmt.where(AgentMemory.memory_type == memory_type)
        if chat_id is not None:
            delete_stmt = delete_stmt.where(
                AgentMemory.memory_metadata["chat_id"].as_string() == str(chat_id)
            )

        result = await self.session.execute(delete_stmt)
        await self.session.commit()
        qdrant_store.delete_many(qdrant_ids)
        return result.rowcount or 0

    async def stats(self, user_id: int) -> Dict[str, Any]:
        type_rows = await self.session.execute(
            select(AgentMemory.memory_type, func.count())
            .where(AgentMemory.user_id == user_id)
            .group_by(AgentMemory.memory_type)
        )
        agent_rows = await self.session.execute(
            select(AgentMemory.agent_id, func.count())
            .where(AgentMemory.user_id == user_id)
            .group_by(AgentMemory.agent_id)
        )
        total = (await self.session.execute(
            select(func.count()).select_from(AgentMemory).where(AgentMemory.user_id == user_id)
        )).scalar() or 0

        return {
            "total": int(total),
            "by_type": {t: int(c) for t, c in type_rows.all()},
            "by_agent": {a: int(c) for a, c in agent_rows.all()},
            "qdrant_available": qdrant_store.available,
        }

    async def latest_config_snapshots(
        self,
        user_id: int,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        config_types = list(
            {"system_prompt", "skill", "ruleset", "tool_definition", "mcp_server", "agent_config"}
        )
        stmt = (
            select(AgentMemory)
            .where(
                AgentMemory.user_id == user_id,
                AgentMemory.agent_id == agent_id,
                AgentMemory.memory_type.in_(config_types),
            )
            .order_by(AgentMemory.memory_type, AgentMemory.updated_at.desc())
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        seen: set[str] = set()
        result: List[Dict[str, Any]] = []
        for row in rows:
            if row.memory_type in seen:
                continue
            seen.add(row.memory_type)
            result.append(_row_to_dict(row))
        return result
