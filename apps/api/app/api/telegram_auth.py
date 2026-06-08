"""Web OAuth endpoints for Telegram users (Google sign-in via browser)."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from ..core.config import get_settings
from ..integrations.telegram.auth_store import auth_store
from ..integrations.telegram.profiles import profile_store, STEP_COMPLETE
from ..integrations.telegram.tokens import public_base, verify_state
from ..prompts.manager import GREETING_EN

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth/telegram", tags=["telegram-auth"])


async def _notify_telegram(telegram_id: int, text: str):
    try:
        from ..integrations.telegram.bot import telegram_bot
        if telegram_bot._app and telegram_bot._app.bot:
            await telegram_bot._app.bot.send_message(chat_id=telegram_id, text=text)
    except Exception as e:
        logger.warning("Could not notify Telegram user %s: %s", telegram_id, e)


@router.get("/google/start")
async def google_start(token: str = Query(...)):
    telegram_id = verify_state(token)
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Invalid or expired link. Send /login in Telegram and try again.")

    if not settings.GOOGLE_CLIENT_ID:
        return HTMLResponse(
            "<h2>Google login not configured</h2>"
            "<p>Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the API .env file.</p>",
            status_code=503,
        )

    redirect_uri = f"{public_base()}/api/auth/telegram/google/callback"
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": token,
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
async def google_callback(code: str = Query(...), state: str = Query(...)):
    telegram_id = verify_state(state)
    if not telegram_id:
        return HTMLResponse("<h2>Link expired</h2><p>Go back to Telegram and tap Login with Google again.</p>", status_code=400)

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    redirect_uri = f"{public_base()}/api/auth/telegram/google/callback"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            logger.error("Google token error: %s", token_resp.text)
            return HTMLResponse("<h2>Google login failed</h2><p>Could not verify with Google.</p>", status_code=400)

        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            return HTMLResponse("<h2>Google login failed</h2><p>Could not load profile.</p>", status_code=400)
        info = user_resp.json()

    email = (info.get("email") or "").strip().lower()
    if not email:
        return HTMLResponse("<h2>Google login failed</h2><p>No email on your Google account.</p>", status_code=400)

    profile = profile_store.get(telegram_id)
    account = auth_store.create_or_link_google(
        telegram_id=telegram_id,
        email=email,
        full_name=info.get("name") or profile.full_name or "Google User",
        first_name=info.get("given_name") or profile.first_name,
        last_name=info.get("family_name") or profile.last_name,
        username=profile.username,
        phone=profile.phone,
        role=profile.role or "student",
        student_id=profile.student_id,
        department=profile.department,
    )
    profile.email = account.email
    profile.full_name = account.full_name
    profile.role = account.role
    profile.step = STEP_COMPLETE
    profile_store.save(profile)

    await _notify_telegram(
        telegram_id,
        f"Google login successful!\n\n"
        f"Name: {account.full_name}\n"
        f"Email: {account.email}\n\n"
        f"{GREETING_EN}",
    )

    return HTMLResponse(
        "<html><body style='font-family:sans-serif;text-align:center;padding:40px'>"
        "<h2>Login successful</h2>"
        "<p>You can close this page and return to Telegram.</p>"
        "</body></html>"
    )
