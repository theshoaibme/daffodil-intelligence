"""Pending web registration payloads until email OTP is verified and profile is completed."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

PENDING_TTL_SECONDS = 600


@dataclass
class PendingRegistration:
    accept_terms: bool = False
    email_verified: bool = False
    first_name: str = ""
    last_name: str = ""
    password_hash: str = ""
    expires_at: float = 0.0


class PendingRegistrationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: Dict[str, PendingRegistration] = {}

    def _get_valid(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        entry = self._entries.get(key)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            del self._entries[key]
            return None
        return entry

    def start_email(self, email: str, *, accept_terms: bool) -> None:
        key = email.strip().lower()
        with self._lock:
            self._entries[key] = PendingRegistration(
                accept_terms=accept_terms,
                email_verified=False,
                expires_at=time.time() + PENDING_TTL_SECONDS,
            )

    def mark_verified(self, email: str) -> bool:
        key = email.strip().lower()
        with self._lock:
            entry = self._get_valid(email)
            if not entry:
                return False
            entry.email_verified = True
            entry.expires_at = time.time() + PENDING_TTL_SECONDS
            self._entries[key] = entry
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
            del self._entries[key]
            return entry

    # Legacy helpers used while migrating callers
    def set(self, email: str, *, first_name: str, last_name: str, password_hash: str) -> None:
        key = email.strip().lower()
        with self._lock:
            self._entries[key] = PendingRegistration(
                accept_terms=True,
                email_verified=False,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                password_hash=password_hash,
                expires_at=time.time() + PENDING_TTL_SECONDS,
            )

    def pop(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        with self._lock:
            entry = self._get_valid(email)
            if not entry:
                return None
            del self._entries[key]
            return entry


pending_registration_store = PendingRegistrationStore()
