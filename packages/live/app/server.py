from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json
from pydantic import BaseModel

app = FastAPI(title="DI Gemini Live")


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


manager = SessionManager()


class LiveSession(BaseModel):
    user_id: int
    voice_model: str = "Aoede"


@app.websocket("/live/{user_id}")
async def live_websocket(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "session_start",
            "voice": "Aoede",
            "model": "gemini-2.0-flash-exp"
        }))

        while True:
            data = await websocket.receive()

            if "bytes" in data:
                audio_chunk = data["bytes"]
                text = await process_audio(audio_chunk)
                if text:
                    response = await generate_response(text)
                    await manager.send_text(user_id, response)

            elif "text" in data:
                message = json.loads(data["text"])
                if message.get("type") == "text":
                    response = await generate_response(message.get("content", ""))
                    await manager.send_text(user_id, response)

    except WebSocketDisconnect:
        manager.disconnect(user_id)


async def process_audio(audio_data: bytes) -> str:
    return "Transcribed text from audio"


async def generate_response(text: str) -> str:
    return f"DI Response to: {text}"


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)