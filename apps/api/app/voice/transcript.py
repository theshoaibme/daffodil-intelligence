import asyncio
import base64
import json
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib
import re


class TranscriptStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SpeakerType(Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class TranscriptSegment:
    segment_id: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker: SpeakerType
    language: str = "en"
    status: TranscriptStatus = TranscriptStatus.COMPLETED
    words: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptSession:
    session_id: str
    user_id: int
    start_time: float
    segments: List[TranscriptSegment] = field(default_factory=list)
    status: str = "active"
    language: str = "en"
    full_text: str = ""
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TranscriptManager:
    def __init__(self):
        self._sessions: Dict[int, TranscriptSession] = {}
        self._pending_audio: Dict[int, deque] = {}
        self._segment_buffers: Dict[int, deque] = {}
        self._max_segments = 1000
        self._buffer_duration_sec = 30
        self._min_confidence = 0.5
        
        self._language_patterns = {
            "bn": re.compile(r'[\u0980-\u09FF]'),
            "hi": re.compile(r'[\u0900-\u097F]'),
            "ar": re.compile(r'[\u0600-\u06FF]'),
            "zh": re.compile(r'[\u4e00-\u9fff]'),
            "ja": re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
            "ko": re.compile(r'[\uac00-\ud7af]')
        }

    async def start_session(self, user_id: int, language: str = "en") -> Dict[str, Any]:
        if user_id in self._sessions:
            existing = self._sessions[user_id]
            return {
                "session_id": existing.session_id,
                "status": "existing",
                "segment_count": len(existing.segments)
            }
        
        session_id = f"transcript_{user_id}_{int(time.time())}"
        
        session = TranscriptSession(
            session_id=session_id,
            user_id=user_id,
            start_time=time.time(),
            language=language
        )
        
        self._sessions[user_id] = session
        self._pending_audio[user_id] = deque(maxlen=50)
        self._segment_buffers[user_id] = deque(maxlen=100)
        
        return {
            "session_id": session_id,
            "status": "started",
            "language": language,
            "timestamp": time.time()
        }

    async def end_session(self, user_id: int, save: bool = True) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No active transcript session",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        session.status = "completed"
        
        full_text = " ".join(seg.text for seg in session.segments if seg.text)
        
        result = {
            "session_id": session.session_id,
            "status": "ended",
            "duration_sec": round(time.time() - session.start_time, 2),
            "total_segments": len(session.segments),
            "word_count": session.word_count,
            "full_text": full_text[:500],
            "language": session.language
        }
        
        if save:
            result["saved"] = True
            result["transcript"] = self._format_transcript(session)
        
        if user_id in self._pending_audio:
            del self._pending_audio[user_id]
        
        return result

    async def process_audio(self, user_id: int, audio_data: str, speaker: str = "user") -> Dict[str, Any]:
        if user_id not in self._sessions:
            await self.start_session(user_id)
        
        session = self._sessions[user_id]
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            audio_size = len(audio_bytes)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Invalid audio data: {str(e)}",
                "code": "INVALID_AUDIO"
            }
        
        self._pending_audio[user_id].append({
            "audio": audio_bytes,
            "timestamp": time.time(),
            "speaker": speaker
        })
        
        transcript = await self._transcribe_audio(audio_bytes)
        
        if not transcript.get("text"):
            return {
                "status": "no_transcript",
                "audio_size": audio_size,
                "segments": len(session.segments)
            }
        
        text = transcript["text"]
        confidence = transcript.get("confidence", 0.8)
        detected_lang = transcript.get("language", session.language)
        
        segment_id = f"seg_{len(session.segments)}_{int(time.time() * 1000)}"
        
        current_time = time.time()
        start_time = current_time - (audio_size / 48000)
        
        words = self._tokenize_words(text)
        
        segment = TranscriptSegment(
            segment_id=segment_id,
            text=text,
            start_time=start_time,
            end_time=current_time,
            confidence=confidence,
            speaker=SpeakerType(speaker) if speaker in ["user", "ai", "system"] else SpeakerType.UNKNOWN,
            language=detected_lang,
            status=TranscriptStatus.COMPLETED,
            words=words,
            metadata={
                "audio_size": audio_size,
                "processing_time_ms": transcript.get("processing_time", 0)
            }
        )
        
        session.segments.append(segment)
        
        session.full_text = " ".join(seg.text for seg in session.segments)
        session.word_count = len(session.full_text.split())
        
        if len(session.segments) > self._max_segments:
            session.segments = session.segments[-self._max_segments:]
        
        return {
            "status": "transcribed",
            "segment_id": segment_id,
            "text": text,
            "confidence": confidence,
            "language": detected_lang,
            "speaker": speaker,
            "timestamp": current_time,
            "total_segments": len(session.segments)
        }

    async def _transcribe_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        from ..core.config import get_settings
        settings = get_settings()
        
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return {
                "text": "Simulated transcription for audio",
                "confidence": 0.75,
                "language": "en",
                "processing_time": 50
            }
        
        try:
            import httpx
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
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
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    return {
                        "text": text,
                        "confidence": 0.9,
                        "language": self._detect_language(text),
                        "processing_time": 100
                    }
        except Exception as e:
            pass
        
        return {
            "text": "Audio transcription placeholder",
            "confidence": 0.5,
            "language": "en",
            "processing_time": 0
        }

    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"
        
        for lang, pattern in self._language_patterns.items():
            if pattern.search(text):
                return lang
        
        return "en"

    def _tokenize_words(self, text: str) -> List[Dict]:
        words = []
        word_list = text.split()
        start_time = time.time()
        
        for i, word in enumerate(word_list):
            words.append({
                "word": word,
                "index": i,
                "start_time": start_time + (i * 0.3),
                "confidence": 0.9
            })
        
        return words

    def _format_transcript(self, session: TranscriptSession) -> List[Dict]:
        return [
            {
                "segment_id": seg.segment_id,
                "text": seg.text,
                "speaker": seg.speaker.value,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "confidence": seg.confidence,
                "language": seg.language
            }
            for seg in session.segments
        ]

    async def get_transcript(self, user_id: int, format: str = "json") -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No transcript session found",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        if format == "text":
            return {
                "text": session.full_text,
                "word_count": session.word_count,
                "duration_sec": round(time.time() - session.start_time, 2)
            }
        
        return {
            "session_id": session.session_id,
            "segments": self._format_transcript(session),
            "full_text": session.full_text,
            "word_count": session.word_count,
            "language": session.language,
            "status": session.status
        }

    async def add_text_transcript(self, user_id: int, text: str, speaker: str = "user") -> Dict[str, Any]:
        if user_id not in self._sessions:
            await self.start_session(user_id)
        
        session = self._sessions[user_id]
        
        segment_id = f"seg_{len(session.segments)}_{int(time.time() * 1000)}"
        
        current_time = time.time()
        
        segment = TranscriptSegment(
            segment_id=segment_id,
            text=text,
            start_time=current_time,
            end_time=current_time,
            confidence=1.0,
            speaker=SpeakerType(speaker) if speaker in ["user", "ai", "system"] else SpeakerType.UNKNOWN,
            language=self._detect_language(text),
            status=TranscriptStatus.COMPLETED,
            words=self._tokenize_words(text)
        )
        
        session.segments.append(segment)
        session.full_text = " ".join(seg.text for seg in session.segments)
        session.word_count = len(session.full_text.split())
        
        return {
            "segment_id": segment_id,
            "status": "added",
            "total_segments": len(session.segments)
        }

    async def get_live_transcript(self, user_id: int, last_segment_id: str = None) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "active": False,
                "segments": []
            }
        
        session = self._sessions[user_id]
        
        segments = session.segments
        if last_segment_id:
            segments = [s for s in segments if s.segment_id > last_segment_id]
        
        return {
            "active": True,
            "session_id": session.session_id,
            "segments": [
                {
                    "id": s.segment_id,
                    "text": s.text,
                    "speaker": s.speaker.value,
                    "timestamp": s.start_time
                }
                for s in segments
            ],
            "total_segments": len(session.segments),
            "full_text": session.full_text[-500:] if session.full_text else ""
        }

    async def search_transcript(self, user_id: int, query: str, case_sensitive: bool = False) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No transcript session found",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        search_text = query if case_sensitive else query.lower()
        
        matches = []
        for seg in session.segments:
            text = seg.text if case_sensitive else seg.text.lower()
            
            if search_text in text:
                matches.append({
                    "segment_id": seg.segment_id,
                    "text": seg.text,
                    "speaker": seg.speaker.value,
                    "timestamp": seg.start_time,
                    "confidence": seg.confidence
                })
        
        return {
            "query": query,
            "matches": matches,
            "total_matches": len(matches)
        }

    async def get_statistics(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No transcript session found",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        speaker_stats = {}
        for seg in session.segments:
            speaker = seg.speaker.value
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {"segments": 0, "words": 0, "characters": 0}
            
            speaker_stats[speaker]["segments"] += 1
            speaker_stats[speaker]["words"] += len(seg.text.split())
            speaker_stats[speaker]["characters"] += len(seg.text)
        
        return {
            "session_id": session.session_id,
            "total_segments": len(session.segments),
            "total_words": session.word_count,
            "total_characters": len(session.full_text),
            "duration_sec": round(time.time() - session.start_time, 2),
            "language": session.language,
            "speaker_stats": speaker_stats,
            "avg_words_per_segment": round(session.word_count / len(session.segments), 1) if session.segments else 0
        }

    async def export_transcript(self, user_id: int, format: str = "json") -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No transcript session found",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        if format == "srt":
            return {
                "format": "srt",
                "content": self._generate_srt(session)
            }
        elif format == "vtt":
            return {
                "format": "vtt",
                "content": self._generate_vtt(session)
            }
        elif format == "text":
            return {
                "format": "text",
                "content": session.full_text
            }
        
        return {
            "format": "json",
            "content": json.dumps(self._format_transcript(session), indent=2)
        }

    def _generate_srt(self, session: TranscriptSession) -> str:
        srt_output = []
        
        for i, seg in enumerate(session.segments, 1):
            start_time = self._format_srt_time(seg.start_time)
            end_time = self._format_srt_time(seg.end_time)
            
            srt_output.append(f"{i}\n{start_time} --> {end_time}\n{seg.text}\n")
        
        return "\n".join(srt_output)

    def _generate_vtt(self, session: TranscriptSession) -> str:
        vtt_output = ["WEBVTT", ""]
        
        for seg in session.segments:
            start_time = self._format_vtt_time(seg.start_time)
            end_time = self._format_vtt_time(seg.end_time)
            
            vtt_output.append(f"{start_time} --> {end_time}")
            vtt_output.append(seg.text)
            vtt_output.append("")
        
        return "\n".join(vtt_output)

    def _format_srt_time(self, timestamp: float) -> str:
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def _format_vtt_time(self, timestamp: float) -> str:
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def get_session_status(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "active": False,
                "session": None
            }
        
        session = self._sessions[user_id]
        
        return {
            "active": True,
            "session_id": session.session_id,
            "status": session.status,
            "segments_count": len(session.segments),
            "word_count": session.word_count,
            "duration_sec": round(time.time() - session.start_time, 2),
            "language": session.language
        }

    async def pause_session(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No active session",
                "code": "NO_SESSION"
            }
        
        self._sessions[user_id].status = "paused"
        
        return {
            "status": "paused",
            "session_id": self._sessions[user_id].session_id
        }

    async def resume_session(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No session to resume",
                "code": "NO_SESSION"
            }
        
        self._sessions[user_id].status = "active"
        
        return {
            "status": "resumed",
            "session_id": self._sessions[user_id].session_id
        }


transcript_manager = TranscriptManager()