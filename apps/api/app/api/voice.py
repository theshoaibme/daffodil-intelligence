from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from ..core.security import get_current_user
from ..voice.realtime import voice_engine, VoiceState

router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceCallRequest(BaseModel):
    language: Optional[str] = "en"
    voice_model: Optional[str] = "Aoede"


class AudioChunkRequest(BaseModel):
    audio_data: str


@router.post("/call/start")
async def start_voice_call(
    request: VoiceCallRequest = VoiceCallRequest(),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.start_call(user_id)
    return result


@router.post("/call/end")
async def end_voice_call(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return await voice_engine.end_call(user_id)


@router.post("/audio/process")
async def process_audio(
    request: AudioChunkRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    return await voice_engine.process_audio_chunk(user_id, request.audio_data)


@router.get("/status")
async def get_voice_status(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    session = voice_engine.get_session(user_id)
    if session:
        return {
            "active": True,
            "session_id": session.session_id,
            "state": session.state.value,
            "language": session.language
        }
    return {"active": False}


@router.websocket("/ws/voice/{user_id}")
async def voice_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    
    session_data = await voice_engine.start_call(user_id)
    await websocket.send_json({
        "type": "connected",
        "session": session_data
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "audio":
                result = await voice_engine.process_audio_chunk(
                    user_id,
                    message.get("data", "")
                )
                await websocket.send_json({
                    "type": "response",
                    "transcript": result.get("transcript"),
                    "response": result.get("response"),
                    "audio": result.get("audio")
                })
            
            elif message.get("type") == "text":
                text = message.get("data")
                result = await voice_engine.process_audio_chunk(user_id, "")
                result["transcript"] = text
                await websocket.send_json({
                    "type": "response",
                    "response": result.get("response", "Processing...")
                })
            
            elif message.get("type") == "end":
                await voice_engine.end_call(user_id)
                break
                
    except WebSocketDisconnect:
        await voice_engine.end_call(user_id)


class VoiceConfig:
    AVAILABLE_VOICES = ["Aoede", "Puck", "Charon", "Ernie", "Fenrir"]
    DEFAULT_VOICE = "Aoede"
    SUPPORTED_LANGUAGES = ["en", "bn", "es", "fr", "de", "zh", "ja"]


@router.get("/voices")
async def get_available_voices():
    return {
        "voices": VoiceConfig.AVAILABLE_VOICES,
        "default": VoiceConfig.DEFAULT_VOICE
    }


@router.get("/languages")
async def get_supported_languages():
    return {"languages": VoiceConfig.SUPPORTED_LANGUAGES}