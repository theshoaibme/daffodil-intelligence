from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    student_id: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    cgpa: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ChatCreate(BaseModel):
    title: str
    agent_type: str


class ChatResponse(BaseModel):
    id: int
    title: str
    agent_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRequest(BaseModel):
    message: str
    agent_type: str
    chat_id: Optional[int] = None
    session_id: Optional[int] = None


class AgentResponse(BaseModel):
    response: str
    agent: str
    tools_used: list[str] = []
    sources: list[str] = []


class StreamResponse(BaseModel):
    chunk: str
    done: bool


class OAuthRequest(BaseModel):
    code: str
    redirect_uri: str