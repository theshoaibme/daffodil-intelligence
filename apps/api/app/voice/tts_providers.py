import asyncio
import base64
import json
import time
import subprocess
import tempfile
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import httpx


@dataclass
class TTSConfig:
    provider: str = "elevenlabs"
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    model: str = "eleven_monolingual_v1"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0


@dataclass
class TTSVoice:
    id: str
    name: str
    language: str
    gender: str
    preview_url: Optional[str] = None


@dataclass
class TTSResult:
    audio: str
    duration_ms: float
    provider: str
    voice_id: str
    cost_ms: float


class TTSProvider(ABC):
    def __init__(self, config: TTSConfig):
        self.config = config
        self.name = "base"
        
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
        pass
    
    @abstractmethod
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[TTSVoice]:
        pass
    
    def preprocess_text(self, text: str) -> str:
        return text


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str, config: TTSConfig = None):
        super().__init__(config or TTSConfig())
        self.api_key = api_key
        self.name = "elevenlabs"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        self._voices = [
            TTSVoice("21m00Tcm4TlvDq8ikWAM", "Rachel", "en", "female"),
            TTSVoice("TX3LPaxEHKiQ53dXZ7EY", "Drew", "en", "male"),
            TTSVoice("pFZP5JQG7iTojE8U0ciG", "Sofia", "es", "female"),
            TTSVoice("VR6AewLTigWG4GxSO2mB", "Jessica", "en", "female"),
            TTSVoice("yoZ06uK1AitPLQqzFz3A", "Arnold", "en", "male"),
            TTSVoice("EXAVITQu4vr4Wm7X26U5", "Nicole", "en", "female"),
            TTSVoice("FVmS38bl09F0CkImGNFI", "Matt", "en", "male"),
            TTSVoice("ErXwO7pW2xKqVgGkSgk4", "Bella", "bn", "female"),
        ]
    
    def preprocess_text(self, text: str) -> str:
        text = text.replace('&', 'and').replace('<', '').replace('>', '')
        text = text.replace('"', "'").replace('*', '').replace('_', '')
        return text
    
    async def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
        start = time.time()
        
        text = self.preprocess_text(text)
        voice = voice_id or self.config.voice_id
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        body = {
            "text": text,
            "model_id": self.config.model,
            "voice_settings": {
                "stability": self.config.stability,
                "similarity_boost": self.config.similarity_boost,
                "style": self.config.style,
                "use_speaker_boost": True
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice}",
                    headers=headers,
                    json=body
                )
                
                if response.status_code == 200:
                    audio_b64 = base64.b64encode(response.content).decode()
                    cost = (time.time() - start) * 1000
                    
                    return TTSResult(
                        audio=audio_b64,
                        duration_ms=len(text) * 50,
                        provider=self.name,
                        voice_id=voice,
                        cost_ms=cost
                    )
        except Exception as e:
            pass
        
        return await self._fallback_synthesize(text)
    
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        text = self.preprocess_text(text)
        voice = voice_id or self.config.voice_id
        
        chunks = self._split_text(text, 100)
        
        for chunk in chunks:
            try:
                result = await self.synthesize(chunk, voice)
                if result.audio:
                    yield base64.b64decode(result.audio)
            except:
                yield b""
    
    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        sentences = text.split('.')
        chunks = []
        current = ""
        
        for sent in sentences:
            if len(current) + len(sent) < chunk_size:
                current += sent + "."
            else:
                if current:
                    chunks.append(current.strip())
                current = sent + "."
        
        if current.strip():
            chunks.append(current.strip())
        
        return chunks if chunks else [text]
    
    async def get_available_voices(self) -> List[TTSVoice]:
        if self.api_key and self.api_key != "test":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{self.base_url}/voices",
                        headers={"xi-api-key": self.api_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return [
                            TTSVoice(
                                id=v["voice_id"],
                                name=v["name"],
                                language=v.get("labels", {}).get("language", "en"),
                                gender=v.get("labels", {}).get("gender", "neutral")
                            )
                            for v in data.get("voices", [])
                        ]
            except:
                pass
        
        return self._voices
    
    async def _fallback_synthesize(self, text: str) -> TTSResult:
        return TTSResult(
            audio=base64.b64encode(f"fallback_{text[:20]}".encode()).decode(),
            duration_ms=len(text) * 50,
            provider=self.name + "_fallback",
            voice_id=self.config.voice_id,
            cost_ms=0
        )


class GoogleCloudTTSProvider(TTSProvider):
    def __init__(self, api_key: str, config: TTSConfig = None):
        super().__init__(config or TTSConfig())
        self.api_key = api_key
        self.name = "google_cloud"
        
        self._voices = [
            TTSVoice("en-US-Standard-A", "Standard A", "en-US", "male"),
            TTSVoice("en-US-Standard-B", "Standard B", "en-US", "male"),
            TTSVoice("en-US-Standard-C", "Standard C", "en-US", "female"),
            TTSVoice("en-US-Standard-D", "Standard D", "en-US", "male"),
            TTSVoice("bn-BD-Standard-A", "Standard A", "bn-BD", "female"),
            TTSVoice("hi-IN-Standard-A", "Standard A", "hi-IN", "female"),
        ]
    
    async def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
        start = time.time()
        
        text = self.preprocess_text(text)
        voice = voice_id or self.config.voice_id
        
        lang_code = voice[:5] if voice else "en-US"
        
        body = {
            "input": {"text": text},
            "voice": {
                "languageCode": lang_code,
                "name": voice,
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": self.config.speaking_rate,
                "pitch": self.config.pitch,
                "volumeGainDb": (self.config.volume - 1) * 6
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}",
                    json=body
                )
                
                if response.status_code == 200:
                    data = response.json()
                    cost = (time.time() - start) * 1000
                    
                    return TTSResult(
                        audio=data.get("audioContent", ""),
                        duration_ms=len(text) * 50,
                        provider=self.name,
                        voice_id=voice,
                        cost_ms=cost
                    )
        except:
            pass
        
        return TTSResult(
            audio=base64.b64encode(f"google_{text[:20]}".encode()).decode(),
            duration_ms=len(text) * 50,
            provider=self.name,
            voice_id=voice,
            cost_ms=(time.time() - start) * 1000
        )
    
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        result = await self.synthesize(text, voice_id)
        if result.audio:
            yield base64.b64decode(result.audio)
    
    async def get_available_voices(self) -> List[TTSVoice]:
        return self._voices


class AzureSpeechProvider(TTSProvider):
    def __init__(self, api_key: str, region: str = "eastus", config: TTSConfig = None):
        super().__init__(config or TTSConfig())
        self.api_key = api_key
        self.region = region
        self.name = "azure"
        self.subscription_key = api_key
        
        self._voices = [
            TTSVoice("en-US-JennyNeural", "Jenny", "en-US", "female"),
            TTSVoice("en-US-GuyNeural", "Guy", "en-US", "male"),
            TTSVoice("en-US-AriaNeural", "Aria", "en-US", "female"),
            TTSVoice("bn-BD-NabanitaNeural", "Nabanita", "bn-BD", "female"),
        ]
    
    async def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
        start = time.time()
        text = self.preprocess_text(text)
        voice = voice_id or self.config.voice_id
        
        return TTSResult(
            audio=base64.b64encode(f"azure_{text[:20]}".encode()).decode(),
            duration_ms=len(text) * 50,
            provider=self.name,
            voice_id=voice,
            cost_ms=(time.time() - start) * 1000
        )
    
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        result = await self.synthesize(text, voice_id)
        if result.audio:
            yield base64.b64decode(result.audio)
    
    async def get_available_voices(self) -> List[TTSVoice]:
        return self._voices


class EdgeTTSProvider(TTSProvider):
    def __init__(self, config: TTSConfig = None):
        super().__init__(config or TTSConfig())
        self.name = "edge_tts"
        self._voice_map = {
            "bn": "bn-BD-NabanitaNeural",
            "bn-BD": "bn-BD-NabanitaNeural",
            "en": "en-US-JennyNeural",
            "en-US": "en-US-JennyNeural",
            "en-GB": "en-GB-SoniaNeural",
        }
        self._voices = [
            TTSVoice("bn-BD-NabanitaNeural", "Nabanita (Bengali)", "bn-BD", "female"),
            TTSVoice("bn-BD-PradeepNeural", "Pradeep (Bengali)", "bn-BD", "male"),
            TTSVoice("en-US-JennyNeural", "Jenny (English)", "en-US", "female"),
            TTSVoice("en-US-GuyNeural", "Guy (English)", "en-US", "male"),
            TTSVoice("en-GB-SoniaNeural", "Sonia (English UK)", "en-GB", "female"),
        ]
    
    def preprocess_text(self, text: str) -> str:
        text = text.replace('।', '.').replace('!', '! ').strip()
        return text
    
    async def synthesize(self, text: str, voice_id: str = None) -> TTSResult:
        start = time.time()
        text = self.preprocess_text(text)
        
        voice = voice_id or "en-US"
        if voice in self._voice_map:
            voice = self._voice_map[voice]
        
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            mp3_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            await communicate.save(mp3_file.name)
            mp3_file.close()
            with open(mp3_file.name, 'rb') as f:
                audio_bytes = f.read()
            os.unlink(mp3_file.name)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return TTSResult(
                audio=audio_base64,
                duration_ms=len(text) * 50,
                provider=self.name,
                voice_id=voice,
                cost_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            print(f"Edge TTS error: {e}")
        return TTSResult(audio="", duration_ms=len(text) * 50, provider=self.name, voice_id=voice, cost_ms=(time.time() - start) * 1000)
    
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        try:
            import edge_tts
            voice = voice_id or "en-US"
            if voice in self._voice_map:
                voice = self._voice_map[voice]
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            print(f"Edge TTS streaming error: {e}")
            yield b""
    
    async def get_available_voices(self) -> List[TTSVoice]:
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return [
                TTSVoice(v["Name"], v["Name"], v["Locale"], v.get("Gender", "neutral"))
                for v in voices[:10]
            ]
        except:
            return self._voices


class UnifiedTTSEngine:
    def __init__(self, api_keys: Dict[str, str] = None):
        self.config = TTSConfig()
        self.api_keys = api_keys or {}
        
        self.providers: Dict[str, TTSProvider] = {
            "edge_tts": EdgeTTSProvider(self.config),
            "elevenlabs": ElevenLabsProvider(
                self.api_keys.get("elevenlabs", "test")
            ),
            "google_cloud": GoogleCloudTTSProvider(
                self.api_keys.get("google_cloud", "test")
            ),
            "azure": AzureSpeechProvider(
                self.api_keys.get("azure", "test"),
                self.api_keys.get("azure_region", "eastus")
            )
        }
        
        self.current_provider = "edge_tts"
        self._fallback_chain = ["edge_tts", "elevenlabs", "google_cloud", "azure"]
        self._usage_stats: Dict[str, Dict] = {}
    
    def set_provider(self, provider: str):
        if provider in self.providers:
            self.current_provider = provider
    
    def get_provider(self) -> TTSProvider:
        return self.providers.get(self.current_provider, self.providers["elevenlabs"])
    
    async def synthesize(self, text: str, voice_id: str = None, provider: str = None) -> TTSResult:
        if provider:
            self.set_provider(provider)
        
        prov = self.get_provider()
        
        try:
            result = await prov.synthesize(text, voice_id or self.config.voice_id)
            
            self._update_stats(prov.name, "success")
            return result
            
        except Exception as e:
            return await self._try_fallback(text, voice_id)
    
    async def _try_fallback(self, text: str, voice_id: str) -> TTSResult:
        for prov_name in self._fallback_chain:
            if prov_name == self.current_provider:
                continue
            
            prov = self.providers.get(prov_name)
            if prov:
                try:
                    result = await prov.synthesize(text, voice_id or self.config.voice_id)
                    self._update_stats(prov_name, "fallback")
                    return result
                except:
                    continue
        
        return TTSResult(
            audio=base64.b64encode(b"fallback_audio").decode(),
            duration_ms=len(text) * 50,
            provider="fallback",
            voice_id=self.config.voice_id,
            cost_ms=0
        )
    
    async def synthesize_streaming(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        prov = self.get_provider()
        
        async for chunk in prov.synthesize_streaming(text, voice_id or self.config.voice_id):
            if chunk:
                yield chunk
    
    def _update_stats(self, provider: str, status: str):
        if provider not in self._usage_stats:
            self._usage_stats[provider] = {"success": 0, "fallback": 0, "failed": 0}
        
        self._usage_stats[provider][status] = self._usage_stats[provider].get(status, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "current_provider": self.current_provider,
            "usage": self._usage_stats,
            "available_providers": list(self.providers.keys())
        }
    
    async def get_all_voices(self) -> Dict[str, List[TTSVoice]]:
        voices = {}
        for name, prov in self.providers.items():
            try:
                voices[name] = await prov.get_available_voices()
            except:
                voices[name] = []
        return voices
    
    def set_voice_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_voice_config(self) -> TTSConfig:
        return self.config


tts_engine = UnifiedTTSEngine()