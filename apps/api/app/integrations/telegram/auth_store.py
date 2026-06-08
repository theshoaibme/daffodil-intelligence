"""Persistent Telegram-linked user accounts (email / Google / password)."""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional

from ...core.security import get_password_hash, verify_password


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
    auth_provider: str = "email"  # email | google
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


class TelegramAuthStore:
    def __init__(self, path: str = "telegram_users.json"):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._by_tid: Dict[str, TelegramAccount] = {}
        self._by_email: Dict[str, str] = {}
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                for tid, data in raw.items():
                    acct = TelegramAccount(**data)
                    self._by_tid[tid] = acct
                    self._by_email[acct.email.lower()] = tid
            except Exception:
                self._by_tid = {}
                self._by_email = {}
        self._loaded = True

    def _save(self):
        self._path.write_text(
            json.dumps({tid: asdict(a) for tid, a in self._by_tid.items()}, indent=2),
            "utf-8",
        )

    def get_by_telegram_id(self, telegram_id: int) -> Optional[TelegramAccount]:
        with self._lock:
            self._load()
            return self._by_tid.get(str(telegram_id))

    def get_by_email(self, email: str) -> Optional[TelegramAccount]:
        with self._lock:
            self._load()
            tid = self._by_email.get(email.strip().lower())
            return self._by_tid.get(tid) if tid else None

    def email_taken(self, email: str, exclude_telegram_id: Optional[int] = None) -> bool:
        acct = self.get_by_email(email)
        if not acct:
            return False
        if exclude_telegram_id and acct.telegram_id == exclude_telegram_id:
            return False
        return True

    def save(self, account: TelegramAccount):
        with self._lock:
            self._load()
            email_key = account.email.lower()
            new_tid = str(account.telegram_id)

            # Drop stale telegram_id keys when an account is relinked.
            stale_tids = [
                tid
                for tid, acct in self._by_tid.items()
                if tid != new_tid
                and (
                    acct.user_id == account.user_id
                    or acct.email.lower() == email_key
                )
            ]
            for tid in stale_tids:
                del self._by_tid[tid]

            self._by_tid[new_tid] = account
            self._by_email[email_key] = new_tid
            self._save()

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
        user_id = hashlib.sha256(f"{email}:{telegram_id}".encode()).hexdigest()[:16]
        account = TelegramAccount(
            user_id=user_id,
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
        return account

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
    ) -> TelegramAccount:
        existing = self.get_by_email(email)
        now = int(time.time())
        if existing:
            existing.telegram_id = telegram_id
            existing.full_name = full_name or existing.full_name
            existing.first_name = first_name or existing.first_name
            existing.last_name = last_name or existing.last_name
            existing.username = username or existing.username
            existing.auth_provider = "google"
            existing.email_verified = True
            existing.last_login = now
            if phone:
                existing.phone = phone
            if role:
                existing.role = role
            if student_id:
                existing.student_id = student_id
            if department:
                existing.department = department
            self.save(existing)
            return existing

        user_id = hashlib.sha256(f"google:{email}:{secrets.token_hex(4)}".encode()).hexdigest()[:16]
        account = TelegramAccount(
            user_id=user_id,
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
            email_verified=True,
            created_at=now,
            last_login=now,
        )
        self.save(account)
        return account

    def verify_login(self, email: str, password: str) -> Optional[TelegramAccount]:
        acct = self.get_by_email(email)
        if not acct or acct.auth_provider != "email":
            return None
        if not acct.password_hash or not verify_password(password, acct.password_hash):
            return None
        acct.last_login = int(time.time())
        self.save(acct)
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
