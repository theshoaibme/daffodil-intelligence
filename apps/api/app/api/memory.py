"""
Memory API
==========
Exposes the unified ``MemoryService`` (durable history + semantic notes).
"""

from fastapi import APIRouter, Depends

from ..core.security import get_current_user
from ..memory import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/remember")
async def remember(data: dict, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    text = data.get("text", "")
    if not text:
        return {"error": "Missing 'text'"}
    note = memory_service.remember(text, user_id=user_id, metadata=data.get("metadata"))
    return {"stored": True, "id": note["id"]}


@router.get("/recall")
async def recall(query: str, k: int = 5, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    notes = memory_service.recall(query, user_id=user_id, k=k)
    return {"query": query, "notes": notes, "count": len(notes)}


@router.get("/history/{chat_id}")
async def history(chat_id: int, limit: int = 50, user: dict = Depends(get_current_user)):
    return {"chat_id": chat_id, "messages": await memory_service.get_history(chat_id, limit=limit)}
