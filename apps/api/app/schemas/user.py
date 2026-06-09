from pydantic import BaseModel, EmailStr, Field
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
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterSendOtpRequest(BaseModel):
    email: EmailStr
    accept_terms: bool


class RegisterVerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)


class RegisterCompleteRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="student", pattern=r"^(student|teacher|staff|manager)$")


class RegisterOtpResponse(BaseModel):
    message: str
    email: str
    dev_otp: Optional[str] = None


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
    model_id: Optional[str] = None
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContextUsageBreakdown(BaseModel):
    messages: int = 0
    draft: int = 0
    memory_recall: int = 0
    system_overhead: int = 0


class ChatContextUsageResponse(BaseModel):
    usage_ratio: float
    used_tokens: int
    max_tokens: int
    usage_percent: int
    breakdown: ContextUsageBreakdown
    message_count: int
    model_id: Optional[str] = None


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


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    student_id: Optional[str] = Field(default=None, max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)
    semester: Optional[int] = Field(
        default=None,
        ge=1,
        le=999,
        description="Batch ID (e.g. 64, 65, 67)",
    )
    avatar_url: Optional[str] = Field(default=None, max_length=512)


DELETE_ACCOUNT_PHRASE = "Delete my account"


class DeleteAccountRequest(BaseModel):
    confirmation_phrase: str = Field(min_length=1, max_length=64)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)