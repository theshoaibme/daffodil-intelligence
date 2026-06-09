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

    @staticmethod
    def _account_key(account: TelegramAccount) -> str:
        if account.telegram_id:
            return str(account.telegram_id)
        return f"uid:{account.user_id}"

    def save(self, account: TelegramAccount):
        with self._lock:
            self._load()
            email_key = account.email.lower()
            new_key = self._account_key(account)

            # Drop stale keys when an account is relinked or moved off-device.
            stale_keys = [
                key
                for key, acct in self._by_tid.items()
                if key != new_key
                and (
                    acct.user_id == account.user_id
                    or acct.email.lower() == email_key
                )
            ]
            for key in stale_keys:
                del self._by_tid[key]

            self._by_tid[new_key] = account
            self._by_email[email_key] = new_key
            self._save()

    def detach_telegram_session(self, telegram_id: int) -> bool:
        """Sign out on this device only; keep account data for future login."""
        with self._lock:
            self._load()
            key = str(telegram_id)
            account = self._by_tid.get(key)
            if not account:
                return False
            del self._by_tid[key]
            account.telegram_id = 0
            storage_key = self._account_key(account)
            self._by_tid[storage_key] = account
            self._by_email[account.email.lower()] = storage_key
            self._save()
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

    def login_email_status(self, email: str) -> str:
        """Return not_found | google_only | has_password for login routing."""
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
            avatar_url=avatar_url,
            email_verified=True,
            created_at=now,
            last_login=now,
        )
        self.save(account)
        return account

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
