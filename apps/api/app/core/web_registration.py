"""Pending web registration payloads until email OTP is verified."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

PENDING_TTL_SECONDS = 600


@dataclass
class PendingRegistration:
    first_name: str
    last_name: str
    password_hash: str
    expires_at: float


class PendingRegistrationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: Dict[str, PendingRegistration] = {}

    def set(self, email: str, *, first_name: str, last_name: str, password_hash: str) -> None:
        key = email.strip().lower()
        with self._lock:
            self._entries[key] = PendingRegistration(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                password_hash=password_hash,
                expires_at=time.time() + PENDING_TTL_SECONDS,
            )

    def pop(self, email: str) -> Optional[PendingRegistration]:
        key = email.strip().lower()
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if time.time() > entry.expires_at:
                del self._entries[key]
                return None
            del self._entries[key]
            return entry


pending_registration_store = PendingRegistrationStore()
