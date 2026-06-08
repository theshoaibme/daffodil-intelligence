"""Unified agent memory ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(64), nullable=False, default="main", index=True)
    scope = Column(String(32), nullable=False, default="root")
    parent_agent_id = Column(String(64), nullable=True)
    content = Column(Text, nullable=False)
    memory_type = Column(String(64), nullable=False, default="fact", index=True)
    visibility = Column(String(32), nullable=False, default="private")
    source = Column(String(32), nullable=False, default="system")
    payload = Column(JSONB, nullable=False, server_default="{}")
    memory_metadata = Column("metadata", JSONB, nullable=False, server_default="{}")
    qdrant_point_id = Column(String(64), nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "content_hash", name="uq_agent_memories_user_hash"),
    )
