from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from .runtime import orchestrator

messaging_router = APIRouter(prefix="/api/messaging", tags=["messaging"])


class MessageRequest(BaseModel):
    chat_id: str
    message: str
    platform: str


async def send_to_api(message: str, chat_id: str = "messaging") -> str:
    """Route a message straight through the unified runtime (in-process).

    Avoids the previous self-HTTP call to a JWT-protected endpoint (which 401'd).
    """
    try:
        result = await orchestrator.run(message, user_id=chat_id, chat_id=f"msg-{chat_id}")
        return result.get("content", "") or "(no response)"
    except Exception as e:
        return f"Error: {e}"


@messaging_router.post("/send")
async def send_message(request: MessageRequest):
    return {"status": "sent", "platform": request.platform}


@messaging_router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id"))

    if text.startswith("/"):
        return {"ok": True}

    response = await send_to_api(text, chat_id=chat_id)
    return {"method": "sendMessage", "chat_id": chat_id, "text": response}


@messaging_router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    entry = data.get("entry", [])[0]
    changes = entry.get("changes", [])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])

    if not messages:
        return {"status": "ok"}

    message = messages[0]
    from_number = message.get("from")
    text = message.get("text", {}).get("body", "")

    response = await send_to_api(text, chat_id=from_number or "whatsapp")

    return {
        "messaging_product": "whatsapp",
        "to": from_number,
        "text": {"body": response}
    }


@messaging_router.post("/voice/start")
async def start_voice_session(platform: str, user_id: str):
    return {"status": "started", "platform": platform}


@messaging_router.post("/voice/end")
async def end_voice_session(platform: str, user_id: str):
    return {"status": "ended"}


@messaging_router.get("/health")
async def messaging_health():
    return {"status": "healthy"}