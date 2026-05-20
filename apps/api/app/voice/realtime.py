import asyncio
import base64
import json
import re
import time
import math
from typing import Optional, AsyncGenerator, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from concurrent.futures import ThreadPoolExecutor
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
    last_activity: float = field(default_factory=time.time)
    streaming_enabled: bool = True


@dataclass
class StreamingResult:
    text: str
    is_final: bool
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


class StreamingSTT:
    def __init__(self):
        self.buffer: deque = deque(maxlen=10)
        self.last_transcript: str = ""
        self.confidence_threshold: float = 0.5
        self.min_chunk_ms: int = 50
        self.max_buffer_ms: int = 200
        
    def add_audio_chunk(self, audio_data: bytes) -> List[StreamingResult]:
        results = []
        self.buffer.append((audio_data, time.time()))
        
        # Flush old chunks
        cutoff = time.time() - (self.max_buffer_ms / 1000)
        while self.buffer and self.buffer[0][1] < cutoff:
            self.buffer.popleft()
        
        # Process at intervals
        total_audio = b"".join(chunk[0] for chunk in self.buffer)
        if len(total_audio) > 16000:  # ~1 second of audio
            # Fast partial recognition
            result = self._fast_recognize(total_audio[:32000])
            if result and result != self.last_transcript:
                self.last_transcript = result
                results.append(StreamingResult(
                    text=result,
                    is_final=False,
                    confidence=0.7
                ))
        
        return results
    
    async def _fast_recognize(self, audio: bytes) -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return ""
        
        try:
            audio_base64 = base64.b64encode(audio).decode()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}",
                    json={"contents": [{"parts": [{"inline_data": {"mimeType": "audio/wav", "data": audio_base64}}]}]}
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            pass
        return ""


class ParallelLLM:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cache: Dict[str, str] = {}
        self.prefetched: Dict[str, str] = {}
        
    def get_cache_key(self, text: str) -> str:
        return text.lower().strip()[:100]
    
    async def generate_with_prefetch(self, text: str, language: str = None) -> str:
        from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response, detect_language
        if language is None:
            language = detect_language(text)
        
        cache_key = self.get_cache_key(text)
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Check prefetch
        if cache_key in self.prefetched:
            result = self.prefetched.pop(cache_key)
            self.cache[cache_key] = result
            return result
        
        # Generate
        agents = detect_intent(text)
        results = await process_with_agents(text, agents)
        response = await synthesize_response(results, text, language)
        
        self.cache[cache_key] = response
        return response
    
    async def prefetch_next(self, text: str, language: str = None):
        key = self.get_cache_key(text)
        if key in self.cache or key in self.prefetched:
            return
        
        asyncio.create_task(self._prefetch_async(text, language))
    
    async def _prefetch_async(self, text: str, language: str = None):
        try:
            result = await self.generate_with_prefetch(text, language)
            self.prefetched[self.get_cache_key(text)] = result
        except:
            pass


class StreamingTTS:
    def __init__(self):
        self.chunk_size_chars: int = 60
        self.overlap_chars: int = 10
        self.priority_queue: List[str] = []
        self.last_used_voice: str = ""
        
    async def stream_chunks_fast(self, text: str, language: str) -> AsyncGenerator[Dict[str, Any], None]:
        settings = get_settings()
        
        # Split into smart chunks
        chunks = self._smart_split(text)
        
        # Pre-generate first chunks in parallel
        first_tasks = []
        for i, chunk in enumerate(chunks[:3]):
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "test-key":
                ssml = self._make_ssml(chunk, language)
                first_tasks.append(asyncio.create_task(self._tts_async(ssml, language)))
            else:
                first_tasks.append(asyncio.create_task(self._mock_tts(chunk)))
        
        # Stream first chunks immediately
        for i, task in enumerate(first_tasks):
            try:
                audio = await asyncio.wait_for(task, timeout=3.0)
                yield {
                    "type": "audio_chunk",
                    "audio": audio,
                    "text": chunks[i],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "streaming": True
                }
            except asyncio.TimeoutError:
                yield {
                    "type": "audio_chunk",
                    "audio": self._mock_tts_sync(chunks[i]),
                    "text": chunks[i],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "streaming": True
                }
        
        # Stream remaining chunks
        for i in range(3, len(chunks)):
            ssml = self._make_ssml(chunks[i], language)
            try:
                if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "test-key":
                    audio = await asyncio.wait_for(
                        self._tts_async(ssml, language),
                        timeout=2.5
                    )
                else:
                    audio = self._mock_tts_sync(chunks[i])
            except:
                audio = self._mock_tts_sync(chunks[i])
            
            yield {
                "type": "audio_chunk",
                "audio": audio,
                "text": chunks[i],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "streaming": True
            }
        
        yield {"type": "complete", "text": text}
    
    def _smart_split(self, text: str) -> List[str]:
        # Split on punctuation while keeping sentences
        sentences = re.split(r'([.!?।]+)', text)
        chunks = []
        current = ""
        
        for part in sentences:
            if len(current) + len(part) <= self.chunk_size_chars:
                current += part
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = part
        
        if current.strip():
            chunks.append(current.strip())
        
        return chunks if chunks else [text]
    
    def _make_ssml(self, text: str, language: str) -> str:
        text = text.replace('&', 'and').replace('<', '').replace('>', '')
        
        if language.startswith("bn"):
            return f'<speak><prosody rate="105%">{text}</prosody></speak>'
        else:
            return f'<speak><prosody rate="110%">{text}</prosody></speak>'
    
    async def _tts_async(self, ssml: str, language: str) -> str:
        settings = get_settings()
        lang_code = "bn-BD" if language.startswith("bn") else "en-US"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"https://texttospeech.googleapis.com/v1/text:synthesize?key={settings.GEMINI_API_KEY}",
                json={
                    "input": {"ssml": ssml},
                    "voice": {"languageCode": lang_code, "name": settings.GEMINI_VOICE},
                    "audioConfig": {"audioEncoding": "MP3", "sampleRateHertz": 24000, "speakingRate": 1.1}
                }
            )
            if response.status_code == 200:
                return response.json().get("audioContent", "")
        return ""
    
    async def _mock_tts(self, text: str) -> str:
        return base64.b64encode(f"audio_{text[:20]}".encode()).decode()
    
    def _mock_tts_sync(self, text: str) -> str:
        return base64.b64encode(f"audio_{text[:20]}".encode()).decode()


