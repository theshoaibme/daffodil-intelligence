import asyncio
import base64
import json
from typing import Optional, Dict
from enum import Enum


class Platform(Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    WEB = "web"


class VoiceMessage:
    def __init__(self, platform: Platform, user_id: str, audio_data: Optional[bytes] = None):
        self.platform = platform
        self.user_id = user_id
        self.audio_data = audio_data
        self.transcript: Optional[str] = None
        self.response: Optional[str] = None
        self.audio_response: Optional[bytes] = None


class MessagingVoiceHandler:
    def __init__(self):
        self.active_voice_sessions: Dict[str, dict] = {}
        self.user_platforms: Dict[str, Platform] = {}
    
    async def handle_voice_message(self, message: VoiceMessage) -> dict:
        user_key = f"{message.platform.value}:{message.user_id}"
        
        if message.audio_data:
            transcript = await self.stt_convert(message.audio_data)
            message.transcript = transcript
        else:
            return {"error": "No audio data provided"}
        
        response = await self.process_with_ai(message.transcript)
        message.response = response
        
        audio_response = await self.tts_convert(response)
        message.audio_response = audio_response
        
        return {
            "transcript": transcript,
            "response": response,
            "audio": base64.b64encode(audio_response).decode() if audio_response else None
        }
    
    async def stt_convert(self, audio: bytes) -> str:
        await asyncio.sleep(0.2)
        return "Speech converted to text"
    
    async def tts_convert(self, text: str) -> bytes:
        await asyncio.sleep(0.2)
        return b"audio_data"
    
    async def process_with_ai(self, text: str) -> str:
        await asyncio.sleep(0.1)
        return f"AI response to: {text[:50]}..."
    
    def start_voice_session(self, user_key: str, platform: Platform):
        self.active_voice_sessions[user_key] = {
            "platform": platform,
            "state": "active",
            "messages": []
        }
        self.user_platforms[user_key] = platform
    
    def end_voice_session(self, user_key: str):
        if user_key in self.active_voice_sessions:
            del self.active_voice_sessions[user_key]
        if user_key in self.user_platforms:
            del self.user_platforms[user_key]
    
    def is_in_voice_session(self, user_key: str) -> bool:
        return user_key in self.active_voice_sessions


voice_handler = MessagingVoiceHandler()