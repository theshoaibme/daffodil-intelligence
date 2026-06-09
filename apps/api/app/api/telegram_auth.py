"""Web OAuth endpoints for Telegram users (Google sign-in via browser)."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_db
from ..core.google_oauth_urls import is_web_oauth_state, telegram_google_oauth_redirect_uri
from ..core.security import create_access_token
from ..integrations.telegram.auth_store import auth_store
from ..integrations.telegram.profiles import profile_store, STEP_COMPLETE
from ..integrations.telegram.tokens import frontend_base, verify_state
logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth/telegram", tags=["telegram-auth"])


def _redirect_uri() -> str:
    return telegram_google_oauth_redirect_uri()


async def _notify_telegram_login(telegram_id: int, account, photo_url: str = ""):
    try:
        from ..integrations.telegram.bot import telegram_bot
        await telegram_bot.notify_login_success(
            telegram_id,
            account,
            photo_url=photo_url or None,
        )
    except Exception as e:
        logger.warning("Could not notify Telegram user %s: %s", telegram_id, e)


def _success_redirect(account, telegram_id: int) -> RedirectResponse:
    jwt = create_access_token({
        "sub": account.user_id,
        "email": account.email,
        "telegram_id": str(telegram_id),
        "role": account.role,
        "source": "telegram_google",
    })
    target = f"{frontend_base()}/intelligence/auth/telegram?token={jwt}"
    return RedirectResponse(target, status_code=302)


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

    redirect_uri = _redirect_uri()
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
async def google_callback(
    state: str = Query(...),
    code: str = Query(None),
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if is_web_oauth_state(state):
        login_url = f"{frontend_base()}/login"
        if error:
            return RedirectResponse(f"{login_url}?google_error={error}")
        if not code:
            return RedirectResponse(f"{login_url}?google_error=missing_code")
        if db is None:
            return RedirectResponse(f"{login_url}?google_error=service_unavailable")
        from .auth import finish_web_google_oauth
        return await finish_web_google_oauth(code, db)

    if error:
        hint = (
            "Your Google account must be added as a <b>Test user</b> on the OAuth consent screen "
            "(Google Cloud Console → APIs &amp; Services → OAuth consent screen → Test users)."
        )
        if error == "access_denied":
            hint = "Access denied. " + hint
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;padding:40px'>"
            f"<h2>Google login blocked</h2><p>{hint}</p>"
            f"<p>Then return to Telegram and tap <b>Login with Google</b> again.</p></body></html>",
            status_code=403,
        )

    if not code:
        return HTMLResponse("<h2>Google login failed</h2><p>No authorization code received.</p>", status_code=400)

    telegram_id = verify_state(state)
    if not telegram_id:
        return HTMLResponse("<h2>Link expired</h2><p>Go back to Telegram and tap Login with Google again.</p>", status_code=400)

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    redirect_uri = _redirect_uri()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                logger.error("Google token error (%s): %s", token_resp.status_code, token_resp.text)
                return HTMLResponse(
                    "<h2>Google login failed</h2>"
                    "<p>Could not verify with Google. The link may have expired — try again from Telegram.</p>",
                    status_code=400,
                )

            access_token = token_resp.json().get("access_token")
            if not access_token:
                return HTMLResponse("<h2>Google login failed</h2><p>No access token from Google.</p>", status_code=400)

            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                logger.error("Google userinfo error (%s): %s", user_resp.status_code, user_resp.text)
                return HTMLResponse("<h2>Google login failed</h2><p>Could not load profile.</p>", status_code=400)
            info = user_resp.json()

        email = (info.get("email") or "").strip().lower()
        if not email:
            return HTMLResponse("<h2>Google login failed</h2><p>No email on your Google account.</p>", status_code=400)

        profile = profile_store.get(telegram_id)
        picture = (info.get("picture") or "").strip()
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
            avatar_url=picture,
        )
        profile.email = account.email
        profile.full_name = account.full_name
        profile.role = account.role
        profile.step = STEP_COMPLETE
        profile_store.save(profile)

        await _notify_telegram_login(
            telegram_id,
            account,
            photo_url=picture,
        )

        return _success_redirect(account, telegram_id)
    except Exception:
        logger.exception("Google OAuth callback failed for telegram_id=%s", telegram_id)
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;padding:40px'>"
            "<h2>Something went wrong</h2>"
            "<p>Google sign-in could not be completed. Return to Telegram and try again.</p>"
            "</body></html>",
            status_code=500,
        )
