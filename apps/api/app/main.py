import logging
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

# নতুন লাইব্রেরি ইমপোর্ট করা হলো
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .api import (
    admin,
    agent_builder,
    agents,
    auth,
    chat,
    rag,
    upload,
    voice,
    websocket,
)
from .core.config import get_settings
from .core.database import close_db, init_db
from .core.middleware import LoggingMiddleware
from .live_broadcaster import live_router
from .messaging_gateway import messaging_router
from .mcp.client import mcp_client

# এনভায়রনমেন্ট এবং ফাইল পাথ সেটআপ
settings = get_settings()
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

Path("logs").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await mcp_client.close()
    await close_db()


# FastAPI অ্যাপ ইনিশিয়ালাইজেশন
app = FastAPI(
    title="Daffodil Intelligence API",
    description="360° Multi-Agent AI Operating System for University",
    version="1.0.0",
    lifespan=lifespan,
)

# -------------------------------------------------------------
# CORS এবং মিডলওয়্যার সেটিংস
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)


# -------------------------------------------------------------
# চ্যাটবটের স্কিমা এবং নতুন জেমিনি কনফিগারেশন
# -------------------------------------------------------------
load_dotenv()
# GEMINI_API_KEY বা GOOGLE_API_KEY যেকোনো একটি ব্যবহার করুন।
# Docker Compose env_file এবং local .env উভয় ক্ষেত্রেই এটি কাজ করবে।
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if gemini_api_key:
    # নতুন SDK-তে Client ইনিশিয়ালাইজ করার নিয়ম
    ai_client = genai.Client(api_key=gemini_api_key)
    # ডিফল্ট মডেল: gemini-2.5-flash ব্যবহার করুন যদি আপনার প্রজেক্টে অ্যাক্সেস থাকে।
    # অন্য মডেল ব্যবহার করতে হলে GEMINI_MODEL_NAME env-এ সেট করুন।
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    logging.info(
        "Using Gemini API key from %s",
        "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "GOOGLE_API_KEY",
    )
else:
    logging.warning("⚠️ GEMINI_API_KEY env ভ্যারিয়েবলটি পাওয়া যায়নি!")
    ai_client = None
    GEMINI_MODEL_NAME = None


class GeminiMessage(BaseModel):
    role: str
    content: str


class GeminiChatRequest(BaseModel):
    message: str
    history: Optional[List[GeminiMessage]] = None


class GeminiChatResponse(BaseModel):
    reply: str
    metadata: Optional[dict] = None


def _normalize_history_new(history: List[GeminiMessage]) -> List[types.Content]:
    """নতুন google-genai লাইব্রেরির Content অবজেক্ট ফরম্যাটে হিস্ট্রি কনভার্ট করার ফাংশন"""
    normalized = []
    for item in history:
        role = item.role.strip().lower()
        # নতুন লাইব্রেরিতে 'user' অথবা 'model' রোল ব্যবহার করতে হয়
        if role in ("assistant", "system", "model"):
            target_role = "model"
        else:
            target_role = "user"
            
        normalized.append(
            types.Content(
                role=target_role,
                parts=[types.Part.from_text(text=item.content)]
            )
        )
    return normalized


# -------------------------------------------------------------
# চ্যাটবটের ডেডিকেটেড এন্ডপয়েন্ট (POST /api/chat)
# -------------------------------------------------------------
@app.post("/api/chat", response_model=GeminiChatResponse)
async def chat_with_gemini(request: GeminiChatRequest):
    if not ai_client:
        raise HTTPException(
            status_code=500,
            detail="Gemini Client configuration missing. Check GEMINI_API_KEY in .env file.",
        )

    try:
        # চ্যাট হিস্ট্রি নতুন ফরম্যাটে রেডি করা হলো
        history_payload = _normalize_history_new(request.history or [])
        
        # নতুন SDK-তে চ্যাট সেশন শুরু করার অফিশিয়াল নিয়ম
        chat_session = ai_client.chats.create(
            model=GEMINI_MODEL_NAME,
            history=history_payload
        )
        
        # মেসেজ পাঠানো
        response = chat_session.send_message(request.message)

        # রেসপন্স টেক্সট এক্সট্রাক্ট করা
        reply_text = response.text if hasattr(response, "text") else str(response)

        return GeminiChatResponse(
            reply=reply_text,
            metadata={"history_count": len(history_payload)},
        )
        
    except APIError as e:
        # জেমিনি এপিআই সংক্রান্ত নির্দিষ্ট এরর হ্যান্ডলিং
        print("\n" + "=" * 50)
        print("🔴 MAIN.PY: GEMINI NEW API ERROR DETECTED")
        print("=" * 50)
        print(f"Status Code: {e.code}")
        print(f"Message: {e.message}")
        print("=" * 50 + "\n")
        raise HTTPException(
            status_code=500, detail=f"Gemini API execution failed: {e.message}"
        )
    except Exception as e:
        # অন্যান্য সাধারণ এরর হ্যান্ডলিং
        print("\n" + "=" * 50)
        print("🔴 MAIN.PY: UNEXPECTED CHAT ERROR DETECTED")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50 + "\n")
        raise HTTPException(
            status_code=500, detail=f"Gemini chat failed unexpectedly: {str(e)}"
        )


# -------------------------------------------------------------
# আপনার অ্যাপ্লিকেশনের অন্যান্য রাউটারসমূহ
# -------------------------------------------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
# app.include_router(chat.chat_router, prefix="/api")  # duplicate /api/chat route removed
app.include_router(rag.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(agent_builder.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(live_router)
app.include_router(messaging_router)
app.websocket("/ws/{user_id}")(websocket.websocket_endpoint)
app.websocket("/voice/ws/{user_id}")(voice.voice_websocket)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Daffodil Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "services": ["api", "mcp", "live", "messaging"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "di-api",
        "tools": (
            len(mcp_client.registry) if hasattr(mcp_client, "registry") else 0
        ),
    }


@app.get("/api/agents/list")
async def list_agents():
    return {
        "agents": [
            {"id": "academic", "name": "Academic Agent", "status": "active"},
            {"id": "library", "name": "Library Agent", "status": "active"},
            {"id": "campus", "name": "Campus Agent", "status": "active"},
            {"id": "career", "name": "Career Agent", "status": "active"},
            {"id": "coding", "name": "Coding Agent", "status": "active"},
            {"id": "research", "name": "Research Agent", "status": "active"},
            {"id": "wellness", "name": "Wellness Agent", "status": "active"},
            {"id": "finance", "name": "Finance Agent", "status": "active"},
            {"id": "vision", "name": "Vision Agent", "status": "active"},
            {"id": "voice", "name": "Voice Agent", "status": "active"},
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)