"""
Memory API
==========
Unified agent memory: facts, conversations, config snapshots, sub-agents.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..core.security import get_current_user
from ..memory import memory_service
from ..memory.types import ALL_MEMORY_TYPES

router = APIRouter(prefix="/memory", tags=["memory"])


class RememberRequest(BaseModel):
    text: str
    agent_id: str = "main"
    memory_type: str = "fact"
    visibility: str = "private"
    metadata: Optional[dict] = None
    payload: Optional[dict] = None


class ClearRequest(BaseModel):
    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    chat_id: Optional[str] = None
    all: bool = Field(False, alias="all")


@router.get("")
async def list_memories(
    agent_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    scope: Optional[str] = None,
    chat_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    user_id = int(user.get("sub"))
    return await memory_service.list_memories(
        user_id,
        agent_id=agent_id,
        memory_type=memory_type,
        scope=scope,
        chat_id=chat_id,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
async def memory_stats(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return await memory_service.stats(user_id)


@router.get("/context/{agent_id}")
async def memory_context(agent_id: str, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    snapshots = await memory_service.get_context_snapshots(user_id, agent_id)
    return {"agent_id": agent_id, "snapshots": snapshots}


@router.post("/remember")
async def remember(body: RememberRequest, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    if not body.text.strip():
        raise HTTPException(400, "Missing text")
    if body.memory_type not in ALL_MEMORY_TYPES:
        raise HTTPException(400, f"Invalid memory_type: {body.memory_type}")

    note = await memory_service.remember(
        body.text,
        user_id=user_id,
        agent_id=body.agent_id,
        memory_type=body.memory_type,
        visibility=body.visibility,
        source="user",
        metadata=body.metadata,
        payload=body.payload,
    )
    return {"stored": True, "id": note.get("id")}


@router.get("/recall")
async def recall(
    query: str,
    k: int = Query(5, ge=1, le=20),
    agent_id: str = "main",
    memory_type: Optional[str] = None,
    chat_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    user_id = int(user.get("sub"))
    types: Optional[List[str]] = [memory_type] if memory_type else None
    notes = await memory_service.recall(
        query,
        user_id=user_id,
        agent_id=agent_id,
        memory_types=types,
        chat_id=chat_id,
        k=k,
    )
    return {"query": query, "notes": notes, "count": len(notes)}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    ok = await memory_service.delete_memory(memory_id, user_id)
    if not ok:
        raise HTTPException(404, "Memory not found")
    return {"deleted": True, "id": memory_id}


@router.delete("")
async def clear_memories(
    agent_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    chat_id: Optional[str] = None,
    all: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    user_id = int(user.get("sub"))
    count = await memory_service.clear_memories(
        user_id,
        agent_id=agent_id,
        memory_type=memory_type,
        chat_id=chat_id,
        clear_all=all,
    )
    return {"cleared": count}


@router.post("/consolidate")
async def consolidate(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return await memory_service.consolidate(user_id)


@router.post("/summarize/{chat_id}")
async def force_summarize(chat_id: int, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    if not await memory_service.verify_chat_owner(chat_id, user_id):
        raise HTTPException(404, "Chat not found")

    from ..core.database import get_session_maker
    from ..memory.repository import MemoryRepository
    from ..memory.summarizer import maybe_rolling_summary

    maker = get_session_maker()
    if maker is None:
        return {"summarized": False, "reason": "no_database"}

    async with maker() as session:
        repo = MemoryRepository(session)
        turns, total = await repo.list_memories(
            user_id, memory_type="conversation_turn", chat_id=chat_id, limit=200
        )
        result = await maybe_rolling_summary(
            repo,
            user_id=user_id,
            agent_id="main",
            chat_id=chat_id,
            turn_index=max(total, 1),
        )
    return {"summarized": result is not None, "summary_id": result.get("id") if result else None}


@router.get("/history/{chat_id}")
async def history(chat_id: int, limit: int = 50, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    if not await memory_service.verify_chat_owner(chat_id, user_id):
        raise HTTPException(404, "Chat not found")
    messages = await memory_service.get_history(chat_id, limit=limit)
    return {"chat_id": chat_id, "messages": messages}
