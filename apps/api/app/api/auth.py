import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.google_oauth_urls import google_oauth_redirect_uri, new_web_oauth_state
from ..core.web_registration import pending_registration_store
from ..integrations.telegram.otp import otp_service
from ..integrations.telegram.tokens import frontend_base
from ..core.database import get_db
from ..core.security import create_access_token, get_current_user, get_password_hash, verify_password
from ..models.user import User
from ..schemas.user import (
    LoginRequest,
    OAuthRequest,
    RegisterOtpResponse,
    RegisterSendOtpRequest,
    RegisterVerifyOtpRequest,
    Token,
    UserCreate,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_or_create_oauth_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    avatar_url: str = "",
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    picture = (avatar_url or "").strip()

    if user:
        changed = False
        if picture and user.avatar_url != picture:
            user.avatar_url = picture
            changed = True
        if full_name and full_name.strip() and user.full_name != full_name.strip():
            user.full_name = full_name.strip()
            changed = True
        if changed:
            await db.commit()
            await db.refresh(user)
        return user

    user_obj = User(
        email=email,
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        full_name=full_name or email.split("@")[0],
        role="student",
        avatar_url=picture or None,
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)
    return user_obj


def _oauth_token_response(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {
        "access_token": token,
        "user": UserResponse.model_validate(user),
    }


async def finish_web_google_oauth(code: str, db: AsyncSession) -> RedirectResponse:
    login_url = f"{frontend_base()}/login"
    redirect_uri = google_oauth_redirect_uri()

    try:
        user_info = await _fetch_google_user_info(code, redirect_uri)
        email = (user_info.get("email") or "").strip().lower()
        if not email:
            return RedirectResponse(f"{login_url}?google_error=invalid_token")

        user = await _get_or_create_oauth_user(
            db,
            email,
            user_info.get("name", "Google User"),
            user_info.get("picture", ""),
        )
        token = create_access_token({"sub": str(user.id), "email": user.email})
    except HTTPException:
        return RedirectResponse(f"{login_url}?google_error=oauth_failed")

    target = f"{frontend_base()}/intelligence/auth/google/callback?{urlencode({'token': token})}"
    return RedirectResponse(target)


async def _fetch_google_user_info(code: str, redirect_uri: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on the server")

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
            raise HTTPException(status_code=400, detail="Invalid OAuth code")

        access_token = token_resp.json().get("access_token")

        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return user_resp.json()


@router.get("/oauth/google/config")
async def google_oauth_config():
    client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
    if not client_id:
        return {"enabled": False, "client_id": None}
    return {
        "enabled": True,
        "client_id": client_id,
        "redirect_uri": google_oauth_redirect_uri(),
    }


@router.get("/oauth/google/start")
async def google_oauth_start():
    client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
    if not client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on the server")

    redirect_uri = google_oauth_redirect_uri()
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": new_web_oauth_state(),
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Legacy callback path — web sign-in uses /api/auth/telegram/google/callback."""
    login_url = f"{frontend_base()}/login"

    if error:
        return RedirectResponse(f"{login_url}?google_error={error}")
    if not code:
        return RedirectResponse(f"{login_url}?google_error=missing_code")
    if db is None:
        return RedirectResponse(f"{login_url}?google_error=service_unavailable")

    return await finish_web_google_oauth(code, db)


@router.post("/register/send-otp", response_model=RegisterOtpResponse)
async def register_send_otp(data: RegisterSendOtpRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    if not data.accept_terms:
        raise HTTPException(status_code=400, detail="You must accept the Terms of Service and Privacy Policy")

    email = data.email.strip().lower()
    if not otp_service.is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    pending_registration_store.set(
        email,
        first_name=data.first_name,
        last_name=data.last_name,
        password_hash=get_password_hash(data.password),
    )

    code = otp_service.generate(email)
    sent, dev_hint = otp_service.send(email, code)

    response = RegisterOtpResponse(
        message="Verification code sent to your email",
        email=email,
    )
    if not sent:
        if settings.NODE_ENV == "development":
            response.dev_otp = dev_hint or code
            response.message = "Verification code generated (SMTP not configured — use dev_otp in development)"
        else:
            raise HTTPException(status_code=503, detail="Unable to send verification email. Try again later.")

    return response


@router.post("/register/verify-otp")
async def register_verify_otp(data: RegisterVerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    email = data.email.strip().lower()
    if not otp_service.verify(email, data.code.strip()):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    pending = pending_registration_store.pop(email)
    if not pending:
        raise HTTPException(status_code=400, detail="Registration session expired. Please start again.")

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    full_name = f"{pending.first_name} {pending.last_name}".strip()
    user_obj = User(
        email=email,
        password_hash=pending.password_hash,
        full_name=full_name,
        role="student",
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)

    return {
        "message": "Registration successful",
        "email": email,
        "user": UserResponse.model_validate(user_obj),
    }


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    result = await db.execute(select(User).where(User.email == user.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_obj = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        full_name=user.full_name,
        student_id=user.student_id,
        department=user.department,
        semester=user.semester
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)
    return user_obj


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user_obj = result.scalar_one_or_none()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return user_obj


@router.post("/oauth/google")
async def oauth_google(oauth_req: OAuthRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    user_info = await _fetch_google_user_info(oauth_req.code, oauth_req.redirect_uri)

    email = (user_info.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Invalid OAuth token")

    user = await _get_or_create_oauth_user(
        db,
        email,
        user_info.get("name", "Google User"),
        user_info.get("picture", ""),
    )
    return _oauth_token_response(user)


@router.post("/oauth/microsoft")
async def oauth_microsoft(oauth_req: OAuthRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "code": oauth_req.code,
                "grant_type": "authorization_code",
                "redirect_uri": oauth_req.redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")

        access_token = token_resp.json().get("access_token")

        user_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_info = user_resp.json()

    email = (user_info.get("mail") or user_info.get("userPrincipalName") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Invalid OAuth token")

    user = await _get_or_create_oauth_user(db, email, user_info.get("displayName", "Microsoft User"))
    return _oauth_token_response(user)


@router.post("/oauth/apple")
async def oauth_apple(oauth_req: OAuthRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    import jwt as pyjwt

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://appleid.apple.com/auth/token",
            data={
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": settings.APPLE_CLIENT_SECRET,
                "code": oauth_req.code,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")

        id_token = token_resp.json().get("id_token")
        user_info = pyjwt.decode(id_token, options={"verify_signature": False})

    email = (user_info.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Invalid OAuth token")

    name = user_info.get("name", {})
    full_name = name.get("fullName", "Apple User") if isinstance(name, dict) else "Apple User"
    user = await _get_or_create_oauth_user(db, email, full_name)
    return _oauth_token_response(user)


@router.post("/oauth/github")
async def oauth_github(oauth_req: OAuthRequest, db: AsyncSession = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": oauth_req.code,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")

        access_token = token_resp.json().get("access_token")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_info = user_resp.json()

        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)
        if primary_email:
            user_info["email"] = primary_email

    email = (user_info.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="GitHub email not available")

    user = await _get_or_create_oauth_user(db, email, user_info.get("login", "GitHub User"))
    return _oauth_token_response(user)