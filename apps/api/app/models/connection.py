"""Research connection and correspondence models."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from ..core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserResearchConnection(Base):
    __tablename__ = "user_research_connections"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String(128), nullable=False)
    target_kind = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "target_id", name="uq_user_research_connection_target"),
        Index("ix_user_research_connections_user_id", "user_id"),
        Index("ix_user_research_connections_target_id", "target_id"),
    )


class ConnectionCorrespondence(Base):
    __tablename__ = "connection_correspondence"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String(128), nullable=False)
    subject = Column(String(512), nullable=False)
    salutation = Column(String(255), nullable=False, default="")
    body = Column(Text, nullable=False)
    closing = Column(Text, nullable=False, default="")
    purpose = Column(String(64), nullable=True)
    direction = Column(String(16), nullable=False, default="outgoing")
    sender_name = Column(String(255), nullable=True)
    message_type = Column(String(16), nullable=False, default="formal")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_connection_correspondence_user_target", "user_id", "target_id"),
    )
