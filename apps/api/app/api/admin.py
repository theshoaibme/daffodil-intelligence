from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User, Chat, Message, Ticket

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    if user_id != 1:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    user_count = await db.scalar(select(func.count(User.id)))
    chat_count = await db.scalar(select(func.count(Chat.id)))
    message_count = await db.scalar(select(func.count(Message.id)))

    return {
        "total_users": user_count or 0,
        "total_chats": chat_count or 0,
        "total_messages": message_count or 0,
    }


@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(select(User).offset(offset).limit(limit))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "department": u.department,
            "role": u.role,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]


@router.get("/tickets")
async def list_tickets(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    result = await db.execute(query.order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat()
        }
        for t in tickets
    ]


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = status
    await db.commit()
    return {"status": "updated"}