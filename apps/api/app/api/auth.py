from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import get_password_hash, verify_password, create_access_token, get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, Token, LoginRequest, OAuthRequest
from ..auth_engine import auth_engine
import httpx

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-simple")
async def register_simple(name: str, email: str, password: str):
    result = auth_engine.register_email(name, email, password, password)
    return {"status": result.status, "message": result.message, "user": result.user, "token": result.access_token}


@router.post("/login-simple")
async def login_simple(email: str, password: str):
    result = auth_engine.login_email(email, password)
    return {"status": result.status, "message": result.message, "user": result.user, "token": result.access_token}

GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
MICROSOFT_CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID"
MICROSOFT_CLIENT_SECRET = "YOUR_MICROSOFT_CLIENT_SECRET"
APPLE_CLIENT_ID = "YOUR_APPLE_CLIENT_ID"
APPLE_CLIENT_SECRET = "YOUR_APPLE_CLIENT_SECRET"
GITHUB_CLIENT_ID = "YOUR_GITHUB_CLIENT_ID"
GITHUB_CLIENT_SECRET = "YOUR_GITHUB_CLIENT_SECRET"


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
async def oauth_google(oauth_req: OAuthRequest):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": oauth_req.code,
                "grant_type": "authorization_code",
                "redirect_uri": oauth_req.redirect_uri
            }
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")
        
        access_token = token_resp.json().get("access_token")
        
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_resp.json()
    
    result = auth_engine.login_google(oauth_req.code, user_info)
    if result.status != "success":
        raise HTTPException(status_code=400, detail=result.message)
    
    return {"access_token": result.access_token, "user": result.user}


@router.post("/oauth/microsoft")
async def oauth_microsoft(oauth_req: OAuthRequest):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "code": oauth_req.code,
                "grant_type": "authorization_code",
                "redirect_uri": oauth_req.redirect_uri
            }
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")
        
        access_token = token_resp.json().get("access_token")
        
        user_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_resp.json()
    
    result = auth_engine.login_microsoft(access_token, user_info)
    if result.status != "success":
        raise HTTPException(status_code=400, detail=result.message)
    
    return {"access_token": result.access_token, "user": result.user}


@router.post("/oauth/apple")
async def oauth_apple(oauth_req: OAuthRequest):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://appleid.apple.com/auth/token",
            data={
                "client_id": APPLE_CLIENT_ID,
                "client_secret": APPLE_CLIENT_SECRET,
                "code": oauth_req.code,
                "grant_type": "authorization_code"
            }
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")
        
        id_token = token_resp.json().get("id_token")
        import jwt
        user_info = jwt.decode(id_token, options={"verify_signature": False})
    
    result = auth_engine.login_apple(id_token, user_info)
    if result.status != "success":
        raise HTTPException(status_code=400, detail=result.message)
    
    return {"access_token": result.access_token, "user": result.user}


@router.post("/oauth/github")
async def oauth_github(oauth_req: OAuthRequest):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": oauth_req.code
            },
            headers={"Accept": "application/json"}
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code")
        
        access_token = token_resp.json().get("access_token")
        
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_resp.json()
        
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)
        if primary_email:
            user_info["email"] = primary_email
    
    result = auth_engine.login_github(access_token, user_info)
    if result.status != "success":
        raise HTTPException(status_code=400, detail=result.message)
    
    return {"access_token": result.access_token, "user": result.user}