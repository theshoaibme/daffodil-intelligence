from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import asyncio
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import Chat, Message
from ..schemas.user import ChatCreate, ChatResponse, MessageResponse, MessageCreate
from ..memory import memory_service
from ..runtime.pipeline import run_turn, run_turn_stream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


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


@router.post("/{chat_id}/messages")
async def add_message(
    chat_id: int,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))

    chat_row = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat_obj = chat_row.scalar_one_or_none()
    agent_id = chat_obj.agent_type if chat_obj else "main"

    user_message = Message(chat_id=chat_id, role="user", content=message.content, meta=message.metadata)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    turn_count_result = await db.execute(
        select(Message).where(Message.chat_id == chat_id, Message.role == "user")
    )
    turn_index = len(turn_count_result.scalars().all())

    async def generate():
        full_response = ""
        tool_calls = []
        engine = "antigravity"
        resolved_agent = agent_id
        try:
            async for event in run_turn_stream(
                message.content,
                user_id=user_id,
                chat_id=chat_id,
                agent_id=agent_id,
            ):
                if not event:
                    continue
                if isinstance(event, str):
                    event = {"type": "content", "content": event}
                event_type = event.get("type", "content")
                if event_type == "content":
                    chunk = event.get("content") or ""
                    if not chunk:
                        continue
                    full_response += chunk
                    yield f'data: {json.dumps({"type": "content", "content": chunk})}\n\n'
                elif event_type == "thinking":
                    thinking = event.get("content") or ""
                    if thinking:
                        yield f'data: {json.dumps({"type": "thinking", "content": thinking})}\n\n'
                elif event_type == "tool":
                    tool_name = event.get("name")
                    if not tool_name:
                        continue
                    status = event.get("status", "active")
                    if status == "active" and tool_name not in tool_calls:
                        tool_calls.append(tool_name)
                    yield f'data: {json.dumps({"type": "tool", "name": tool_name, "status": status})}\n\n'
            if not full_response.strip():
                result = await run_turn(
                    message.content,
                    user_id=user_id,
                    chat_id=chat_id,
                    agent_id=agent_id,
                )
                full_response = result.get("content", "")
                tool_calls = result.get("tool_calls", [])
                engine = result.get("engine", engine)
                resolved_agent = result.get("agent_id", agent_id)
                if full_response:
                    yield f'data: {json.dumps({"content": full_response})}\n\n'
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            full_response = f"I encountered an error while processing your request: {str(e)}"
            yield f'data: {json.dumps({"content": full_response})}\n\n'

        # Save assistant message to the database
        assistant_metadata = {
            "engine": engine,
            "agent_id": resolved_agent,
            "tools_used": tool_calls,
            "sources": [],
        }
        
        try:
            assistant_message = Message(
                chat_id=chat_id,
                role="assistant",
                content=full_response,
                meta=assistant_metadata
            )
            db.add(assistant_message)
            await db.commit()
            await db.refresh(assistant_message)

            try:
                await memory_service.process_turn_memory(
                    user_id=user_id,
                    agent_id=resolved_agent,
                    chat_id=chat_id,
                    user_msg=message.content,
                    assistant_msg=full_response,
                    turn_index=turn_index,
                )
            except Exception as mem_err:
                logger.warning("Turn memory processing failed: %s", mem_err)
            
            # Yield final message payload
            final_payload = {
                "id": assistant_message.id,
                "chat_id": chat_id,
                "role": "assistant",
                "content": full_response,
                "metadata": assistant_metadata,
                "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
        except Exception as e:
            logger.error(f"Error saving assistant message: {e}")
            # Fallback final payload if DB save fails
            final_payload = {
                "id": int(asyncio.get_event_loop().time() * 1000),
                "chat_id": chat_id,
                "role": "assistant",
                "content": full_response,
                "metadata": assistant_metadata,
                "created_at": None
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
            
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )