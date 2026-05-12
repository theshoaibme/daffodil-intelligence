import asyncio
import base64
import json
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import httpx
from ..core.config import get_settings


class VoiceState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    CONNECTED = "connected"


@dataclass
class VoiceCallSession:
    session_id: str
    user_id: int
    state: VoiceState
    language: str = "en"
    voice_model: str = "Aoede"


class RealtimeVoiceEngine:
    def __init__(self):
        self.sessions: dict[str, VoiceCallSession] = {}
        self.active_calls: dict[int, str] = {}
        
    async def start_call(self, user_id: int) -> dict:
        session_id = f"call_{user_id}_{asyncio.get_event_loop().time()}"
        session = VoiceCallSession(
            session_id=session_id,
            user_id=user_id,
            state=VoiceState.CONNECTED
        )
        self.sessions[session_id] = session
        self.active_calls[user_id] = session_id
        
        return {
            "session_id": session_id,
            "status": "connected",
            "voice_model": session.voice_model,
            "language": session.language
        }
    
    async def end_call(self, user_id: int) -> dict:
        if user_id in self.active_calls:
            session_id = self.active_calls[user_id]
            if session_id in self.sessions:
                del self.sessions[session_id]
            del self.active_calls[user_id]
            return {"status": "ended", "session_id": session_id}
        return {"status": "no_active_call"}
    
    async def process_audio_chunk(self, user_id: int, audio_data: str) -> dict:
        if user_id not in self.active_calls:
            return {"error": "No active call"}
        
        session = self.sessions[self.active_calls[user_id]]
        session.state = VoiceState.PROCESSING
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            transcript = await self.speech_to_text(audio_bytes)
            
            if not transcript:
                return {"status": "no_speech_detected"}
            
            response = await self.generate_response(transcript)
            audio_response = await self.text_to_speech(response)
            
            session.state = VoiceState.SPEAKING
            
            return {
                "transcript": transcript,
                "response": response,
                "audio": audio_response,
                "state": "success"
            }
            
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}
    
    async def speech_to_text(self, audio: bytes) -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return "Mock transcript"
        
        try:
            audio_base64 = base64.b64encode(audio).decode()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [{
                                "inline_data": {
                                    "mimeType": "audio/wav",
                                    "data": audio_base64
                                }
                            }]
                        }]
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0].text
        except Exception as e:
            pass
        return "Could not transcribe audio"
    
    async def text_to_speech(self, text: str) -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return base64.b64encode(b"mock_audio").decode()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={settings.GEMINI_API_KEY}",
                    json={
                        "input": {"text": text},
                        "voice": {"languageCode": "en-US", "name": settings.GEMINI_VOICE},
                        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 16000}
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("audioContent", "")
        except Exception as e:
            pass
        return ""
    
    async def generate_response(self, text: str) -> str:
        from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
        agents = detect_intent(text)
        results = await process_with_agents(text, agents)
        return await synthesize_response(results, text)
    
    def get_session(self, user_id: int) -> Optional[VoiceCallSession]:
        if user_id in self.active_calls:
            return self.sessions.get(self.active_calls[user_id])
        return None


voice_engine = RealtimeVoiceEngine()