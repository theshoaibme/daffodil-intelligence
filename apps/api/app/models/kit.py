"""Kit device pairing and audit models."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..core.database import Base


class KitDevice(Base):
    __tablename__ = "kit_devices"

    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False, server_default="desktop")
    device_secret = Column(String(128), nullable=False)
    allowed_commands = Column(JSONB, nullable=False, server_default='["screen","input","file_read","file_write","record"]')
    allowed_roots = Column(JSONB, nullable=False, server_default="[]")
    is_online = Column(Boolean, nullable=False, server_default="false")
    last_seen_at = Column(DateTime(timezone=True))
    ws_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KitPairingCode(Base):
    __tablename__ = "kit_pairing_codes"

    code = Column(String(8), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KitAuditEvent(Base):
    __tablename__ = "kit_audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    device_id = Column(String(64), ForeignKey("kit_devices.id", ondelete="SET NULL"), index=True)
    command = Column(String(64), nullable=False)
    payload = Column(JSONB)
    success = Column(Boolean, server_default="true")
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
