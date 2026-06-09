"""Shared Google OAuth redirect URI and web-login state helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from .config import get_settings
from ..integrations.telegram.tokens import frontend_base, public_base, sign_state, verify_state

settings = get_settings()
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


def _is_local_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in _LOCAL_HOSTS or host.endswith(".local")


def web_google_oauth_redirect_uri() -> str:
    """Redirect URI for browser sign-in from the web app (Vite /api proxy in dev)."""
    override = (getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "") or "").strip()
    if override:
        return override.rstrip("/")
    frontend = frontend_base().rstrip("/")
    if frontend and _is_local_host(frontend):
        return f"{frontend}/api/auth/oauth/google/callback"
    if frontend:
        return f"{frontend}/api/auth/oauth/google/callback"
    return f"{public_base().rstrip('/')}/api/auth/oauth/google/callback"


def telegram_google_oauth_redirect_uri() -> str:
    """Redirect URI for Google sign-in started from Telegram."""
    override = (getattr(settings, "TELEGRAM_GOOGLE_OAUTH_REDIRECT_URI", "") or "").strip()
    if override:
        return override.rstrip("/")
    public = (getattr(settings, "TELEGRAM_OAUTH_PUBLIC_URL", "") or "").strip().rstrip("/")
    if public:
        return f"{public}/api/auth/telegram/google/callback"
    return f"{public_base().rstrip('/')}/api/auth/telegram/google/callback"


def google_oauth_redirect_uri() -> str:
    """Default redirect URI (web)."""
    return web_google_oauth_redirect_uri()


def new_web_oauth_state() -> str:
    return sign_state(0, purpose="web")


def is_web_oauth_state(state: str) -> bool:
    return verify_state(state, purpose="web") is not None
