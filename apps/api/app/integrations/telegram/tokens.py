"""Signed tokens for Telegram OAuth deep links."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional
from urllib.parse import urlparse

from ...core.config import get_settings

settings = get_settings()
STATE_TTL = 900


def public_base() -> str:
    return (getattr(settings, "API_PUBLIC_URL", "") or "http://localhost:8000").rstrip("/")


def frontend_base() -> str:
    """User-facing origin (Vite dev server proxies /api to the API)."""
    return (getattr(settings, "FRONTEND_PUBLIC_URL", "") or public_base()).rstrip("/")


def oauth_redirect_base() -> str:
    """OAuth callback base — prefer frontend so the browser stays on :3000."""
    return frontend_base()


def telegram_oauth_base() -> str:
    """Public origin for Telegram OAuth start links (API host, or TELEGRAM_OAUTH_PUBLIC_URL)."""
    override = (getattr(settings, "TELEGRAM_OAUTH_PUBLIC_URL", "") or "").strip()
    if override:
        return override.rstrip("/")
    return public_base().rstrip("/")


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


def is_telegram_inline_url(url: str) -> bool:
    """Telegram rejects localhost/private hosts on inline URL buttons."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host or host in _LOCAL_HOSTS:
        return False
    if host.endswith(".local") or host.endswith(".localhost"):
        return False
    return True


def google_login_url(telegram_id: int) -> str:
    token = sign_state(telegram_id)
    return f"{telegram_oauth_base()}/api/auth/telegram/google/start?token={token}"


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
