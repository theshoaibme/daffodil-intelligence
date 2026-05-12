from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from ..auth_engine import auth_engine, AuthProvider

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    token: str
    user_info: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(request: RegisterRequest):
    result = auth_engine.register_email(
        name=request.name,
        email=request.email,
        password=request.password,
        confirm_password=request.confirm_password,
        phone=request.phone
    )
    
    if result.status == "error":
        raise HTTPException(status_code=400, detail=result.message)
    
    return {
        "status": result.status,
        "message": result.message,
        "access_token": result.access_token,
        "user": result.user
    }


@router.post("/login")
async def login(request: LoginRequest):
    result = auth_engine.login_email(request.email, request.password)
    
    if result.status == "error":
        raise HTTPException(status_code=401, detail=result.message)
    
    return {
        "status": result.status,
        "message": result.message,
        "access_token": result.access_token,
        "user": result.user
    }


@router.post("/google")
async def google_login(request: GoogleLoginRequest):
    result = auth_engine.login_google(request.token, request.user_info)
    
    if result.status == "error":
        raise HTTPException(status_code=401, detail=result.message)
    
    return {
        "status": result.status,
        "message": result.message,
        "access_token": result.access_token,
        "user": result.user
    }


@router.get("/verify")
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.replace("Bearer ", "")
    payload = auth_engine.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = auth_engine.get_user(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"status": "valid", "user": user}


@router.get("/me")
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.replace("Bearer ", "")
    payload = auth_engine.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = auth_engine.get_user(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/logout")
async def logout():
    return {"status": "success", "message": "Logged out"}


@router.get("/providers")
async def get_auth_providers():
    return {
        "providers": [
            {"id": "email", "name": "Email/Password", "enabled": True},
            {"id": "google", "name": "Google", "enabled": True},
            {"id": "microsoft", "name": "Microsoft", "enabled": False},
            {"id": "apple", "name": "Apple", "enabled": False},
            {"id": "github", "name": "GitHub", "enabled": False}
        ]
    }