"""Telegram-linked user accounts stored in PostgreSQL (users table)."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import select

from ...core.database import is_mock_database
from ...core.security import get_password_hash, verify_password
from ...models.user import User
from .pg_sync import sync_session


@dataclass
class TelegramAccount:
    user_id: str
    telegram_id: int
    email: str
    full_name: str
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    phone: str = ""
    role: str = "student"
    student_id: str = ""
    department: str = ""
    password_hash: str = ""
    auth_provider: str = "email"  # email | google | both
    avatar_url: str = ""
    email_verified: bool = False
    created_at: int = 0
    last_login: int = 0

    def context_line(self) -> str:
        parts = [f"role={self.role}", f"email={self.email}"]
        if self.phone:
            parts.append(f"phone={self.phone}")
        if self.student_id:
            parts.append(f"student_id={self.student_id}")
        if self.department:
            parts.append(f"department={self.department}")
        return "User profile: " + ", ".join(parts)


def _dt_to_epoch(value: Optional[datetime]) -> int:
    if value is None:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())


def _epoch_to_dt(epoch: int) -> Optional[datetime]:
    if not epoch:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def _user_to_account(user: User) -> TelegramAccount:
    full_name = (user.full_name or "").strip()
    first = (user.first_name or "").strip()
    last = (user.last_name or "").strip()
    if not full_name and (first or last):
        full_name = f"{first} {last}".strip()
    return TelegramAccount(
        user_id=f"web:{user.id}",
        telegram_id=int(user.telegram_id or 0),
        email=user.email,
        full_name=full_name,
        first_name=first,
        last_name=last,
        username=user.telegram_username or "",
        phone=user.phone or "",
        role=user.role or "student",
        student_id=user.student_id or "",
        department=user.department or "",
        password_hash=user.password_hash or "",
        auth_provider=user.auth_provider or "email",
        avatar_url=user.avatar_url or "",
        email_verified=bool(user.email_verified),
        created_at=_dt_to_epoch(user.created_at),
        last_login=_dt_to_epoch(user.last_login),
    )


def _apply_account_to_user(user: User, account: TelegramAccount) -> None:
    user.email = account.email.strip().lower()
    user.full_name = account.full_name
    user.first_name = account.first_name or None
    user.last_name = account.last_name or None
    user.telegram_username = account.username or None
    user.phone = account.phone or None
    user.role = account.role or "student"
    user.student_id = account.student_id or None
    user.department = account.department or None
    user.password_hash = account.password_hash or None
    user.auth_provider = account.auth_provider or "email"
    user.avatar_url = account.avatar_url or None
    user.email_verified = bool(account.email_verified)
    user.telegram_id = account.telegram_id or None
    user.last_login = _epoch_to_dt(account.last_login)


class TelegramAuthStore:
    """PostgreSQL-backed store; in-memory fallback when DB is unavailable (tests)."""

    def __init__(self, path: str = ""):
        self._lock = threading.Lock()
        self._memory_by_tid: Dict[str, TelegramAccount] = {}
        self._memory_by_email: Dict[str, str] = {}
        # Explicit path => in-memory (tests); otherwise PostgreSQL unless DB is mocked.
        self._use_memory = is_mock_database() or bool(path)

    def _memory_key(self, account: TelegramAccount) -> str:
        if account.telegram_id:
            return str(account.telegram_id)
        return f"uid:{account.user_id}"

    def _memory_save(self, account: TelegramAccount) -> None:
        email_key = account.email.lower()
        new_key = self._memory_key(account)
        stale = [
            key
            for key, acct in self._memory_by_tid.items()
            if key != new_key and (acct.user_id == account.user_id or acct.email.lower() == email_key)
        ]
        for key in stale:
            del self._memory_by_tid[key]
        self._memory_by_tid[new_key] = account
        self._memory_by_email[email_key] = new_key

    def _memory_get_by_tid(self, telegram_id: int) -> Optional[TelegramAccount]:
        return self._memory_by_tid.get(str(telegram_id))

    def _memory_get_by_email(self, email: str) -> Optional[TelegramAccount]:
        key = self._memory_by_email.get(email.strip().lower())
        return self._memory_by_tid.get(key) if key else None

    def get_by_telegram_id(self, telegram_id: int) -> Optional[TelegramAccount]:
        with self._lock:
            if self._use_memory:
                return self._memory_get_by_tid(telegram_id)
            with sync_session() as db:
                row = db.execute(
                    select(User).where(User.telegram_id == telegram_id)
                ).scalar_one_or_none()
                return _user_to_account(row) if row else None

    def get_by_email(self, email: str) -> Optional[TelegramAccount]:
        with self._lock:
            if self._use_memory:
                return self._memory_get_by_email(email)
            with sync_session() as db:
                row = db.execute(
                    select(User).where(User.email == email.strip().lower())
                ).scalar_one_or_none()
                return _user_to_account(row) if row else None

    def email_taken(self, email: str, exclude_telegram_id: Optional[int] = None) -> bool:
        acct = self.get_by_email(email)
        if not acct:
            return False
        if exclude_telegram_id and acct.telegram_id == exclude_telegram_id:
            return False
        return True

    def save(self, account: TelegramAccount):
        with self._lock:
            if self._use_memory:
                self._memory_save(account)
                return
            with sync_session() as db:
                user: Optional[User] = None
                if account.user_id.startswith("web:"):
                    try:
                        uid = int(account.user_id.split(":", 1)[1])
                        user = db.get(User, uid)
                    except (TypeError, ValueError):
                        user = None
                if user is None and account.telegram_id:
                    user = db.execute(
                        select(User).where(User.telegram_id == account.telegram_id)
                    ).scalar_one_or_none()
                if user is None:
                    user = db.execute(
                        select(User).where(User.email == account.email.strip().lower())
                    ).scalar_one_or_none()
                if user is None:
                    user = User(email=account.email.strip().lower())
                    db.add(user)
                _apply_account_to_user(user, account)
                db.flush()
                account.user_id = f"web:{user.id}"

    def detach_telegram_session(self, telegram_id: int) -> bool:
        with self._lock:
            if self._use_memory:
                key = str(telegram_id)
                account = self._memory_by_tid.get(key)
                if not account:
                    return False
                del self._memory_by_tid[key]
                account.telegram_id = 0
                self._memory_save(account)
                return True
            with sync_session() as db:
                user = db.execute(
                    select(User).where(User.telegram_id == telegram_id)
                ).scalar_one_or_none()
                if not user:
                    return False
                user.telegram_id = None
                return True

    def create_email_account(
        self,
        *,
        telegram_id: int,
        email: str,
        password: str,
        full_name: str,
        first_name: str,
        last_name: str,
        username: str,
        phone: str,
        role: str,
        student_id: str,
        department: str,
    ) -> TelegramAccount:
        now = int(time.time())
        account = TelegramAccount(
            user_id="",
            telegram_id=telegram_id,
            email=email.strip().lower(),
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone=phone,
            role=role,
            student_id=student_id,
            department=department,
            password_hash=get_password_hash(password),
            auth_provider="email",
            email_verified=True,
            created_at=now,
            last_login=now,
        )
        self.save(account)
        return self.get_by_telegram_id(telegram_id) or account

    def login_email_status(self, email: str) -> str:
        acct = self.get_by_email(email)
        if not acct:
            return "not_found"
        if acct.password_hash:
            return "has_password"
        return "google_only"

    def create_or_link_google(
        self,
        *,
        telegram_id: int,
        email: str,
        full_name: str,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
        phone: str = "",
        role: str = "student",
        student_id: str = "",
        department: str = "",
        avatar_url: str = "",
    ) -> TelegramAccount:
        existing = self.get_by_email(email)
        now = int(time.time())
        if existing:
            existing.telegram_id = telegram_id
            existing.full_name = full_name or existing.full_name
            existing.first_name = first_name or existing.first_name
            existing.last_name = last_name or existing.last_name
            existing.username = username or existing.username
            existing.auth_provider = "both" if existing.password_hash else "google"
            existing.email_verified = True
            existing.last_login = now
            if avatar_url:
                existing.avatar_url = avatar_url
            if phone:
                existing.phone = phone
            if role:
                existing.role = role
            if student_id:
                existing.student_id = student_id
            if department:
                existing.department = department
            self.save(existing)
            return self.get_by_telegram_id(telegram_id) or existing

        account = TelegramAccount(
            user_id="",
            telegram_id=telegram_id,
            email=email.strip().lower(),
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone=phone,
            role=role,
            student_id=student_id,
            department=department,
            password_hash="",
            auth_provider="google",
            avatar_url=avatar_url,
            email_verified=True,
            created_at=now,
            last_login=now,
        )
        self.save(account)
        return self.get_by_telegram_id(telegram_id) or account

    def verify_login(self, email: str, password: str) -> Optional[TelegramAccount]:
        acct = self.get_by_email(email)
        if not acct or not acct.password_hash:
            return None
        if not verify_password(password, acct.password_hash):
            return None
        acct.last_login = int(time.time())
        self.save(acct)
        return acct

    def verify_login_with_names(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> Optional[TelegramAccount]:
        acct = self.verify_login(email, password)
        if not acct:
            return None
        if not acct.first_name.strip() or not acct.last_name.strip():
            acct.first_name = first_name.strip()
            acct.last_name = last_name.strip()
            acct.full_name = f"{acct.first_name} {acct.last_name}".strip()
            self.save(acct)
            return acct
        if acct.first_name.strip().lower() != first_name.strip().lower():
            return None
        if acct.last_name.strip().lower() != last_name.strip().lower():
            return None
        return acct

    def link_telegram(self, telegram_id: int, email: str) -> Optional[TelegramAccount]:
        acct = self.get_by_email(email)
        if not acct:
            return None
        acct.telegram_id = telegram_id
        acct.last_login = int(time.time())
        self.save(acct)
        return acct


auth_store = TelegramAuthStore()
