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
    result = await voice_engine.start_call(user_id, request.language, request.voice_model)
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
                    "response": result.get("response")
                })
            
            elif message.get("type") == "text":
                text = message.get("data")
                language = message.get("language", "en")
                result = await voice_engine.process_text_message(user_id, text)
                
                if result.get("state") == "success":
                    response_text = result.get("response", "")
                    
                    async for chunk in voice_engine.stream_text_to_speech(response_text, user_id):
                        if chunk["type"] == "interrupted":
                            await websocket.send_json({"type": "interrupted"})
                            break
                        elif chunk["type"] == "audio_chunk":
                            await websocket.send_json({
                                "type": "audio_chunk",
                                "audio": chunk.get("audio", ""),
                                "text": chunk.get("text", ""),
                                "chunk_index": chunk.get("chunk_index", 0),
                                "total_chunks": chunk.get("total_chunks", 1)
                            })
                        elif chunk["type"] == "complete":
                            await websocket.send_json({
                                "type": "complete",
                                "response": chunk.get("text", "")
                            })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": result.get("error", "Processing failed")
                    })
            
            elif message.get("type") == "interrupt":
                await voice_engine.interrupt_call(user_id)
                await websocket.send_json({"type": "interrupt_ack"})
            
            elif message.get("type") == "end":
                await voice_engine.end_call(user_id)
                break
                
    except WebSocketDisconnect:
        await voice_engine.end_call(user_id)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
        await voice_engine.end_call(user_id)


class VoiceConfig:
    AVAILABLE_VOICES = ["Aoede", "Puck", "Charon", "Ernie", "Fenrir"]
    DEFAULT_VOICE = "Aoede"
    SUPPORTED_LANGUAGES = ["en", "bn"]


@router.get("/voices")
async def get_available_voices():
    return {
        "voices": VoiceConfig.AVAILABLE_VOICES,
        "default": VoiceConfig.DEFAULT_VOICE
    }


@router.get("/languages")
async def get_supported_languages():
    return {"languages": VoiceConfig.SUPPORTED_LANGUAGES}