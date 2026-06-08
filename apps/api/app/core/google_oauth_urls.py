"""Shared Google OAuth redirect URI and web-login state helpers."""

from __future__ import annotations

from .config import get_settings
from ..integrations.telegram.tokens import public_base, sign_state, verify_state

settings = get_settings()


def google_oauth_redirect_uri() -> str:
    """Redirect URI sent to Google — must match Google Cloud Console exactly."""
    override = (getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "") or "").strip()
    if override:
        return override.rstrip("/")
    return f"{public_base()}/api/auth/telegram/google/callback"


def new_web_oauth_state() -> str:
    return sign_state(0, purpose="web")


def is_web_oauth_state(state: str) -> bool:
    return verify_state(state, purpose="web") is not None
