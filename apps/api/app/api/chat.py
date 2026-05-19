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
from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response

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
    
    # Create and save user message
    user_message = Message(chat_id=chat_id, role="user", content=message.content, meta=message.metadata)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    # Detect agent intent
    agents = detect_intent(message.content)
    
    async def generate():
        full_response = ""
        try:
            # Execute agents in the background
            results = await process_with_agents(message.content, agents, {"user_id": user_id})
            
            # Synthesize for UI (preserving markdown and newlines)
            if not results:
                synthesized = "I'm not sure how to help with that. Can you be more specific?"
            elif len(results) == 1:
                synthesized = list(results.values())[0]
            else:
                response_parts = []
                for agent_name, result in results.items():
                    if isinstance(result, str) and not result.startswith("Error"):
                        response_parts.append(result)
                synthesized = "\n\n".join(response_parts)
        except Exception as e:
            logger.error(f"Error processing agents: {e}")
            synthesized = f"I encountered an error while processing your request: {str(e)}"
            
        # Stream the synthesized response line-by-line and word-by-word (preserving newlines)
        lines = synthesized.splitlines(keepends=True)
        for line in lines:
            words = line.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                full_response += chunk
                yield f'data: {json.dumps({"content": chunk})}\n\n'
                await asyncio.sleep(0.02)
            
        # Save assistant message to the database
        assistant_metadata = {
            "agent": ", ".join(agents),
            "tools_used": [],
            "sources": []
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