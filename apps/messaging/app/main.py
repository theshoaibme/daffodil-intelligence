from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import os

app = FastAPI(title="DI Messaging Gateway")

from voice_handler import voice_handler, VoiceMessage, Platform


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
        except Exception as e:
            return f"Error: {str(e)}"


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id"))
    
    if text.startswith("/"):
        return {"ok": True}
    
    user_key = f"telegram:{chat_id}"
    
    if text.lower() in ["voice", "call", "/voice"]:
        voice_handler.start_voice_session(user_key, Platform.TELEGRAM)
        return {"method": "sendMessage", "chat_id": chat_id, "text": "🎙️ Voice mode activated. Send a voice message or type 'end' to exit."}
    
    if text.lower() == "end" and voice_handler.is_in_voice_session(user_key):
        voice_handler.end_voice_session(user_key)
        return {"method": "sendMessage", "chat_id": chat_id, "text": "👋 Voice mode ended."}
    
    response = await send_to_api(text)
    return {"method": "sendMessage", "chat_id": chat_id, "text": response}


@app.post("/webhook/telegram/voice")
async def telegram_voice(request: Request):
    data = await request.json()
    message = data.get("message", {})
    voice = message.get("voice", {})
    file_id = voice.get("file_id")
    chat_id = str(message.get("chat", {}).get("id"))
    
    user_key = f"telegram:{chat_id}"
    
    if not voice_handler.is_in_voice_session(user_key):
        return {"method": "sendMessage", "chat_id": chat_id, "text": "Start voice mode first with /voice"}
    
    voice_msg = VoiceMessage(
        platform=Platform.TELEGRAM,
        user_id=chat_id,
        audio_data=b"voice_file_data"
    )
    
    result = await voice_handler.handle_voice_message(voice_msg)
    
    return {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": f"🎙️ You said: {result.get('transcript')}\n\n🤖 Response: {result.get('response')}"
    }


@app.post("/webhook/whatsapp")
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
    user_key = f"whatsapp:{from_number}"
    
    if message.get("type") == "voice":
        voice_msg = VoiceMessage(
            platform=Platform.WHATSAPP,
            user_id=from_number,
            audio_data=b"whatsapp_voice"
        )
        result = await voice_handler.handle_voice_message(voice_msg)
        
        return {
            "messaging_product": "whatsapp",
            "to": from_number,
            "text": {
                "body": f"🎙️ You said: {result.get('transcript')}\n\n🤖 Response: {result.get('response')}"
            }
        }
    
    text = message.get("text", {}).get("body", "")
    
    if text.lower() in ["voice", "call"]:
        voice_handler.start_voice_session(user_key, Platform.WHATSAPP)
        return {
            "messaging_product": "whatsapp",
            "to": from_number,
            "text": {"body": "🎙️ Voice mode activated. Send a voice message."}
        }
    
    response = await send_to_api(text)
    
    return {
        "messaging_product": "whatsapp",
        "to": from_number,
        "text": {"body": response}
    }


@app.post("/send")
async def send_message(request: MessageRequest):
    if request.platform == "telegram":
        return {"status": "sent", "platform": "telegram"}
    elif request.platform == "whatsapp":
        return {"status": "sent", "platform": "whatsapp"}
    raise HTTPException(status_code=400, detail="Invalid platform")


@app.post("/voice/start")
async def start_voice_session(platform: str, user_id: str):
    p = Platform.TELEGRAM if platform == "telegram" else Platform.WHATSAPP
    user_key = f"{platform}:{user_id}"
    voice_handler.start_voice_session(user_key, p)
    return {"status": "started"}


@app.post("/voice/end")
async def end_voice_session(platform: str, user_id: str):
    user_key = f"{platform}:{user_id}"
    voice_handler.end_voice_session(user_key)
    return {"status": "ended"}


@app.get("/health")
async def health():
    return {"status": "healthy", "voice_sessions": len(voice_handler.active_voice_sessions)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)