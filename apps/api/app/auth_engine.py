import hashlib
import hmac
import secrets
import time
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum


class AuthProvider(Enum):
    EMAIL = "email"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    APPLE = "apple"
    GITHUB = "github"


@dataclass
class User:
    user_id: str
    name: str
    email: str
    phone: Optional[str]
    password_hash: Optional[str]
    auth_provider: AuthProvider
    created_at: int
    last_login: int


@dataclass
class AuthResponse:
    status: str
    message: str
    access_token: Optional[str] = None
    user: Optional[Dict] = None


class SecureHasher:
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt, pwd_hash = stored_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except:
            return False


class JWTManager:
    def __init__(self, secret: str = "di-secret-key"):
        self.secret = secret
        
    def create_token(self, user_id: str, email: str, provider: str) -> str:
        payload = f"{user_id}|{email.replace('.','_DOT_')}|{provider}|{int(time.time())}"
        signature = hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        return f"{payload}|{signature}"
    
    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            parts = token.split('|')
            if len(parts) < 4:
                return None
                
            user_id = parts[0]
            email = parts[1].replace('_DOT_', '.')
            provider = parts[2]
            timestamp = parts[3]
            
            if int(time.time()) - int(timestamp) > 3600:
                return None
                
            return {
                "user_id": user_id,
                "email": email,
                "provider": provider
            }
        except:
            return None


class UserStore:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.email_index: Dict[str, str] = {}
        
    def create_user(self, name: str, email: str, password: str = None, 
                    phone: str = None, provider: AuthProvider = AuthProvider.EMAIL) -> User:
        user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        
        password_hash = None
        if password:
            password_hash = SecureHasher.hash_password(password)
            
        user = User(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            auth_provider=provider,
            created_at=int(time.time()),
            last_login=int(time.time())
        )
        
        self.users[user_id] = user
        self.email_index[email] = user_id
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        user_id = self.email_index.get(email)
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def update_last_login(self, user_id: str):
        if user_id in self.users:
            self.users[user_id].last_login = int(time.time())


class AuthenticationEngine:
    def __init__(self):
        self.user_store = UserStore()
        self.jwt = JWTManager()
        
    def register_email(self, name: str, email: str, password: str, 
                      confirm_password: str, phone: str = None) -> AuthResponse:
        if password != confirm_password:
            return AuthResponse(
                status="error",
                message="Passwords do not match"
            )
            
        if self.user_store.get_user_by_email(email):
            return AuthResponse(
                status="error",
                message="Email already registered"
            )
            
        if len(password) < 8:
            return AuthResponse(
                status="error",
                message="Password must be at least 8 characters"
            )
            
        user = self.user_store.create_user(
            name=name,
            email=email,
            password=password,
            phone=phone,
            provider=AuthProvider.EMAIL
        )
        
        token = self.jwt.create_token(user.user_id, user.email, "email")
        
        return AuthResponse(
            status="success",
            message="Registration successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def login_email(self, email: str, password: str) -> AuthResponse:
        user = self.user_store.get_user_by_email(email)
        
        if not user:
            return AuthResponse(
                status="error",
                message="User does not exist"
            )
            
        if user.auth_provider != AuthProvider.EMAIL:
            return AuthResponse(
                status="error",
                message=f"Use {user.auth_provider.value} login"
            )
            
        if not user.password_hash or not SecureHasher.verify_password(password, user.password_hash):
            return AuthResponse(
                status="error",
                message="Invalid credentials"
            )
            
        self.user_store.update_last_login(user.user_id)
        token = self.jwt.create_token(user.user_id, user.email, "email")
        
        return AuthResponse(
            status="success",
            message="Login successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def login_google(self, google_token: str, user_info: Dict) -> AuthResponse:
        email = user_info.get("email")
        name = user_info.get("name", "Google User")
        
        if not email:
            return AuthResponse(
                status="error",
                message="Invalid OAuth token"
            )
            
        user = self.user_store.get_user_by_email(email)
        
        if not user:
            user = self.user_store.create_user(
                name=name,
                email=email,
                provider=AuthProvider.GOOGLE
            )
        else:
            if user.auth_provider != AuthProvider.GOOGLE:
                return AuthResponse(
                    status="error",
                    message="Use email/password for this account"
                )
            self.user_store.update_last_login(user.user_id)
            
        token = self.jwt.create_token(user.user_id, user.email, "google")
        
        return AuthResponse(
            status="success",
            message="Google login successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def login_microsoft(self, access_token: str, user_info: Dict) -> AuthResponse:
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        name = user_info.get("displayName", "Microsoft User")
        
        if not email:
            return AuthResponse(
                status="error",
                message="Invalid OAuth token"
            )
            
        user = self.user_store.get_user_by_email(email)
        
        if not user:
            user = self.user_store.create_user(
                name=name,
                email=email,
                provider=AuthProvider.MICROSOFT
            )
        else:
            if user.auth_provider != AuthProvider.MICROSOFT:
                return AuthResponse(
                    status="error",
                    message="Use email/password for this account"
                )
            self.user_store.update_last_login(user.user_id)
            
        token = self.jwt.create_token(user.user_id, user.email, "microsoft")
        
        return AuthResponse(
            status="success",
            message="Microsoft login successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def login_apple(self, id_token: str, user_info: Dict) -> AuthResponse:
        email = user_info.get("email")
        name = user_info.get("name", {}).get("fullName", "Apple User")
        
        if not email:
            return AuthResponse(
                status="error",
                message="Invalid OAuth token"
            )
            
        user = self.user_store.get_user_by_email(email)
        
        if not user:
            user = self.user_store.create_user(
                name=name,
                email=email,
                provider=AuthProvider.APPLE
            )
        else:
            if user.auth_provider != AuthProvider.APPLE:
                return AuthResponse(
                    status="error",
                    message="Use email/password for this account"
                )
            self.user_store.update_last_login(user.user_id)
            
        token = self.jwt.create_token(user.user_id, user.email, "apple")
        
        return AuthResponse(
            status="success",
            message="Apple login successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def login_github(self, access_token: str, user_info: Dict) -> AuthResponse:
        email = user_info.get("email")
        name = user_info.get("login", "GitHub User")
        
        if not email:
            return AuthResponse(
                status="error",
                message="GitHub email not available"
            )
            
        user = self.user_store.get_user_by_email(email)
        
        if not user:
            user = self.user_store.create_user(
                name=name,
                email=email,
                provider=AuthProvider.GITHUB
            )
        else:
            if user.auth_provider != AuthProvider.GITHUB:
                return AuthResponse(
                    status="error",
                    message="Use email/password for this account"
                )
            self.user_store.update_last_login(user.user_id)
            
        token = self.jwt.create_token(user.user_id, user.email, "github")
        
        return AuthResponse(
            status="success",
            message="GitHub login successful",
            access_token=token,
            user={
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "auth_provider": user.auth_provider.value
            }
        )
    
    def verify_token(self, token: str) -> Optional[Dict]:
        return self.jwt.verify_token(token)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "auth_provider": user.auth_provider.value,
            "created_at": user.created_at,
            "last_login": user.last_login
        }


auth_engine = AuthenticationEngine()