import asyncio
import base64
import json
import re
from typing import Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import httpx
from ..core.config import get_settings


class VoiceState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    CONNECTED = "connected"
    INTERRUPTED = "interrupted"


@dataclass
class VoiceCallSession:
    session_id: str
    user_id: int
    state: VoiceState
    language: str = "en"
    voice_model: str = "Charon"
    interrupted: bool = False


class RealtimeVoiceEngine:
    def __init__(self):
        self.sessions: dict[str, VoiceCallSession] = {}
        self.active_calls: dict[int, str] = {}
        
    async def start_call(self, user_id: int, language: str = "en", voice_model: str = "Charon") -> dict:
        session_id = f"call_{user_id}_{asyncio.get_event_loop().time()}"
        session = VoiceCallSession(
            session_id=session_id,
            user_id=user_id,
            state=VoiceState.CONNECTED,
            language=language,
            voice_model=voice_model
        )
        self.sessions[session_id] = session
        self.active_calls[user_id] = session_id
        
        return {
            "session_id": session_id,
            "status": "connected",
            "voice_model": voice_model,
            "language": language
        }
    
    async def end_call(self, user_id: int) -> dict:
        if user_id in self.active_calls:
            session_id = self.active_calls[user_id]
            if session_id in self.sessions:
                del self.sessions[session_id]
            del self.active_calls[user_id]
            return {"status": "ended", "session_id": session_id}
        return {"status": "no_active_call"}
    
    async def interrupt_call(self, user_id: int) -> dict:
        if user_id in self.active_calls:
            session_id = self.active_calls[user_id]
            if session_id in self.sessions:
                self.sessions[session_id].interrupted = True
                self.sessions[session_id].state = VoiceState.INTERRUPTED
            return {"status": "interrupted"}
        return {"status": "no_active_call"}
    
    def check_interrupted(self, user_id: int) -> bool:
        if user_id in self.active_calls:
            session_id = self.active_calls[user_id]
            if session_id in self.sessions:
                if self.sessions[session_id].interrupted:
                    self.sessions[session_id].interrupted = False
                    self.sessions[session_id].state = VoiceState.PROCESSING
                    return True
        return False
    
    async def process_audio_chunk(self, user_id: int, audio_data: str) -> dict:
        if user_id not in self.active_calls:
            return {"error": "No active call"}
        
        session = self.sessions[self.active_calls[user_id]]
        session.state = VoiceState.PROCESSING
        session.interrupted = False
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            transcript = await self.speech_to_text(audio_bytes)
            
            if not transcript:
                return {"status": "no_speech_detected"}
            
            response = await self.generate_response(transcript)
            
            session.state = VoiceState.SPEAKING
            
            return {
                "transcript": transcript,
                "response": response,
                "state": "success"
            }
            
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}
    
    async def process_text_message(self, user_id: int, text: str) -> dict:
        if user_id not in self.active_calls:
            return {"error": "No active call"}
        
        session = self.sessions[self.active_calls[user_id]]
        session.state = VoiceState.PROCESSING
        session.interrupted = False
        
        try:
            response = await self.generate_response(text, session.language)
            
            session.state = VoiceState.SPEAKING
            
            return {
                "response": response,
                "state": "success"
            }
            
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}
    
    async def stream_text_to_speech(self, text: str, user_id: int) -> AsyncGenerator[dict, None]:
        if user_id not in self.active_calls:
            return
        
        session = self.sessions[self.active_calls[user_id]]
        settings = get_settings()
        
        ssml_text = self.add_ssml_prosody(text, session.language)
        sentences = self.split_sentences_with_ssml(ssml_text)
        
        for i, sentence in enumerate(sentences):
            if self.check_interrupted(user_id):
                yield {"type": "interrupted", "text": ""}
                return
            
            clean_text = self.strip_ssml(sentence)
            if not clean_text.strip():
                continue
            
            audio = await self.text_to_speech_ssml(f"<speak>{sentence}</speak>", session.language)
            
            yield {
                "type": "audio_chunk",
                "audio": audio,
                "text": clean_text,
                "chunk_index": i,
                "total_chunks": len(sentences)
            }
            
            await asyncio.sleep(0.05)
        
        yield {"type": "complete", "text": text}
    
    def add_ssml_prosody(self, text: str, language: str) -> str:
        text = self.preprocess_for_speech(text)
        
        if language.startswith("bn"):
            patterns = [
                (r'\b(হ্যাঁ|অবশ্যই|ঠিক আছে)\b', r'<prosody rate="105%">\1</prosody>'),
                (r'\b(তবে|কিন্তু|তবে|মাঝে মাঝে)\b', '<break time="100ms"/>'),
                (r'\b(মনে রেখো|মনে করো|গুরুত্বপূর্ণ)\b', '<prosody pitch="+3%"><emphasis level="moderate">\1</emphasis></prosody>'),
                (r'\b(কি|কিভাবে|কেন|কখন|কোথায়)\b', '<prosody pitch="+2%">\1</prosody>'),
            ]
        else:
            patterns = [
                (r'\b(okay|ok|sure|right|yes|yeah)\b', r'<prosody rate="105%">\1</prosody>'),
                (r'\b(but|however|although|well)\b', '<break time="100ms"/>'),
                (r'\b(important|remember|note that|key)\b', '<prosody pitch="+3%"><emphasis level="moderate">\1</emphasis></prosody>'),
                (r'\b(what|how|why|when|where|who)\b', '<prosody pitch="+2%">\1</prosody>'),
            ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def split_sentences_with_ssml(self, text: str) -> list:
        sentence_pattern = r'[^.!?]+[.!?]+'
        sentences = re.findall(sentence_pattern, text)
        
        if not sentences:
            return [text] if text.strip() else []
        
        return [s.strip() for s in sentences if s.strip()]
    
    def preprocess_for_speech(self, text: str) -> str:
        text = text.replace('&', 'and').replace('<', '').replace('>', '')
        text = re.sub(r'\s+', ' ', text).strip()
        
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        return text
    
    def strip_ssml(self, ssml_text: str) -> str:
        text = re.sub(r'<[^>]+>', '', ssml_text)
        return text.strip()
    
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
    
    async def text_to_speech_ssml(self, ssml: str, language: str = "en-US") -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return base64.b64encode(b"mock_audio_" + ssml.encode()).decode()
        
        lang_code = language
        if language == "bn-BD":
            lang_code = "bn-BD"
        elif language.startswith("bn"):
            lang_code = "bn-BD"
        elif language == "en-US":
            lang_code = "en-US"
        else:
            lang_code = "en-US"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={settings.GEMINI_API_KEY}",
                    json={
                        "input": {"ssml": ssml},
                        "voice": {
                            "languageCode": lang_code,
                            "name": settings.GEMINI_VOICE
                        },
                        "audioConfig": {
                            "audioEncoding": "MP3",
                            "sampleRateHertz": 24000,
                            "speakingRate": 1.1,
                            "pitch": 0,
                            "volumeGainDb": 0
                        }
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("audioContent", "")
        except Exception as e:
            pass
        return ""
    
    async def text_to_speech(self, text: str) -> str:
        return await self.text_to_speech_ssml(text, "en-US")
    
    async def generate_response(self, text: str, language: str = None) -> str:
        from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response, detect_language
        if language is None:
            language = detect_language(text)
        agents = detect_intent(text)
        results = await process_with_agents(text, agents)
        return await synthesize_response(results, text, language)
    
    def get_session(self, user_id: int) -> Optional[VoiceCallSession]:
        if user_id in self.active_calls:
            return self.sessions.get(self.active_calls[user_id])
        return None


voice_engine = RealtimeVoiceEngine()