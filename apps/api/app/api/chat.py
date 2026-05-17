import traceback
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
# নতুন অফিসিয়াল লাইব্রেরি ইমপোর্ট
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import Chat, Message
from ..schemas.user import ChatCreate, ChatResponse, MessageResponse, MessageCreate

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY is required in environment")

# নতুন Client ইনিশিয়ালাইজেশন
client = genai.Client(api_key=gemini_api_key)
# ডিফল্ট মডেল সেটআপ; প্রজেক্টে gemini-flash-latest ব্যবহার করা হলে সাধারণভাবে কাজ করার সম্ভাবনা বেশি।
# যদি আপনার প্রজেক্টে অন্য মডেল অ্যাক্সেস থাকে, তাহলে GEMINI_MODEL_NAME env সেট করুন।
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")

router = APIRouter(prefix="/chats", tags=["chats"])
chat_router = APIRouter(prefix="", tags=["chat"])


class GeminiMessage(BaseModel):
    role: str
    content: str


class GeminiChatRequest(BaseModel):
    message: str
    history: Optional[List[GeminiMessage]] = None


class GeminiChatResponse(BaseModel):
    reply: str
    metadata: Optional[dict] = None


def _normalize_history(history: List[GeminiMessage]) -> List[types.Content]:
    """নতুন google-genai SDK এর স্ট্রাকচার অনুযায়ী চ্যাট হিস্ট্রি অবজেক্ট তৈরি করা"""
    normalized = []
    for item in history:
        role = item.role.strip().lower()
        # জেমিনি 'assistant' বোঝে না, 'model' দিতে হয়
        if role in ("assistant", "system", "model"):
            target_role = "model"
        else:
            target_role = "user"
            
        # নতুন SDK types.Content এবং types.Part এক্সপেক্ট করে
        normalized.append(
            types.Content(
                role=target_role,
                parts=[types.Part.from_text(text=item.content)]
            )
        )
    return normalized


@chat_router.post("/chat", response_model=GeminiChatResponse)
async def chat_with_gemini(request: GeminiChatRequest):
    try:
        # হিস্ট্রি অবজেক্ট লিস্ট জেনারেট করা
        history_payload = _normalize_history(request.history or [])
        
        # নতুন লাইব্রেরিতে চ্যাট সেশন শুরু করার নিয়ম
        # এটি সরাসরি হিস্ট্রি লিস্ট এবং নতুন মেসেজ একসাথে হ্যান্ডেল করতে পারে
        chat_session = client.chats.create(
            model=MODEL_NAME,
            history=history_payload
        )
        
        # মেসেজ পাঠানো
        response = chat_session.send_message(request.message)
        
        # রেসপন্স টেক্সট এক্সট্রাক্ট করা
        reply_text = response.text if hasattr(response, "text") and response.text else str(response)
            
        return GeminiChatResponse(
            reply=reply_text,
            metadata={"history_count": len(history_payload)}
        )
    except Exception as e:
        print("\n" + "="*50)
        print("🔴 GEMINI API ERROR DETECTED")
        print("="*50)
        traceback.print_exc()
        print("="*50 + "\n")
        
        raise HTTPException(status_code=500, detail=f"Gemini chat failed: {str(e)}")


# =====================================================================
# ডাটাবেজ রাউটসমূহ (যা আগে যেভাবে ছিল ঠিক সেভাবেই রাখা হয়েছে)
# =====================================================================

@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    chat_obj = Chat(user_id=user_id, title=chat.title, agent_type=chat.agent_type)
    db.add(chat_obj)
    await db.commit()
    await db.refresh(chat_obj)
    return chat_obj


@router.get("/", response_model=List[ChatResponse])
async def get_chats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await db.execute(select(Chat).where(Chat.user_id == user_id).order_by(Chat.created_at.desc()))
    return result.scalars().all()


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await db.execute(
        select(Message).join(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).order_by(Message.created_at)
    )
    return result.scalars().all()


@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def add_message(
    chat_id: int,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    msg_obj = Message(chat_id=chat_id, role="user", content=message.content, metadata=message.metadata)
    db.add(msg_obj)
    await db.commit()
    await db.refresh(msg_obj)
    return msg_obj