from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json

live_router = APIRouter(prefix="/api/live", tags=["live"])


class SessionManager:
    def __init__(self):
        self.sessions: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.sessions[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.sessions:
            del self.sessions[user_id]

    async def send_audio(self, user_id: int, audio_data: bytes):
        if user_id in self.sessions:
            await self.sessions[user_id].send_bytes(audio_data)

    async def send_text(self, user_id: int, text: str):
        if user_id in self.sessions:
            await self.sessions[user_id].send_text(json.dumps({"type": "text", "content": text}))


session_manager = SessionManager()


@live_router.websocket("/ws/{user_id}")
async def live_websocket(websocket: WebSocket, user_id: int):
    await session_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                break
            if "bytes" in data:
                await session_manager.send_text(user_id, "Audio received")
    except WebSocketDisconnect:
        pass
    finally:
        session_manager.disconnect(user_id)


@live_router.post("/transcribe")
async def transcribe_audio():
    return {"transcript": "Sample transcription"}


@live_router.post("/synthesize")
async def synthesize_speech(text: str):
    return {"audio": "base64_audio_data"}


@live_router.get("/health")
async def live_health():
    return {"status": "healthy", "sessions": len(session_manager.sessions)}