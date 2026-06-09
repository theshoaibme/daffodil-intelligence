"""Pending web registration payloads until email OTP is verified and profile is completed."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import delete, select

from ..core.database import is_mock_database
from ..models.telegram import PendingRegistrationRow
from .pg_sync import sync_session

PENDING_TTL_SECONDS = 600


@dataclass
class PendingRegistration:
    accept_terms: bool = False
    email_verified: bool = False
    first_name: str = ""
    last_name: str = ""
    password_hash: str = ""
    expires_at: float = 0.0


def _row_to_pending(row: PendingRegistrationRow) -> PendingRegistration:
    return PendingRegistration(
        accept_terms=bool(row.accept_terms),
        email_verified=bool(row.email_verified),
        first_name=row.first_name or "",
        last_name=row.last_name or "",
        password_hash=row.password_hash or "",
        expires_at=row.expires_at.timestamp() if row.expires_at else 0.0,
    )


class PendingRegistrationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._memory: Dict[str, PendingRegistration] = {}
        self._use_memory = is_mock_database()

    def _purge_expired_memory(self) -> None:
        now = time.time()
        expired = [k for k, v in self._memory.items() if now > v.expires_at]
        for key in expired:
            del self._memory[key]

    def _purge_expired_pg(self, db) -> None:
        db.execute(
            delete(PendingRegistrationRow).where(
                PendingRegistrationRow.expires_at < datetime.now(timezone.utc)
            )
        )

    def _get_valid(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        if self._use_memory:
            self._purge_expired_memory()
            entry = self._memory.get(key)
            if not entry or time.time() > entry.expires_at:
                self._memory.pop(key, None)
                return None
            return entry
        with sync_session() as db:
            self._purge_expired_pg(db)
            row = db.get(PendingRegistrationRow, key)
            if not row:
                return None
            if row.expires_at < datetime.now(timezone.utc):
                db.delete(row)
                return None
            return _row_to_pending(row)

    def start_email(self, email: str, *, accept_terms: bool) -> None:
        key = email.strip().lower()
        expires = datetime.fromtimestamp(time.time() + PENDING_TTL_SECONDS, tz=timezone.utc)
        with self._lock:
            if self._use_memory:
                self._memory[key] = PendingRegistration(
                    accept_terms=accept_terms,
                    email_verified=False,
                    expires_at=time.time() + PENDING_TTL_SECONDS,
                )
                return
            with sync_session() as db:
                row = db.get(PendingRegistrationRow, key)
                if row is None:
                    row = PendingRegistrationRow(email=key, expires_at=expires)
                    db.add(row)
                row.accept_terms = accept_terms
                row.email_verified = False
                row.expires_at = expires

    def mark_verified(self, email: str) -> bool:
        key = email.strip().lower()
        with self._lock:
            entry = self._get_valid(email)
            if not entry:
                return False
            if self._use_memory:
                entry.email_verified = True
                entry.expires_at = time.time() + PENDING_TTL_SECONDS
                self._memory[key] = entry
                return True
            with sync_session() as db:
                row = db.get(PendingRegistrationRow, key)
                if not row:
                    return False
                row.email_verified = True
                row.expires_at = datetime.fromtimestamp(
                    time.time() + PENDING_TTL_SECONDS, tz=timezone.utc
                )
                return True

    def get_verified(self, email: str) -> Optional[PendingRegistration]:
        with self._lock:
            entry = self._get_valid(email)
            if not entry or not entry.email_verified:
                return None
            return entry

    def pop_verified(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        with self._lock:
            entry = self._get_valid(email)
            if not entry or not entry.email_verified:
                return None
            if self._use_memory:
                del self._memory[key]
            else:
                with sync_session() as db:
                    row = db.get(PendingRegistrationRow, key)
                    if row:
                        db.delete(row)
            return entry

    def set(self, email: str, *, first_name: str, last_name: str, password_hash: str) -> None:
        key = email.strip().lower()
        with self._lock:
            if self._use_memory:
                self._memory[key] = PendingRegistration(
                    accept_terms=True,
                    email_verified=False,
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    password_hash=password_hash,
                    expires_at=time.time() + PENDING_TTL_SECONDS,
                )
                return
            with sync_session() as db:
                row = db.get(PendingRegistrationRow, key)
                if row is None:
                    row = PendingRegistrationRow(
                        email=key,
                        expires_at=datetime.fromtimestamp(
                            time.time() + PENDING_TTL_SECONDS, tz=timezone.utc
                        ),
                    )
                    db.add(row)
                row.accept_terms = True
                row.email_verified = False
                row.first_name = first_name.strip()
                row.last_name = last_name.strip()
                row.password_hash = password_hash

    def pop(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        with self._lock:
            entry = self._get_valid(email)
            if not entry:
                return None
            if self._use_memory:
                del self._memory[key]
            else:
                with sync_session() as db:
                    row = db.get(PendingRegistrationRow, key)
                    if row:
                        db.delete(row)
            return entry


pending_registration_store = PendingRegistrationStore()
