"""Signed tokens for Telegram OAuth deep links."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from ...core.config import get_settings

settings = get_settings()
STATE_TTL = 900


def public_base() -> str:
    return (getattr(settings, "API_PUBLIC_URL", "") or "http://localhost:8000").rstrip("/")


def sign_state(telegram_id: int, purpose: str = "google") -> str:
    secret = settings.JWT_SECRET or getattr(settings, "APP_SECRET_KEY", "") or "di-dev-secret"
    ts = int(time.time())
    payload = f"{purpose}:{telegram_id}:{ts}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{payload}:{sig}"


def verify_state(token: str, purpose: str = "google") -> Optional[int]:
    secret = settings.JWT_SECRET or getattr(settings, "APP_SECRET_KEY", "") or "di-dev-secret"
    try:
        parts = token.split(":")
        if len(parts) != 4:
            return None
        p, tid, ts, sig = parts
        if p != purpose:
            return None
        if int(time.time()) - int(ts) > STATE_TTL:
            return None
        payload = f"{p}:{tid}:{ts}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected):
            return None
        return int(tid)
    except (ValueError, TypeError):
        return None
