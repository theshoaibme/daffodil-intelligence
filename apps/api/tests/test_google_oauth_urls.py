"""Google OAuth redirect URI helpers."""

from app.core.google_oauth_urls import (
    is_web_oauth_state,
    new_web_oauth_state,
    telegram_google_oauth_redirect_uri,
    web_google_oauth_redirect_uri,
)
from app.integrations.telegram.tokens import google_login_url


def test_web_redirect_uri_uses_api_host_in_dev():
    uri = web_google_oauth_redirect_uri()
    assert uri.endswith("/api/auth/oauth/google/callback")
    assert ":8000" in uri


def test_telegram_redirect_uri_uses_api_host_in_dev():
    uri = telegram_google_oauth_redirect_uri()
    assert uri.endswith("/api/auth/telegram/google/callback")
    assert ":8000" in uri


def test_web_oauth_state_round_trip():
    state = new_web_oauth_state()
    assert state.startswith("web:0:")
    assert is_web_oauth_state(state)


def test_telegram_google_start_uses_api_not_frontend():
    url = google_login_url(42)
    assert "/api/auth/telegram/google/start" in url
    assert ":8000" in url
