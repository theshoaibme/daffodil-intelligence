"""Telegram session and queue ORM models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..core.database import Base


class TelegramProfileSession(Base):
    __tablename__ = "telegram_profile_sessions"

    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String(128), nullable=False, default="")
    first_name = Column(String(128), nullable=False, default="")
    last_name = Column(String(128), nullable=False, default="")
    full_name = Column(String(255), nullable=False, default="")
    role = Column(String(32), nullable=False, default="")
    phone = Column(String(32), nullable=False, default="")
    email = Column(String(255), nullable=False, default="")
    pending_password = Column(String(255), nullable=False, default="")
    student_id = Column(String(50), nullable=False, default="")
    department = Column(String(100), nullable=False, default="")
    step = Column(String(64), nullable=False, default="auth_menu")
    mode = Column(String(32), nullable=False, default="")
    selected_agent_id = Column(String(64), nullable=False, default="")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PendingRegistrationRow(Base):
    __tablename__ = "pending_registrations"

    email = Column(String(255), primary_key=True)
    accept_terms = Column(Boolean, nullable=False, default=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    first_name = Column(String(128), nullable=False, default="")
    last_name = Column(String(128), nullable=False, default="")
    password_hash = Column(String(255), nullable=False, default="")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TelegramOutboundMessage(Base):
    __tablename__ = "telegram_outbound_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(64), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
