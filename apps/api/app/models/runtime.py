"""Runtime persistence models: event log, workflows, workflow nodes."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..core.database import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(128), nullable=False, index=True)
    turn_id = Column(String(128), nullable=False, index=True)
    seq = Column(BigInteger, nullable=False)
    envelope = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="pending")
    definition = Column(JSONB, nullable=False, default=dict)
    checkpoint = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    agent_id = Column(String(128), nullable=True)
    kind = Column(String(32), nullable=False, default="agent")
    status = Column(String(32), nullable=False, default="pending")
    input = Column(JSONB, nullable=True)
    output = Column(JSONB, nullable=True)
    parallel_group = Column(String(64), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
