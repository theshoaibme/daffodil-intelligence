"""Bridge Telegram login to web (Postgres) user accounts."""

from __future__ import annotations

import time
from typing import Optional, Tuple

from sqlalchemy import select

from ...core.database import get_session_maker
from ...core.security import verify_password
from ...models.user import User
from .auth_store import TelegramAccount, auth_store


def _split_full_name(full_name: str) -> Tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


async def fetch_web_user_by_email(email: str) -> Optional[User]:
    session_maker = get_session_maker()
    if session_maker is None:
        return None
    async with session_maker() as db:
        result = await db.execute(select(User).where(User.email == email.strip().lower()))
        return result.scalar_one_or_none()


async def resolve_login_email_status(email: str) -> Tuple[str, bool]:
    """Return (status, web_only). status: not_found | google_only | has_password."""
    status = auth_store.login_email_status(email)
    if status != "not_found":
        return status, False
    web_user = await fetch_web_user_by_email(email)
    if web_user:
        return "has_password", True
    return "not_found", False


def link_web_user_to_telegram(
    *,
    telegram_id: int,
    web_user: User,
    username: str = "",
) -> TelegramAccount:
    email = web_user.email.strip().lower()
    first_name, last_name = _split_full_name(web_user.full_name or "")
    full_name = (web_user.full_name or f"{first_name} {last_name}").strip()

    existing = auth_store.get_by_email(email)
    if existing:
        existing.telegram_id = telegram_id
        existing.password_hash = web_user.password_hash
        existing.full_name = full_name or existing.full_name
        existing.first_name = first_name or existing.first_name
        existing.last_name = last_name or existing.last_name
        existing.username = username or existing.username
        existing.role = web_user.role or existing.role
        existing.student_id = web_user.student_id or existing.student_id
        existing.department = web_user.department or existing.department
        if web_user.avatar_url:
            existing.avatar_url = web_user.avatar_url
        existing.email_verified = True
        existing.auth_provider = "both" if existing.auth_provider == "google" else "email"
        auth_store.save(existing)
        return existing

    account = TelegramAccount(
        user_id=f"web:{web_user.id}",
        telegram_id=telegram_id,
        email=email,
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        username=username,
        role=web_user.role or "student",
        student_id=web_user.student_id or "",
        department=web_user.department or "",
        password_hash=web_user.password_hash,
        auth_provider="email",
        avatar_url=web_user.avatar_url or "",
        email_verified=True,
        created_at=int(time.time()),
        last_login=int(time.time()),
    )
    auth_store.save(account)
    return account


async def verify_web_password_login(
    *,
    telegram_id: int,
    email: str,
    password: str,
    username: str = "",
) -> Optional[TelegramAccount]:
    web_user = await fetch_web_user_by_email(email)
    if not web_user or not verify_password(password, web_user.password_hash):
        return None
    return link_web_user_to_telegram(
        telegram_id=telegram_id,
        web_user=web_user,
        username=username,
    )
