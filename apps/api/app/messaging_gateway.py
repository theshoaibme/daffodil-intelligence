from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import httpx

messaging_router = APIRouter(prefix="/api/messaging", tags=["messaging"])


class MessageRequest(BaseModel):
    chat_id: str
    message: str
    platform: str


async def send_to_api(message: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/agents/chat",
                json={"message": message, "agent_type": "supervisor"},
                timeout=10.0
            )
            return response.json().get("response", "Error processing message")
        except Exception:
            return "Error: Could not reach agent service"


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

    response = await send_to_api(text)
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

    response = await send_to_api(text)

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