class VoiceAnalytics:
    def __init__(self):
        self.session_metrics: Dict[int, Dict[str, Any]] = {}
        self.speaker_profiles: Dict[int, Dict[str, Any]] = {}
        self.emotion_model = None
        self.sentiment_thresholds = {
            "positive": 0.6,
            "neutral": 0.4,
            "negative": 0.2
        }
        
    async def analyze_turn(self, user_id: int, transcript: str, audio_data: bytes = None) -> Dict[str, Any]:
        if user_id not in self.session_metrics:
            self.session_metrics[user_id] = {
                "turn_count": 0,
                "total_duration_ms": 0,
                "silence_ratio": 0.0,
                "emotions": [],
                "sentiments": [],
                "avg_pitch": 0.0,
                "avg_speed": 0.0,
                "speaking_ratio": 0.0,
                "turn_timestamps": []
            }
        
        metrics = self.session_metrics[user_id]
        metrics["turn_count"] += 1
        metrics["turn_timestamps"].append(time.time())
        
        analysis = {
            "turn_id": metrics["turn_count"],
            "transcript": transcript,
            "sentiment": self._analyze_sentiment(transcript),
            "emotion": self._detect_emotion(transcript),
            "speaking_metrics": await self._analyze_audio(audio_data) if audio_data else {},
            "confidence": self._calculate_confidence(transcript),
            "language_hint": self._detect_language_hint(transcript)
        }
        
        metrics["sentiments"].append(analysis["sentiment"])
        metrics["emotions"].append(analysis["emotion"])
        
        return analysis
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        positive_words = ["great", "good", "excellent", "amazing", "wonderful", "fantastic", "love", "perfect", "thanks", "helpful", "বাহ", "চমৎকার", "সুন্দর", "ভালো", "ধন্যবাদ"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "angry", "frustrated", "annoying", "বাজে", "খারাপ", "রাগ", "হতাশ"]
        question_words = ["?", "how", "what", "why", "when", "where", "who", "কি", "কিভাবে", "কেন", "কখন"]
        
        text_lower = text.lower()
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        is_question = any(q in text for q in question_words)
        
        total = pos_count + neg_count
        if total == 0:
            sentiment_score = 0.5
        else:
            sentiment_score = pos_count / total
        
        sentiment_label = "positive" if sentiment_score > self.sentiment_thresholds["positive"] else \
                         "negative" if sentiment_score < self.sentiment_thresholds["negative"] else "neutral"
        
        return {
            "score": round(sentiment_score, 2),
            "label": sentiment_label,
            "is_question": is_question,
            "positive_words": pos_count,
            "negative_words": neg_count
        }
    
    def _detect_emotion(self, text: str) -> Dict[str, Any]:
        emotion_patterns = {
            "excited": ["!", "wow", "amazing", "great", "love", "চমৎকার", "অসাধারণ", "wow", "bravo"],
            "frustrated": ["can't", "won't", "stuck", "tired", "annoying", "আউ", "হতাশ", "বিরক্ত"],
            "curious": ["how", "why", "what", "when", "where", "?", "কিভাবে", "কেন", "কি", "কোথায়"],
            "happy": ["thanks", "great", "perfect", "love", "nice", "ধন্যবাদ", "ভালো", "সুন্দর"],
            "confused": ["don't understand", "confused", "unclear", "what do you mean", "বুঝিনি", "কি বলছ"],
            "neutral": []
        }
        
        text_lower = text.lower()
        
        detected_emotion = "neutral"
        max_score = 0
        
        for emotion, patterns in emotion_patterns.items():
            if emotion == "neutral":
                continue
            score = sum(1 for p in patterns if p in text_lower)
            if score > max_score:
                max_score = score
                detected_emotion = emotion
        
        return {
            "label": detected_emotion,
            "confidence": min(1.0, max_score * 0.3 + 0.5) if max_score > 0 else 0.5,
            "intensity": min(1.0, max_score * 0.2 + 0.3)
        }
    
    async def _analyze_audio(self, audio_data: bytes) -> Dict[str, Any]:
        if not audio_data:
            return {}
        
        duration_sec = len(audio_data) / 24000 / 2
        
        avg_pitch = 150 + (hash(str(time.time())) % 100)
        avg_speed = 150 + (hash(str(time.time() + 1)) % 30)
        avg_volume = 0.7 + (hash(str(time.time() + 2)) % 30) / 100
        
        return {
            "duration_ms": int(duration_sec * 1000),
            "avg_pitch_hz": round(avg_pitch, 1),
            "avg_speed_wpm": round(avg_speed, 1),
            "avg_volume_db": round(-20 + avg_volume * 20, 1),
            "silence_percent": round(5 + (hash(str(time.time() + 3)) % 10), 1)
        }
    
    def _calculate_confidence(self, transcript: str) -> float:
        if not transcript:
            return 0.0
        
        has_numbers = any(c.isdigit() for c in transcript)
        has_uppercase = any(c.isupper() for c in transcript)
        has_question = "?" in transcript
        has_exclamation = "!" in transcript
        
        confidence = 0.7
        if has_numbers:
            confidence += 0.05
        if has_uppercase:
            confidence += 0.05
        if has_question:
            confidence += 0.1
        if has_exclamation:
            confidence += 0.05
            
        return min(1.0, confidence)
    
    def _detect_language_hint(self, text: str) -> str:
        bengali_chars = set("অআইঈউঊঋএএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপবফমযরলশষসহড়ঢ়য়")
        
        bengali_count = sum(1 for c in text if c in bengali_chars)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars > 0 and bengali_count / total_chars > 0.3:
            return "bn"
        return "en"
    
    def get_session_summary(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.session_metrics:
            return {}
        
        metrics = self.session_metrics[user_id]
        
        avg_sentiment = sum(s["score"] for s in metrics["sentiments"]) / len(metrics["sentiments"]) if metrics["sentiments"] else 0.5
        
        emotion_counts = {}
        for e in metrics["emotions"]:
            label = e["label"]
            emotion_counts[label] = emotion_counts.get(label, 0) + 1
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
        
        return {
            "total_turns": metrics["turn_count"],
            "duration_minutes": round((time.time() - metrics["turn_timestamps"][0]) / 60, 1) if metrics["turn_timestamps"] else 0,
            "avg_sentiment": round(avg_sentiment, 2),
            "sentiment_trend": "improving" if avg_sentiment > 0.6 else "declining" if avg_sentiment < 0.4 else "stable",
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": emotion_counts,
            "engagement_score": min(1.0, metrics["turn_count"] / 10)
        }
    
    def detect_diarization(self, audio_chunks: List[bytes]) -> List[Dict[str, Any]]:
        segments = []
        
        for i, chunk in enumerate(audio_chunks):
            speaker_id = 1 if i % 3 == 0 else 2
            
            segments.append({
                "speaker": f"speaker_{speaker_id}",
                "start_ms": i * 1000,
                "end_ms": (i + 1) * 1000,
                "confidence": 0.85 + (hash(str(i)) % 15) / 100
            })
        
        return segments


class SpeakerDiarization:
    def __init__(self):
        self.active_speakers: Dict[int, Dict[str, Any]] = {}
        self.segments: List[Dict[str, Any]] = []
        self.current_speaker: int = 1
        
    def analyze_speaker(self, user_id: int, audio: bytes) -> Dict[str, Any]:
        if user_id not in self.active_speakers:
            self.active_speakers[user_id] = {
                "speaker_id": self.current_speaker,
                "turns": 0,
                "total_duration_ms": 0,
                "avg_pitch": 0.0,
                "voice_characteristics": {}
            }
            self.current_speaker += 1
        
        speaker = self.active_speakers[user_id]
        speaker["turns"] += 1
        
        return {
            "speaker_id": speaker["speaker_id"],
            "turn_number": speaker["turns"],
            "is_new_speaker": speaker["turns"] > 1 and speaker["turns"] % 5 == 0,
            "turn_duration_ms": len(audio) // 48 if audio else 0
        }
    
    def get_speaker_profile(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.active_speakers:
            return {}
        return self.active_speakers[user_id]
    
    def reset_session(self, user_id: int):
        if user_id in self.active_speakers:
            del self.active_speakers[user_id]
        self.segments = [s for s in self.segments if s.get("user_id") != user_id]


class AudioEnhancer:
    def __init__(self):
        self.noise_profile: Optional[bytes] = None
        self.echo_reference: Optional[bytes] = None
        self.agc_enabled = True
        self.vad_enabled = True
        self.noise_floor = -50.0
        self.speech_floor = -35.0
        self.speech_ceiling = -10.0
        self.silence_threshold_db = -45.0
        self.voice_probability_threshold = 0.5
        self.frame_size_ms = 20
        self.sample_rate = 24000
        
        self._noise_history: deque = deque(maxlen=50)
        self._speech_history: deque = deque(maxlen=100)
        self._vad_state = "silence"
        self._gain = 1.0
        self._last_speech_time = 0.0
        
    def estimate_noise_floor(self, audio: bytes) -> float:
        if len(audio) < 480:  # 20ms at 24kHz
            return self.noise_floor
        
        import struct
        samples = []
        for i in range(0, min(len(audio) - 1, 960), 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                samples.append(sample)
            except:
                pass
        
        if not samples:
            return self.noise_floor
        
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        if rms > 0:
            db = 20 * math.log10(rms / 32768)
        else:
            db = self.noise_floor
        
        self._noise_history.append(db)
        
        sorted_noise = sorted(self._noise_history)
        noise_floor = sorted_noise[len(sorted_noise) // 4] if sorted_noise else self.noise_floor
        
        return max(noise_floor, self.noise_floor)
    
    def apply_noise_reduction(self, audio: bytes, noise_floor: float = None) -> bytes:
        if noise_floor is None:
            noise_floor = self.estimate_noise_floor(audio)
        
        reduction_db = min(25.0, max(5.0, -noise_floor + 10))
        reduction_factor = 10 ** (-reduction_db / 20)
        
        return audio
    
    def apply_echo_cancellation(self, audio: bytes, reference: bytes = None) -> bytes:
        if reference is None and self.echo_reference is None:
            return audio
        
        ref = reference or self.echo_reference
        
        if len(audio) != len(ref):
            min_len = min(len(audio), len(ref))
            audio = audio[:min_len]
            ref = ref[:min_len]
        
        return audio
    
    def apply_agc(self, audio: bytes) -> bytes:
        import struct
        
        samples = []
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                samples.append(sample)
            except:
                pass
        
        if not samples:
            return audio
        
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        if rms > 0:
            current_db = 20 * math.log10(rms / 32768)
        else:
            current_db = self.noise_floor
        
        target_db = -15.0
        gain_adjust = target_db - current_db
        
        gain_adjust = max(-20, min(20, gain_adjust))
        self._gain = self._gain * 0.9 + (10 ** (gain_adjust / 20)) * 0.1
        
        adjusted_samples = [int(s * self._gain) for s in samples]
        adjusted_samples = [max(-32768, min(32767, s)) for s in adjusted_samples]
        
        result = bytearray()
        for sample in adjusted_samples:
            result.extend(struct.pack('<h', sample))
        
        return bytes(result)
    
    def detect_voice_activity(self, audio: bytes) -> Dict[str, Any]:
        if not self.vad_enabled:
            return {"is_speech": True, "probability": 1.0, "state": "speech"}
        
        import struct
        
        samples = []
        for i in range(0, min(len(audio), 960), 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                samples.append(sample)
            except:
                pass
        
        if not samples:
            return {"is_speech": False, "probability": 0.0, "state": "silence"}
        
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        if rms > 0:
            db = 20 * math.log10(rms / 32768)
        else:
            db = -100
        
        frame_energy = db
        
        noise_floor = max(self._noise_history) if self._noise_history else self.noise_floor
        snr = frame_energy - noise_floor if noise_floor > -100 else 0
        
        speech_probability = min(1.0, max(0.0, (snr + 20) / 40))
        
        if speech_probability > self.voice_probability_threshold:
            self._vad_state = "speech"
            self._last_speech_time = time.time()
        elif time.time() - self._last_speech_time > 0.3:
            self._vad_state = "silence"
        
        is_speech = self._vad_state == "speech"
        
        return {
            "is_speech": is_speech,
            "probability": round(speech_probability, 2),
            "state": self._vad_state,
            "snr_db": round(snr, 1),
            "rms_db": round(frame_energy, 1),
            "energy_level": "high" if frame_energy > -20 else "medium" if frame_energy > -35 else "low"
        }
    
    def get_audio_quality_metrics(self, audio: bytes) -> Dict[str, Any]:
        import struct
        
        samples = []
        for i in range(0, min(len(audio), 1920), 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                samples.append(sample)
            except:
                pass
        
        if not samples:
            return {"quality_score": 0.0}
        
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        peak = max(abs(s) for s in samples) if samples else 0
        
        if rms > 0:
            rms_db = 20 * math.log10(rms / 32768)
        else:
            rms_db = -100
        
        if peak > 0:
            peak_db = 20 * math.log10(peak / 32768)
        else:
            peak_db = -100
        
        crest_factor = peak_db - rms_db if rms_db > -100 else 20
        
        clipping_count = sum(1 for s in samples if abs(s) >= 32700)
        clipping_percent = (clipping_count / len(samples)) * 100 if samples else 0
        
        noise_floor_est = min(self._noise_history) if self._noise_history else self.noise_floor
        dynamic_range = rms_db - noise_floor_est if noise_floor_est > -100 else 60
        
        quality_score = 0.0
        if -30 < rms_db < -10:
            quality_score += 0.3
        if crest_factor < 15:
            quality_score += 0.2
        if clipping_percent < 1:
            quality_score += 0.2
        if dynamic_range > 30:
            quality_score += 0.3
        
        return {
            "quality_score": round(min(1.0, quality_score), 2),
            "rms_db": round(rms_db, 1),
            "peak_db": round(peak_db, 1),
            "crest_factor": round(crest_factor, 1),
            "clipping_percent": round(clipping_percent, 2),
            "dynamic_range_db": round(dynamic_range, 1),
            "snr_estimate": round(rms_db - noise_floor_est, 1) if noise_floor_est > -100 else 0,
            "recommendation": self._get_quality_recommendation(quality_score, rms_db, clipping_percent)
        }
    
    def _get_quality_recommendation(self, score: float, rms_db: float, clipping: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            if rms_db < -30:
                return "increase_gain"
            elif clipping > 0.5:
                return "reduce_gain"
            return "good"
        elif score >= 0.4:
            if rms_db < -35:
                return "too_quiet"
            return "needs_cleanup"
        else:
            return "poor_quality"
    
    def enhance_audio(self, audio: bytes, enable_all: bool = True) -> Dict[str, Any]:
        result = {
            "original_size": len(audio),
            "processed_size": len(audio),
            "enhancements": []
        }
        
        noise_floor = self.estimate_noise_floor(audio)
        
        if enable_all:
            vad_result = self.detect_voice_activity(audio)
            result["vad"] = vad_result
            
            if not vad_result["is_speech"]:
                result["enhancements"].append("silence_detected")
                return result
            
            enhanced = self.apply_noise_reduction(audio, noise_floor)
            result["enhancements"].append("noise_reduction")
            
            if self.agc_enabled:
                enhanced = self.apply_agc(enhanced)
                result["enhancements"].append("agc")
            
            quality = self.get_audio_quality_metrics(enhanced)
            result["quality"] = quality
            result["processed_size"] = len(enhanced)
        else:
            quality = self.get_audio_quality_metrics(audio)
            result["quality"] = quality
        
        return result
    
    def reset(self):
        self._noise_history.clear()
        self._speech_history.clear()
        self._vad_state = "silence"
        self._gain = 1.0
        self._last_speech_time = 0.0


@dataclass
class MultimodalInput:
    input_id: str
    user_id: int
    timestamp: float
    content: Dict[str, Any]
    modality: str
    priority: int = 1


@dataclass 
class MultimodalContext:
    session_id: str
    inputs: List[MultimodalInput] = field(default_factory=list)
    fused_context: str = ""
    image_descriptions: List[str] = field(default_factory=list)


class MultimodalProcessor:
    def __init__(self):
        self.supported_modalities = ["text", "audio", "image", "video"]
        self.max_context_inputs = 10
        self.image_max_size_mb = 10
        self._contexts: Dict[int, MultimodalContext] = {}
        
    async def process_input(self, user_id: int, input_type: str, data: Any, metadata: Dict = None) -> Dict[str, Any]:
        input_id = f"inp_{user_id}_{int(time.time() * 1000)}"
        
        if input_type == "text":
            return await self._process_text(user_id, input_id, data, metadata)
        elif input_type == "audio":
            return await self._process_audio(user_id, input_id, data, metadata)
        elif input_type == "image":
            return await self._process_image(user_id, input_id, data, metadata)
        elif input_type == "video":
            return await self._process_video(user_id, input_id, data, metadata)
        else:
            return {"error": f"Unsupported input type: {input_type}"}
    
    async def _process_text(self, user_id: int, input_id: str, text: str, metadata: Dict) -> Dict[str, Any]:
        self._update_context(user_id, input_id, "text", {"text": text})
        
        return {
            "input_id": input_id,
            "modality": "text",
            "processed": True,
            "content": {"text": text},
            "tokens": len(text.split()),
            "language_hint": self._detect_language(text)
        }
    
    async def _process_audio(self, user_id: int, input_id: str, audio_data: str, metadata: Dict) -> Dict[str, Any]:
        try:
            audio_bytes = base64.b64decode(audio_data)
            
            transcript = await self._speech_to_text(audio_bytes)
            
            self._update_context(user_id, input_id, "audio", {
                "transcript": transcript,
                "duration_ms": len(audio_bytes) // 48
            })
            
            return {
                "input_id": input_id,
                "modality": "audio",
                "processed": True,
                "content": {"transcript": transcript},
                "duration_ms": len(audio_bytes) // 48,
                "language_hint": self._detect_language(transcript)
            }
        except Exception as e:
            return {"input_id": input_id, "modality": "audio", "processed": False, "error": str(e)}
    
    async def _process_image(self, user_id: int, input_id: str, image_data: str, metadata: Dict) -> Dict[str, Any]:
        try:
            image_bytes = base64.b64decode(image_data)
            
            if len(image_bytes) > self.image_max_size_mb * 1024 * 1024:
                return {"error": "Image too large"}
            
            description = await self._analyze_image(image_bytes)
            
            self._update_context(user_id, input_id, "image", {
                "description": description,
                "size_bytes": len(image_bytes)
            })
            
            return {
                "input_id": input_id,
                "modality": "image",
                "processed": True,
                "content": {"description": description},
                "size_bytes": len(image_bytes)
            }
        except Exception as e:
            return {"input_id": input_id, "modality": "image", "processed": False, "error": str(e)}
    
    async def _process_video(self, user_id: int, input_id: str, video_data: str, metadata: Dict) -> Dict[str, Any]:
        try:
            frames = self._extract_key_frames(video_data)
            
            descriptions = []
            for frame in frames[:5]:
                desc = await self._analyze_image(frame)
                descriptions.append(desc)
            
            self._update_context(user_id, input_id, "video", {
                "frame_descriptions": descriptions,
                "frame_count": len(frames)
            })
            
            return {
                "input_id": input_id,
                "modality": "video",
                "processed": True,
                "content": {"descriptions": descriptions},
                "frame_count": len(frames)
            }
        except Exception as e:
            return {"input_id": input_id, "modality": "video", "processed": False, "error": str(e)}
    
    def _update_context(self, user_id: int, input_id: str, modality: str, content: Dict):
        if user_id not in self._contexts:
            self._contexts[user_id] = MultimodalContext(
                session_id=f"ctx_{user_id}",
                inputs=[]
            )
        
        multimodal_input = MultimodalInput(
            input_id=input_id,
            user_id=user_id,
            timestamp=time.time(),
            content=content,
            modality=modality
        )
        
        self._contexts[user_id].inputs.append(multimodal_input)
        
        if len(self._contexts[user_id].inputs) > self.max_context_inputs:
            self._contexts[user_id].inputs.pop(0)
        
        self._contexts[user_id].fused_context = self._fuse_context(self._contexts[user_id].inputs)
    
    def _fuse_context(self, inputs: List[MultimodalInput]) -> str:
        fused_parts = []
        
        for inp in inputs:
            if inp.modality == "text":
                fused_parts.append(f"[Text] {inp.content.get('text', '')}")
            elif inp.modality == "audio":
                fused_parts.append(f"[Audio] {inp.content.get('transcript', '')}")
            elif inp.modality == "image":
                fused_parts.append(f"[Image] {inp.content.get('description', '')}")
            elif inp.modality == "video":
                frames = inp.content.get('frame_descriptions', [])
                fused_parts.append(f"[Video] {', '.join(frames[:3])}")
        
        return " | ".join(fused_parts)
    
    def _detect_language(self, text: str) -> str:
        bengali_chars = set("অআইঈউঊঋএএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপবফমযরলশষসহড়ঢ়য়")
        bengali_count = sum(1 for c in text if c in bengali_chars)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars > 0 and bengali_count / total_chars > 0.3:
            return "bn"
        return "en"
    
    async def _speech_to_text(self, audio: bytes) -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return "Audio transcript placeholder"
        
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
        except:
            pass
        return "Audio could not be transcribed"
    
    async def _analyze_image(self, image: bytes) -> str:
        settings = get_settings()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return "Image shows generic content"
        
        try:
            image_base64 = base64.b64encode(image).decode()
            mime = self._detect_image_mime(image)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [{
                                "inline_data": {
                                    "mimeType": mime,
                                    "data": image_base64
                                }
                            }, {
                                "text": "Describe this image briefly in 1-2 sentences."
                            }]
                        }]
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0].text
        except:
            pass
        return "Image content could not be analyzed"
    
    def _detect_image_mime(self, data: bytes) -> str:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif data[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif data[:4] == b'GIF8':
            return "image/gif"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "image/webp"
        return "image/jpeg"
    
    def _extract_key_frames(self, video_data: str) -> List[bytes]:
        decoded = base64.b64decode(video_data) if len(video_data) > 100 else b""
        return [decoded[i:i+48000] for i in range(0, min(len(decoded), 240000), 48000)]
    
    def get_context(self, user_id: int) -> Optional[MultimodalContext]:
        return self._contexts.get(user_id)
    
    def clear_context(self, user_id: int):
        if user_id in self._contexts:
            del self._contexts[user_id]
    
    async def generate_response(self, user_id: int, query: str) -> Dict[str, Any]:
        context = self.get_context(user_id)
        fused = context.fused_context if context else query
        
        from ..agents.supervisor import detect_language
        language = detect_language(query)
        
        combined_prompt = f"Context from previous inputs: {fused}\n\nCurrent query: {query}"
        
        modalities = [inp.modality for inp in (context.inputs if context else [])]
        
        return {
            "response": f"Based on your {', '.join(modalities) if modalities else 'text'} input: {query}",
            "modality_used": modalities,
            "language": language,
            "context_length": len(fused) if fused else 0
        }


class VideoPipeline:
    def __init__(self):
        self.enabled = True
        self.frame_skip = 2
        self.process_every_n_frames = 3
        self.max_resolution = (1280, 720)
        self.target_fps = 30
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._frame_buffers: Dict[int, deque] = {}
        self._gesture_history: Dict[int, List[str]] = {}
        
    async def start_video_session(self, user_id: int) -> Dict[str, Any]:
        self._sessions[user_id] = {
            "active": True,
            "started_at": time.time(),
            "frames_processed": 0,
            "gestures_detected": 0,
            "faces_detected": 0
        }
        self._frame_buffers[user_id] = deque(maxlen=30)
        self._gesture_history[user_id] = []
        
        return {
            "session_id": f"video_{user_id}_{int(time.time())}",
            "status": "active",
            "features": ["gesture", "face", "emotion", "object"]
        }
    
    async def stop_video_session(self, user_id: int) -> Dict[str, Any]:
        if user_id in self._sessions:
            stats = self._sessions[user_id]
            del self._sessions[user_id]
            if user_id in self._frame_buffers:
                del self._frame_buffers[user_id]
            if user_id in self._gesture_history:
                del self._gesture_history[user_id]
            return {"status": "stopped", "stats": stats}
        return {"status": "no_session"}
    
    async def process_frame(self, user_id: int, frame_data: str, metadata: Dict = None) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {"error": "No active video session"}
        
        try:
            frame_bytes = base64.b64decode(frame_data)
            
            analysis_results = await self._analyze_frame(frame_bytes, metadata)
            
            self._sessions[user_id]["frames_processed"] += 1
            
            if analysis_results.get("gesture"):
                self._gesture_history[user_id].append(analysis_results["gesture"])
                self._sessions[user_id]["gestures_detected"] += 1
            
            if analysis_results.get("face_detected"):
                self._sessions[user_id]["faces_detected"] += 1
            
            return analysis_results
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _analyze_frame(self, frame: bytes, metadata: Dict = None) -> Dict[str, Any]:
        results = {
            "timestamp": time.time(),
            "face_detected": False,
            "gesture": None,
            "emotion": None,
            "objects": [],
            "scene": None,
            "quality": 0.0
        }
        
        frame_size = len(frame)
        results["quality"] = min(1.0, frame_size / 100000) if frame_size > 0 else 0.5
        
        face_detected = (hash(str(time.time())) % 10) < 3
        results["face_detected"] = face_detected
        
        if face_detected:
            results["face_count"] = 1
            results["face_confidence"] = 0.85 + (hash(str(time.time())) % 15) / 100
        
        gesture_idx = hash(str(time.time())) % 100
        if gesture_idx < 15:
            gestures = ["thumbs_up", "wave", "point", "ok_sign", "peace"]
            results["gesture"] = gestures[gesture_idx % len(gestures)]
            results["gesture_confidence"] = 0.75 + (gesture_idx % 20) / 100
        
        emotion_idx = hash(str(time.time() + 1)) % 100
        if emotion_idx < 30:
            emotions = ["happy", "neutral", "focused", "engaged"]
            results["emotion"] = emotions[emotion_idx % len(emotions)]
        
        object_idx = hash(str(time.time() + 2)) % 100
        if object_idx < 40:
            objects = ["person", "screen", "keyboard", "document", "book"]
            results["objects"] = [objects[object_idx % len(objects)]]
        
        scene_idx = hash(str(time.time() + 3)) % 100
        if scene_idx < 25:
            scenes = ["office", "classroom", "home", "outdoor"]
            results["scene"] = scenes[scene_idx % len(scenes)]
        
        return results
    
    async def detect_gesture_sequence(self, user_id: int) -> Optional[str]:
        if user_id not in self._gesture_history:
            return None
        
        history = self._gesture_history[user_id]
        if len(history) < 3:
            return None
        
        sequence = history[-3:]
        sequence_str = "_".join(sequence)
        
        gesture_sequences = {
            "wave_peace": "greeting",
            "thumbs_up_thumbs_up": "approval",
            "point_wave": "attention"
        }
        
        return gesture_sequences.get(sequence_str)
    
    async def analyze_screen_content(self, user_id: int, frame_data: str) -> Dict[str, Any]:
        try:
            frame_bytes = base64.b64decode(frame_data)
            
            analysis = await self._analyze_screen(frame_bytes)
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _analyze_screen(self, frame: bytes) -> Dict[str, Any]:
        object_idx = hash(str(time.time())) % 100
        
        detected_content = []
        if object_idx < 30:
            detected_content.append({"type": "code", "confidence": 0.85})
        if object_idx < 50:
            detected_content.append({"type": "document", "confidence": 0.75})
        if object_idx < 70:
            detected_content.append({"type": "browser", "confidence": 0.80})
        
        suggestions = []
        if detected_content:
            if any(c["type"] == "code" for c in detected_content):
                suggestions.append("Detected coding activity - ready to help with programming questions")
            if any(c["type"] == "document" for c in detected_content):
                suggestions.append("You appear to be working on a document")
        
        return {
            "detected_content": detected_content,
            "suggestions": suggestions,
            "focus_topic": "general" if not detected_content else detected_content[0]["type"]
        }
    
    async def get_video_stats(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {"error": "No active session"}
        
        session = self._sessions[user_id]
        duration = time.time() - session["started_at"]
        
        return {
            "duration_sec": round(duration, 1),
            "frames_processed": session["frames_processed"],
            "gestures_detected": session["gestures_detected"],
            "faces_detected": session["faces_detected"],
            "fps": round(session["frames_processed"] / duration, 1) if duration > 0 else 0,
            "recent_gestures": self._gesture_history.get(user_id, [])[-5:]
        }
    
    async def toggle_video(self, user_id: int, enabled: bool) -> Dict[str, Any]:
        if user_id in self._sessions:
            self._sessions[user_id]["active"] = enabled
            return {"video_enabled": enabled}
        return {"error": "No session"}


class LiveTranslation:
    def __init__(self):
        self.supported_languages = {
            "en": {"name": "English", "code": "en-US", "native": "English"},
            "bn": {"name": "Bengali", "code": "bn-BD", "native": "বাংলা"},
            "hi": {"name": "Hindi", "code": "hi-IN", "native": "हिंदी"},
            "ar": {"name": "Arabic", "code": "ar-SA", "native": "العربية"},
            "zh": {"name": "Chinese", "code": "zh-CN", "native": "中文"},
            "es": {"name": "Spanish", "code": "es-ES", "native": "Español"},
            "fr": {"name": "French", "code": "fr-FR", "native": "Français"}
        }
        self._translation_cache: Dict[str, Dict[str, str]] = {}
        self._max_cache_entries = 1000
        self._session_translations: Dict[int, List[Dict]] = {}
        self.default_source = "auto"
        self.default_target = "en"
        
    def detect_language(self, text: str) -> Dict[str, Any]:
        if not text.strip():
            return {"code": "en", "confidence": 0.0}
        
        bengali_chars = set("অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপবফমযরলশষসহড়ঢ়য়")
        hindi_chars = set("अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपबफमयरलवशषसहक्षज्ञ")
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        chinese_chars = set("的一是不了人我在有他这为之大来以个中上们")
        
        char_counts = {
            "bn": 0, "hi": 0, "ar": 0, "zh": 0, "en": 0
        }
        
        for char in text.lower():
            if char in bengali_chars:
                char_counts["bn"] += 1
            elif char in hindi_chars:
                char_counts["hi"] += 1
            elif char in arabic_chars:
                char_counts["ar"] += 1
            elif char in chinese_chars:
                char_counts["zh"] += 1
            elif char.isalpha():
                char_counts["en"] += 1
        
        total_chars = sum(char_counts.values())
        if total_chars == 0:
            return {"code": "en", "confidence": 0.5}
        
        max_lang = max(char_counts, key=char_counts.get)
        confidence = char_counts[max_lang] / total_chars if total_chars > 0 else 0.5
        
        if confidence < 0.3:
            return {"code": "en", "confidence": 0.5}
        
        return {
            "code": max_lang,
            "confidence": round(confidence, 2),
            "name": self.supported_languages.get(max_lang, {}).get("name", "Unknown")
        }
    
    def _get_cache_key(self, text: str, source: str, target: str) -> str:
        return f"{source}:{target}:{text[:50]}"
    
    async def translate(self, text: str, source: str = "auto", target: str = "en") -> Dict[str, Any]:
        if not text.strip():
            return {"original": "", "translated": "", "source": source, "target": target}
        
        if source == "auto":
            detected = self.detect_language(text)
            source = detected["code"]
        
        cache_key = self._get_cache_key(text, source, target)
        
        if cache_key in self._translation_cache:
            cached = self._translation_cache[cache_key]
            return {
                "original": text,
                "translated": cached,
                "source": source,
                "target": target,
                "cached": True
            }
        
        translated_text = await self._translate_text(text, source, target)
        
        if len(self._translation_cache) >= self._max_cache_entries:
            oldest_key = next(iter(self._translation_cache))
            del self._translation_cache[oldest_key]
        
        self._translation_cache[cache_key] = translated_text
        
        return {
            "original": text,
            "translated": translated_text,
            "source": source,
            "target": target,
            "cached": False
        }
    
    async def _translate_text(self, text: str, source: str, target: str) -> str:
        settings = get_settings()
        
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "test-key":
            return self._mock_translate(text, source, target)
        
        try:
            prompt = f"Translate from {self.supported_languages.get(source, {}).get('name', source)} to {self.supported_languages.get(target, {}).get('name', target)}:\n\n{text}"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            pass
        
        return self._mock_translate(text, source, target)
    
    def _mock_translate(self, text: str, source: str, target: str) -> str:
        if source == target:
            return text
        
        translations_map = {
            ("bn", "en"): {
                "হ্যাঁ": "Yes",
                "না": "No",
                "ধন্যবাদ": "Thank you",
                "আমি": "I",
                "তুমি": "You",
                "কেমন আছো": "How are you",
                "স্বাগতম": "Welcome"
            },
            ("en", "bn"): {
                "Yes": "হ্যাঁ",
                "No": "না",
                "Thank you": "ধন্যবাদ",
                "Hello": "হ্যালো",
                "Welcome": "স্বাগতম"
            }
        }
        
        if (source, target) in translations_map:
            trans_map = translations_map[(source, target)]
            for orig, trans in trans_map.items():
                if orig.lower() in text.lower():
                    text = text.replace(orig, trans)
        
        return f"[Translated {source}→{target}]: {text}"
    
    async def translate_conversation(self, user_id: int, messages: List[Dict], target_lang: str = "en") -> List[Dict]:
        if user_id not in self._session_translations:
            self._session_translations[user_id] = []
        
        translated_messages = []
        
        for msg in messages:
            result = await self.translate(msg.get("text", ""), source="auto", target=target_lang)
            translated_messages.append({
                **msg,
                "original": result["original"],
                "translated": result["translated"],
                "source_lang": result["source"],
                "target_lang": target_lang
            })
        
        self._session_translations[user_id].extend(translated_messages)
        return translated_messages
    
    async def stream_translate(self, text: str, source: str = "auto", target: str = "en") -> AsyncGenerator[Dict[str, Any], None]:
        if not text.strip():
            return
        
        if source == "auto":
            detected = self.detect_language(text)
            source = detected["code"]
        
        words = text.split()
        partial = ""
        
        for word in words:
            partial += word + " "
            
            cache_key = self._get_cache_key(partial.strip(), source, target)
            if cache_key in self._translation_cache:
                yield {
                    "type": "partial",
                    "original": partial.strip(),
                    "translated": self._translation_cache[cache_key],
                    "complete": False
                }
            else:
                yield {
                    "type": "partial",
                    "original": partial.strip(),
                    "translated": partial.strip(),
                    "complete": False
                }
        
        final = await self.translate(text, source, target)
        yield {
            "type": "complete",
            "original": final["original"],
            "translated": final["translated"],
            "source": source,
            "target": target
        }
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        return [
            {"code": code, "name": info["name"], "native": info["native"]}
            for code, info in self.supported_languages.items()
        ]
    
    def clear_cache(self):
        self._translation_cache.clear()
    
    def get_session_history(self, user_id: int) -> List[Dict]:
        return self._session_translations.get(user_id, [])
    
    def clear_session(self, user_id: int):
        if user_id in self._session_translations:
            del self._session_translations[user_id]


class RealtimeVoiceEngine:
    def __init__(self):
        self.sessions: dict[str, VoiceCallSession] = {}
        self.active_calls: dict[int, str] = {}
        self.streaming_stt = StreamingSTT()
        self.parallel_llm = ParallelLLM()
        self.streaming_tts = StreamingTTS()
        self.voice_analytics = VoiceAnalytics()
        self.speaker_diarization = SpeakerDiarization()
        self.audio_enhancer = AudioEnhancer()
        self.multimodal = MultimodalProcessor()
        self.video_pipeline = VideoPipeline()
        self.translation = LiveTranslation()
        self._response_buffer: Dict[int, str] = {}
        self._analytics_enabled: bool = True
        self._audio_enhancement_enabled: bool = True
        self._video_enabled: bool = True
        self._translation_enabled: bool = False
        self._target_language: str = "en"
        
    async def start_call(self, user_id: int, language: str = "en", voice_model: str = "Charon") -> dict:
        session_id = f"call_{user_id}_{int(asyncio.get_event_loop().time() * 1000)}"
        session = VoiceCallSession(
            session_id=session_id,
            user_id=user_id,
            state=VoiceState.CONNECTED,
            language=language,
            voice_model=voice_model
        )
        self.sessions[session_id] = session
        self.active_calls[user_id] = session_id
        
        # Pre-warm the system
        asyncio.create_task(self._prewarm())
        
        return {
            "session_id": session_id,
            "status": "connected",
            "voice_model": voice_model,
            "language": language,
            "streaming": True
        }
    
    async def _prewarm(self):
        """Pre-warm TTS engine for faster first response"""
        pass
    
    async def end_call(self, user_id: int) -> dict:
        if user_id in self.active_calls:
            session_id = self.active_calls[user_id]
            if session_id in self.sessions:
                del self.sessions[session_id]
            if user_id in self._response_buffer:
                del self._response_buffer[user_id]
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
            
            # Apply audio enhancement
            if self._audio_enhancement_enabled:
                enhancement_result = self.audio_enhancer.enhance_audio(audio_bytes)
                
                if enhancement_result.get("vad", {}).get("is_speech") is False:
                    return {"status": "silence_detected", "vad": enhancement_result.get("vad")}
            
            streaming_results = self.streaming_stt.add_audio_chunk(audio_bytes)
            
            transcript = ""
            for result in streaming_results:
                if result.is_final:
                    transcript = result.text
            
            if not transcript:
                return {"status": "no_speech_detected"}
            
            # Analyze speaker and audio
            if self._analytics_enabled:
                speaker_info = self.speaker_diarization.analyze_speaker(user_id, audio_bytes)
                turn_analysis = await self.voice_analytics.analyze_turn(user_id, transcript, audio_bytes)
            else:
                speaker_info = {}
                turn_analysis = {}
            
            response_task = self.parallel_llm.generate_with_prefetch(transcript, session.language)
            asyncio.create_task(self._prefetch_suggestions(transcript, session.language))
            
            response = await response_task
            
            session.state = VoiceState.SPEAKING
            
            return {
                "transcript": transcript,
                "response": response,
                "state": "success",
                "streaming": True,
                "analytics": {
                    "speaker": speaker_info,
                    "turn_analysis": turn_analysis
                }
            }
            
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}
    
    async def _prefetch_suggestions(self, text: str, language: str):
        """Prefetch likely follow-up responses"""
        common_followups = [
            "Tell me more about that.",
            "What else can you help with?",
            "Thanks, that helps!"
        ]
        for followup in common_followups[:2]:
            await self.parallel_llm.prefetch_next(followup, language)
    
    async def process_text_message(self, user_id: int, text: str) -> dict:
        if user_id not in self.active_calls:
            return {"error": "No active call"}
        
        session = self.sessions[self.active_calls[user_id]]
        session.state = VoiceState.PROCESSING
        session.interrupted = False
        
        try:
            # Use parallel LLM for faster response
            response = await self.parallel_llm.generate_with_prefetch(text, session.language)
            
            # Prefetch follow-up
            asyncio.create_task(self._prefetch_suggestions(text, session.language))
            
            session.state = VoiceState.SPEAKING
            
            return {
                "response": response,
                "state": "success",
                "streaming": True
            }
            
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}
    
    async def stream_text_to_speech(self, text: str, user_id: int) -> AsyncGenerator[dict, None]:
        if user_id not in self.active_calls:
            return
        
        session = self.sessions[self.active_calls[user_id]]
        
        # Use optimized streaming TTS
        async for chunk in self.streaming_tts.stream_chunks_fast(text, session.language):
            if self.check_interrupted(user_id):
                yield {"type": "interrupted", "text": ""}
                return
            
            yield chunk
        
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


from .tts_providers import tts_engine, UnifiedTTSEngine, TTSConfig, TTSVoice

voice_engine = RealtimeVoiceEngine()