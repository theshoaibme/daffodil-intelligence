from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from typing import List, Optional
import json
import asyncio
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import Chat, Message
from ..schemas.user import (
    ChatCreate,
    ChatResponse,
    MessageResponse,
    MessageCreate,
    ChatContextUsageResponse,
)
from ..core.context_usage import compute_chat_context_usage
from ..memory import memory_service
from ..runtime.pipeline import run_turn, run_turn_stream
from ..runtime.event_emitter import TurnEventEmitter, persist_event_log
from ..voice.chat_voice import resolve_voice_message
from uuid import uuid4

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
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = int(user.get("sub"))
    stmt = select(Chat).where(Chat.user_id == user_id)
    term = (q or "").strip()
    if term:
        pattern = f"%{term}%"
        stmt = (
            select(Chat)
            .distinct()
            .outerjoin(Message, Message.chat_id == Chat.id)
            .where(
                Chat.user_id == user_id,
                or_(Chat.title.ilike(pattern), Message.content.ilike(pattern)),
            )
        )
    stmt = stmt.order_by(Chat.created_at.desc())
    result = await db.execute(stmt)
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


@router.get("/{chat_id}/trace")
async def get_chat_trace(
    chat_id: int,
    limit: int = 5,
    user: dict = Depends(get_current_user),
):
    """Recent runtime turn traces (agent/tool/thinking flow) for this chat."""
    from ..runtime.trace import trace_recorder

    user_id = int(user.get("sub"))
    return {
        "chat_id": chat_id,
        "turns": trace_recorder.recent(user_id=user_id, chat_id=chat_id, limit=limit),
    }


@router.get("/{chat_id}/context", response_model=ChatContextUsageResponse)
async def get_chat_context_usage(
    chat_id: int,
    draft: str = "",
    model_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_id = int(user.get("sub"))
    return await compute_chat_context_usage(
        db,
        chat_id=chat_id,
        user_id=user_id,
        draft_message=draft,
        model_id=model_id,
    )


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

    turn_content = message.content
    turn_metadata = dict(message.metadata or {})
    try:
        turn_content, turn_metadata = await resolve_voice_message(turn_content, turn_metadata)
    except ValueError as voice_err:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(voice_err)) from voice_err

    if not (turn_content or "").strip():
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Message content is required")

    user_message = Message(chat_id=chat_id, role="user", content=turn_content, meta=turn_metadata)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    turn_count_result = await db.execute(
        select(Message).where(Message.chat_id == chat_id, Message.role == "user")
    )
    turn_index = len(turn_count_result.scalars().all())

    has_attachments = bool(turn_metadata.get("attachments"))

    async def generate():
        full_response = ""
        tool_calls = []
        ui_blocks = []
        engine = "antigravity"
        resolved_agent = agent_id
        resolved_model = message.model_id
        model_mode = "manual" if message.model_id and message.model_id != "auto" else "auto"
        model_routing = None
        turn_id = f"turn-{uuid4().hex[:12]}"
        emitter = TurnEventEmitter(
            session_id=str(chat_id),
            turn_id=turn_id,
        )
        context_usage = await compute_chat_context_usage(
            db,
            chat_id=chat_id,
            user_id=user_id,
            draft_message=turn_content,
            model_id=message.model_id,
        )
        ctx_envelope = emitter.wrap_legacy({"type": "context", **context_usage})
        yield emitter.sse_line(ctx_envelope)
        try:
            async for event in run_turn_stream(
                turn_content,
                user_id=user_id,
                chat_id=chat_id,
                agent_id=agent_id,
                model_id=message.model_id,
                attachments=turn_metadata.get("attachments") if has_attachments else None,
                metadata=turn_metadata,
            ):
                if not event:
                    continue
                if isinstance(event, str):
                    event = {"type": "content", "content": event}
                event_type = event.get("type", "content")
                if event_type == "model":
                    resolved_model = event.get("model_id", resolved_model)
                    model_mode = event.get("model_mode", model_mode)
                    model_routing = event.get("model_routing")
                if event_type == "content":
                    chunk = event.get("content") or ""
                    if chunk:
                        full_response += chunk
                elif event_type == "ui":
                    block = event.get("block")
                    if isinstance(block, dict):
                        ui_blocks.append(block)
                elif event_type == "tool":
                    tool_name = event.get("name")
                    if tool_name:
                        status = event.get("status", "active")
                        if status == "active" and tool_name not in tool_calls:
                            tool_calls.append(tool_name)
                elif event_type == "agent":
                    resolved_agent = event.get("agent_id", resolved_agent)

                envelope = emitter.wrap_legacy(event)
                yield emitter.sse_line(envelope)

            if not full_response.strip() and not ui_blocks and not tool_calls:
                result = await run_turn(
                    turn_content,
                    user_id=user_id,
                    chat_id=chat_id,
                    agent_id=agent_id,
                    model_id=message.model_id,
                    attachments=turn_metadata.get("attachments") if has_attachments else None,
                    metadata=turn_metadata,
                )
                full_response = result.get("content", "")
                tool_calls = result.get("tool_calls", [])
                engine = result.get("engine", engine)
                resolved_agent = result.get("agent_id", agent_id)
                resolved_model = result.get("model_id", resolved_model)
                model_mode = result.get("model_mode", model_mode)
                model_routing = result.get("model_routing", model_routing)
                for block in result.get("ui_blocks") or []:
                    if isinstance(block, dict):
                        ui_blocks.append(block)
                        yield emitter.sse_line(emitter.wrap_legacy({"type": "ui", "block": block}))
                if full_response:
                    yield emitter.sse_line(
                        emitter.wrap_legacy({"type": "content", "content": full_response})
                    )
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            full_response = f"I encountered an error while processing your request: {str(e)}"
            yield emitter.sse_line(
                emitter.wrap_legacy({"type": "content", "content": full_response})
            )

        from ..runtime.response_validate import validate_assistant_response

        full_response = validate_assistant_response(full_response, ui_blocks)

        # Save assistant message to the database
        try:
            context_usage = await compute_chat_context_usage(
                db,
                chat_id=chat_id,
                user_id=user_id,
                model_id=resolved_model,
            )
        except Exception:
            context_usage = None

        assistant_metadata = {
            "engine": engine,
            "agent_id": resolved_agent,
            "tools_used": tool_calls,
            "ui_blocks": ui_blocks,
            "sources": [],
            "model_id": resolved_model,
            "model_mode": model_mode,
            "model_routing": model_routing,
            "context_usage": context_usage,
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
                    user_msg=turn_content,
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

        await persist_event_log(db, emitter.events)
        yield emitter.done_line()
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