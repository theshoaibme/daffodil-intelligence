from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    hash_obj = hashlib.sha256(plain.encode())
    return hash_obj.hexdigest() == hashed


def get_password_hash(password: str) -> str:
    hash_obj = hashlib.sha256(password.encode())
    return hash_obj.hexdigest()


def jwt_secret() -> str:
    return settings.JWT_SECRET or settings.APP_SECRET_KEY or "di-dev-secret"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def decode_token_for_refresh(token: str, max_age_days: int = 7) -> dict:
    """Accept a recently expired access token for refresh (signature still verified)."""
    try:
        payload = jwt.decode(
            token,
            jwt_secret(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    exp = payload.get("exp")
    if exp is not None:
        expired_at = datetime.utcfromtimestamp(exp)
        if datetime.utcnow() > expired_at + timedelta(days=max_age_days):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_token(credentials.credentials)


async def get_refresh_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_token_for_refresh(credentials.credentials)
