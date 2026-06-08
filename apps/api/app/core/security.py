from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings
from .database import get_db

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


async def get_or_create_dev_user(db) -> "User":
    from .database import get_db
    from ..models.user import User
    from sqlalchemy import select
    
    try:
        result = await db.execute(select(User).where(User.email == "dev@daffodil.edu.bd"))
        user = result.scalar_one_or_none()
        if user:
            return user
    except Exception as e:
        print(f"Error finding dev user: {e}")
        user = None

    if not user:
        try:
            user = User(
                email="dev@daffodil.edu.bd",
                password_hash=get_password_hash("devpassword"),
                full_name="Alex Carter",
                role="student"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except Exception as e:
            print(f"Error creating dev user: {e}")
            # Fallback object if commit fails (e.g. MockSession)
            class TempUser:
                id = 1
                email = "dev@daffodil.edu.bd"
                role = "student"
            return TempUser()
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
):
    from .database import get_db
    
    if not credentials:
        if settings.NODE_ENV == "development" or settings.USE_MOCK_DATA:
            user = await get_or_create_dev_user(db)
            return {"sub": str(user.id), "email": user.email, "role": getattr(user, 'role', 'student')}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        if settings.NODE_ENV == "development" or settings.USE_MOCK_DATA:
            user = await get_or_create_dev_user(db)
            return {"sub": str(user.id), "email": user.email, "role": getattr(user, 'role', 'student')}
        raise