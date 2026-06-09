from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import json
import asyncio
import time
import base64

from ..core.security import get_current_user
from ..voice.tts_providers import tts_engine
from ..voice.voice_effects import voice_effects, EffectType, VoiceEffectConfig
from ..voice.personality import personality_engine, PersonalityMood, PersonalityTrait, SpeakingStyle
from ..voice.failover import failover_manager, CircuitState, ServiceStatus, RetryConfig
from ..voice.call_recorder import call_recorder, RecordingFormat
from ..voice.conversation_memory import conversation_memory, MemoryType, MemoryPriority, ConversationContext
from ..voice.agent_orchestrator import agent_orchestrator, AgentType, TaskPriority
from ..voice.real_time_analytics import real_time_analytics, MetricType, AlertLevel
from ..voice.realtime import voice_engine, VoiceState
from ..voice.microphone import microphone_manager
from ..voice.transcript import transcript_manager
from ..master_agent import master_agent

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


@router.get("/analytics/{user_id}")
async def get_session_analytics(user_id: int, user: dict = Depends(get_current_user)):
    summary = voice_engine.voice_analytics.get_session_summary(user_id)
    speaker_profile = voice_engine.speaker_diarization.get_speaker_profile(user_id)
    
    return {
        "session_summary": summary,
        "speaker_profile": speaker_profile,
        "analytics_enabled": voice_engine._analytics_enabled
    }


@router.post("/analytics/toggle")
async def toggle_analytics(enabled: bool = True, user: dict = Depends(get_current_user)):
    voice_engine._analytics_enabled = enabled
    return {"analytics_enabled": enabled}


@router.get("/analytics/emotions/{user_id}")
async def get_emotion_timeline(user_id: int, user: dict = Depends(get_current_user)):
    if user_id in voice_engine.voice_analytics.session_metrics:
        metrics = voice_engine.voice_analytics.session_metrics[user_id]
        return {
            "emotions": metrics["emotions"],
            "sentiments": metrics["sentiments"],
            "turn_count": metrics["turn_count"]
        }
    return {"emotions": [], "sentiments": [], "turn_count": 0}


@router.post("/audio/enhance/toggle")
async def toggle_audio_enhancement(enabled: bool = True, user: dict = Depends(get_current_user)):
    voice_engine._audio_enhancement_enabled = enabled
    return {"audio_enhancement_enabled": enabled}


@router.post("/audio/enhance/quality")
async def get_audio_quality(audio_data: str, user: dict = Depends(get_current_user)):
    try:
        audio_bytes = base64.b64decode(audio_data)
        metrics = voice_engine.audio_enhancer.get_audio_quality_metrics(audio_bytes)
        return metrics
    except Exception as e:
        return {"error": str(e)}


@router.post("/audio/vad")
async def detect_voice_activity(audio_data: str, user: dict = Depends(get_current_user)):
    try:
        audio_bytes = base64.b64decode(audio_data)
        result = voice_engine.audio_enhancer.detect_voice_activity(audio_bytes)
        return result
    except Exception as e:
        return {"error": str(e)}


class MultimodalRequest(BaseModel):
    input_type: str
    data: str
    metadata: Optional[Dict[str, Any]] = None


class MultimodalQueryRequest(BaseModel):
    query: str


@router.post("/multimodal/process")
async def process_multimodal_input(
    request: MultimodalRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.multimodal.process_input(
        user_id,
        request.input_type,
        request.data,
        request.metadata
    )
    return result


@router.post("/multimodal/query")
async def query_with_multimodal(
    request: MultimodalQueryRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.multimodal.generate_response(user_id, request.query)
    return result


@router.get("/multimodal/context")
async def get_multimodal_context(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    context = voice_engine.multimodal.get_context(user_id)
    if context:
        return {
            "session_id": context.session_id,
            "inputs_count": len(context.inputs),
            "fused_context": context.fused_context[:500],
            "modalities": [inp.modality for inp in context.inputs]
        }
    return {"context": None}


@router.delete("/multimodal/context")
async def clear_multimodal_context(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    voice_engine.multimodal.clear_context(user_id)
    return {"status": "cleared"}


class VideoFrameRequest(BaseModel):
    frame_data: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/video/start")
async def start_video_session(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.start_video_session(user_id)
    return result


@router.post("/video/stop")
async def stop_video_session(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.stop_video_session(user_id)
    return result


@router.post("/video/frame")
async def process_video_frame(
    request: VideoFrameRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.process_frame(
        user_id,
        request.frame_data,
        request.metadata
    )
    return result


@router.get("/video/stats")
async def get_video_stats(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.get_video_stats(user_id)
    return result


@router.post("/video/toggle")
async def toggle_video(enabled: bool = True, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.toggle_video(user_id, enabled)
    return result


@router.post("/video/screen")
async def analyze_screen(
    frame_data: str,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.video_pipeline.analyze_screen_content(user_id, frame_data)
    return result


@router.get("/video/gesture/{user_id}")
async def get_gesture_sequence(user_id: int, user: dict = Depends(get_current_user)):
    result = await voice_engine.video_pipeline.detect_gesture_sequence(user_id)
    return {"sequence": result, "detected": result is not None}


class TranslationRequest(BaseModel):
    text: str
    source: Optional[str] = "auto"
    target: Optional[str] = "en"


@router.post("/translate")
async def translate_text(
    request: TranslationRequest,
    user: dict = Depends(get_current_user)
):
    result = await voice_engine.translation.translate(
        request.text,
        request.source,
        request.target
    )
    return result


@router.post("/translate/stream")
async def stream_translate(
    request: TranslationRequest,
    user: dict = Depends(get_current_user)
):
    translations = []
    async for chunk in voice_engine.translation.stream_translate(
        request.text,
        request.source,
        request.target
    ):
        translations.append(chunk)
    return {"chunks": translations}


@router.get("/translate/languages")
async def get_translation_languages():
    return {"languages": voice_engine.translation.get_supported_languages()}


@router.post("/translate/conversation")
async def translate_conversation(
    messages: List[Dict],
    target: str = "en",
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await voice_engine.translation.translate_conversation(user_id, messages, target)
    return {"translations": result}


@router.post("/translate/toggle")
async def toggle_translation(enabled: bool = False, target: str = "en", user: dict = Depends(get_current_user)):
    voice_engine._translation_enabled = enabled
    voice_engine._target_language = target
    return {"translation_enabled": enabled, "target_language": target}


@router.get("/translate/detect")
async def detect_language(text: str):
    result = voice_engine.translation.detect_language(text)
    return result


@router.delete("/translate/cache")
async def clear_translation_cache(user: dict = Depends(get_current_user)):
    voice_engine.translation.clear_cache()
    return {"status": "cleared"}


@router.get("/translate/history")
async def get_translation_history(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    history = voice_engine.translation.get_session_history(user_id)
    return {"history": history[-50:]}


class TTSConfigRequest(BaseModel):
    provider: Optional[str] = None
    voice_id: Optional[str] = None
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style: Optional[float] = None
    speaking_rate: Optional[float] = None


class TTSSynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    provider: Optional[str] = None


@router.get("/tts/providers")
async def get_tts_providers():
    stats = tts_engine.get_stats()
    return {
        "providers": stats["available_providers"],
        "current": stats["current_provider"],
        "usage": stats["usage"]
    }


@router.get("/tts/voices")
async def get_available_voices(provider: Optional[str] = None):
    if provider:
        tts_engine.set_provider(provider)
    
    all_voices = await tts_engine.get_all_voices()
    return {"voices": all_voices}


@router.get("/tts/voices/{provider}")
async def get_provider_voices(provider: str):
    tts_engine.set_provider(provider)
    voices = await tts_engine.get_all_voices()
    return {"provider": provider, "voices": voices.get(provider, [])}


@router.post("/tts/synthesize")
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    user: dict = Depends(get_current_user)
):
    result = await tts_engine.synthesize(
        request.text,
        request.voice_id,
        request.provider
    )
    return {
        "audio": result.audio,
        "duration_ms": result.duration_ms,
        "provider": result.provider,
        "voice_id": result.voice_id,
        "cost_ms": result.cost_ms
    }


@router.post("/tts/config")
async def configure_tts(
    request: TTSConfigRequest,
    user: dict = Depends(get_current_user)
):
    if request.provider:
        tts_engine.set_provider(request.provider)
    
    if hasattr(tts_engine.config, 'stability') and request.stability is not None:
        tts_engine.config.stability = request.stability
    if request.similarity_boost is not None:
        tts_engine.config.similarity_boost = request.similarity_boost
    if request.style is not None:
        tts_engine.config.style = request.style
    if request.speaking_rate is not None:
        tts_engine.config.speaking_rate = request.speaking_rate
    if request.voice_id:
        tts_engine.config.voice_id = request.voice_id
    
    return {"config": {
        "provider": tts_engine.current_provider,
        "voice_id": tts_engine.config.voice_id,
        "stability": tts_engine.config.stability,
        "similarity_boost": tts_engine.config.similarity_boost,
        "style": tts_engine.config.style,
        "speaking_rate": tts_engine.config.speaking_rate
    }}


@router.get("/tts/stats")
async def get_tts_stats():
    return tts_engine.get_stats()


class VoiceEffectRequest(BaseModel):
    audio_data: str
    effect_type: Optional[str] = "none"
    pitch_shift: Optional[float] = 0.0
    volume_gain_db: Optional[float] = 0.0


@router.get("/effects/presets")
async def get_effect_presets():
    presets = voice_effects.get_available_presets()
    return {"presets": presets}


@router.post("/effects/preset")
async def apply_effect_preset(preset_name: str, user: dict = Depends(get_current_user)):
    preset = voice_effects.get_preset(preset_name)
    return {"preset": preset_name, "config": voice_effects.get_config()}


@router.post("/effects/apply")
async def apply_voice_effect(
    request: VoiceEffectRequest,
    user: dict = Depends(get_current_user)
):
    audio = base64.b64decode(request.audio_data)
    
    config = VoiceEffectConfig()
    config.effect_type = EffectType(request.effect_type)
    config.pitch_shift = request.pitch_shift
    config.volume_gain_db = request.volume_gain_db
    
    processed = voice_effects.apply_effect(audio, config)
    processed_b64 = base64.b64encode(processed).decode()
    
    return {
        "audio": processed_b64,
        "effect": request.effect_type,
        "size": len(processed)
    }


@router.post("/effects/config")
async def configure_effects(
    effect_type: Optional[str] = None,
    pitch_shift: Optional[float] = None,
    volume_gain_db: Optional[float] = None,
    echo_delay_ms: Optional[float] = None,
    reverb_room_size: Optional[float] = None,
    user: dict = Depends(get_current_user)
):
    kwargs = {}
    if effect_type:
        kwargs["effect_type"] = effect_type
    if pitch_shift is not None:
        kwargs["pitch_shift"] = pitch_shift
    if volume_gain_db is not None:
        kwargs["volume_gain_db"] = volume_gain_db
    if echo_delay_ms is not None:
        kwargs["echo_delay_ms"] = echo_delay_ms
    if reverb_room_size is not None:
        kwargs["reverb_room_size"] = reverb_room_size
    
    voice_effects.set_config(**kwargs)
    return voice_effects.get_config()


@router.get("/effects/status")
async def get_effects_status():
    return voice_effects.get_config()


@router.get("/effects/effects-list")
async def get_effects_list():
    return {"effects": voice_effects.get_available_effects()}


@router.get("/effects/backgrounds")
async def get_background_sounds():
    return {"sounds": voice_effects.get_background_sounds()}


@router.post("/effects/background")
async def set_background_sound(sound_id: str, user: dict = Depends(get_current_user)):
    success = voice_effects.set_background_sound(sound_id)
    if success:
        return {"status": "active", "sound": voice_effects.get_active_background()}
    return {"error": "Sound not found"}


@router.post("/effects/background/stop")
async def stop_background_sound(user: dict = Depends(get_current_user)):
    voice_effects.stop_background()
    return {"status": "stopped"}


class PersonalityRequest(BaseModel):
    preset: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[float] = None
    humor_level: Optional[float] = None
    formality_level: Optional[float] = None
    empathy_level: Optional[float] = None
    creativity_level: Optional[float] = None


@router.get("/personality/presets")
async def get_personality_presets():
    return {"presets": personality_engine.get_presets()}


@router.post("/personality/preset")
async def set_personality_preset(preset: str, user: dict = Depends(get_current_user)):
    success = personality_engine.set_preset(preset)
    if success:
        return {"status": "applied", "preset": preset, "config": personality_engine.get_current_config()}
    return {"error": "Preset not found"}


@router.post("/personality/mood")
async def set_personality_mood(mood: str, user: dict = Depends(get_current_user)):
    try:
        personality_engine.set_mood(PersonalityMood(mood))
        return {"status": "updated", "mood": mood}
    except ValueError:
        return {"error": f"Invalid mood: {mood}"}


@router.post("/personality/config")
async def configure_personality(request: PersonalityRequest, user: dict = Depends(get_current_user)):
    if request.preset:
        personality_engine.set_preset(request.preset)
    
    if request.mood:
        try:
            personality_engine.set_mood(PersonalityMood(request.mood))
        except:
            pass
    
    personality_engine.set_custom_config(
        energy_level=request.energy_level,
        humor_level=request.humor_level,
        formality_level=request.formality_level,
        empathy_level=request.empathy_level,
        creativity_level=request.creativity_level
    )
    
    return personality_engine.get_current_config()


@router.get("/personality/status")
async def get_personality_status():
    return personality_engine.get_current_config()


@router.get("/personality/greeting")
async def get_personality_greeting(language: str = "en"):
    return {"greeting": personality_engine.generate_greeting(language)}


@router.get("/personality/encouragement")
async def get_encouragement(context: str = "good_progress"):
    return {"encouragement": personality_engine.get_encouragement(context)}


@router.post("/personality/respond")
async def respond_to_emotion(emotion: str):
    return {"response": personality_engine.respond_to_emotion(emotion)}


@router.post("/personality/feedback")
async def submit_feedback(positive: bool, user: dict = Depends(get_current_user)):
    personality_engine.adjust_based_on_feedback(positive)
    return {"status": "adjusted", "new_config": personality_engine.get_current_config()}


class RetryConfigRequest(BaseModel):
    max_attempts: Optional[int] = None
    base_delay_ms: Optional[int] = None
    max_delay_ms: Optional[int] = None
    exponential_base: Optional[float] = None


@router.get("/failover/status")
async def get_failover_status():
    stats = failover_manager.get_stats()
    services = failover_manager.get_all_service_health()
    return {
        "stats": stats,
        "services": services
    }


@router.get("/failover/service/{service_name}")
async def get_service_health(service_name: str):
    return failover_manager.get_service_health(service_name)


@router.get("/failover/circuit/{service_name}")
async def get_circuit_state(service_name: str):
    state = failover_manager.get_circuit_state(service_name)
    return {
        "service": service_name,
        "state": state.value
    }


@router.post("/failover/circuit/{service_name}/reset")
async def reset_circuit(service_name: str, user: dict = Depends(get_current_user)):
    failover_manager.reset_circuit(service_name)
    return {"status": "reset", "service": service_name}


@router.post("/failover/health-check")
async def run_health_checks():
    await failover_manager.run_health_checks()
    return {"status": "completed"}


@router.get("/failover/events")
async def get_failover_events(limit: int = 20):
    events = failover_manager.get_recent_events(limit)
    return {"events": events}


@router.post("/failover/retry-config")
async def configure_retry(
    service_name: str,
    config: RetryConfigRequest,
    user: dict = Depends(get_current_user)
):
    retry_config = RetryConfig()
    if config.max_attempts is not None:
        retry_config.max_attempts = config.max_attempts
    if config.base_delay_ms is not None:
        retry_config.base_delay_ms = config.base_delay_ms
    if config.max_delay_ms is not None:
        retry_config.max_delay_ms = config.max_delay_ms
    if config.exponential_base is not None:
        retry_config.exponential_base = config.exponential_base
    
    failover_manager.set_retry_config(service_name, retry_config)
    return {"service": service_name, "config": {
        "max_attempts": retry_config.max_attempts,
        "base_delay_ms": retry_config.base_delay_ms,
        "max_delay_ms": retry_config.max_delay_ms,
        "exponential_base": retry_config.exponential_base
    }}


@router.get("/failover/retry-config/{service_name}")
async def get_retry_config(service_name: str):
    config = failover_manager.get_retry_config(service_name)
    return {
        "service": service_name,
        "config": {
            "max_attempts": config.max_attempts,
            "base_delay_ms": config.base_delay_ms,
            "max_delay_ms": config.max_delay_ms,
            "exponential_base": config.exponential_base
        }
    }


@router.get("/failover/services")
async def get_services():
    return {"services": list(failover_manager.services.keys())}


class RecordingRequest(BaseModel):
    format: Optional[str] = "wav"


@router.post("/recording/start")
async def start_recording(
    request: RecordingRequest = RecordingRequest(),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = call_recorder.start_recording(user_id, RecordingFormat(request.format))
    return result


@router.post("/recording/stop")
async def stop_recording(save: bool = True, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    result = call_recorder.stop_recording(user_id, save)
    return result


@router.post("/recording/pause")
async def pause_recording(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return call_recorder.pause_recording(user_id)


@router.post("/recording/resume")
async def resume_recording(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return call_recorder.resume_recording(user_id)


@router.post("/recording/chunk")
async def add_audio_chunk(
    audio_data: str,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    audio_bytes = base64.b64decode(audio_data)
    success = call_recorder.add_audio_chunk(user_id, audio_bytes)
    return {"added": success}


@router.post("/recording/transcript")
async def add_transcript_entry(
    text: str,
    speaker: str = "user",
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    success = call_recorder.add_transcript_entry(user_id, text, speaker, time.time())
    return {"added": success}


@router.post("/recording/sentiment")
async def add_sentiment_entry(
    sentiment: str,
    score: float,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    success = call_recorder.add_sentiment_entry(user_id, sentiment, score, time.time())
    return {"added": success}


@router.post("/recording/tag")
async def add_recording_tag(
    tag: str,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    success = call_recorder.add_tag(user_id, tag)
    return {"added": success}


@router.post("/recording/notes")
async def set_recording_notes(
    notes: str,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    success = call_recorder.set_notes(user_id, notes)
    return {"updated": success}


@router.get("/recording/status")
async def get_recording_status(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return call_recorder.get_active_recording_status(user_id) or {"status": "idle"}


@router.get("/recording/list")
async def list_recordings(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    recordings = call_recorder.list_recordings(user_id, limit)
    return {"recordings": recordings}


@router.get("/recording/{recording_id}")
async def get_recording(recording_id: str):
    return call_recorder.get_recording(recording_id) or {"error": "Not found"}


@router.get("/recording/{recording_id}/audio")
async def get_recording_audio(recording_id: str):
    audio = call_recorder.get_audio_base64(recording_id)
    if audio:
        return {"audio": audio}
    return {"error": "No audio data"}


@router.get("/recording/{recording_id}/transcript")
async def get_recording_transcript(recording_id: str):
    transcript = call_recorder.get_transcript_with_timestamps(recording_id)
    return {"transcript": transcript}


@router.post("/recording/{recording_id}/export")
async def export_recording(recording_id: str, format: str = "wav"):
    result = call_recorder.export_recording(recording_id, format)
    return result or {"error": "Export failed"}


@router.delete("/recording/{recording_id}")
async def delete_recording(recording_id: str):
    success = call_recorder.delete_recording(recording_id)
    return {"deleted": success}


@router.get("/recording/stats")
async def get_recording_stats(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return call_recorder.get_recording_stats(user_id)


@router.get("/recording/search")
async def search_recordings(query: str, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    results = call_recorder.search_transcripts(query, user_id)
    return {"results": results}


class MemoryRequest(BaseModel):
    content: str
    memory_type: Optional[str] = "short_term"
    importance: Optional[float] = 0.5
    tags: Optional[List[str]] = None


@router.post("/memory/add")
async def add_memory(
    request: MemoryRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    mem_type = MemoryType(request.memory_type) if request.memory_type else MemoryType.SHORT_TERM
    
    entry = conversation_memory.add_to_memory(
        user_id,
        request.content,
        memory_type=mem_type,
        importance=request.importance,
        tags=request.tags
    )
    
    return {
        "memory_id": entry.memory_id,
        "type": entry.memory_type.value,
        "created": True
    }


@router.get("/memory/retrieve")
async def retrieve_memories(
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 5,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    mem_type = MemoryType(memory_type) if memory_type else None
    
    memories = conversation_memory.retrieve_relevant(
        user_id,
        query,
        memory_type=mem_type,
        limit=limit
    )
    
    return {
        "memories": [
            {
                "id": m.memory_id,
                "content": m.content,
                "type": m.memory_type.value,
                "importance": m.importance_score,
                "timestamp": m.timestamp
            }
            for m in memories
        ]
    }


@router.get("/memory/context")
async def get_memory_context(
    current_message: str,
    include_short_term: bool = True,
    include_long_term: bool = True,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    context = conversation_memory.get_context_for_response(
        user_id,
        current_message,
        include_short_term,
        include_long_term
    )
    return {"context": context}


@router.post("/memory/consolidate")
async def consolidate_memories(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    count = conversation_memory.consolidate_to_long_term(user_id)
    return {"consolidated": count}


@router.post("/memory/forget")
async def forget_old_memories(max_age_seconds: float = 3600, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    count = conversation_memory.forget_old_memories(user_id, max_age_seconds)
    return {"forgotten": count}


@router.get("/memory/search")
async def search_memories(
    query: str,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    results = conversation_memory.search_memories(user_id, query, limit)
    return {"results": results}


@router.get("/memory/stats")
async def get_memory_stats(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return conversation_memory.get_memory_stats(user_id)


@router.get("/memory/recent")
async def get_recent_memories(
    turns: int = 5,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    recent = conversation_memory.get_recent_context(user_id, turns)
    return {"recent": recent}


@router.post("/memory/episode")
async def create_episode(
    session_id: str,
    messages: List[Dict],
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    context = ConversationContext(
        session_id=session_id,
        user_id=user_id,
        start_time=time.time()
    )
    for msg in messages:
        context.add_message(msg.get("role", "user"), msg.get("content", ""))
    
    episode = conversation_memory.create_episode(user_id, session_id, context)
    return {"episode": episode}


@router.get("/memory/episodes")
async def get_episodes(limit: int = 10, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    episodes = conversation_memory.get_episode_history(user_id, limit)
    return {"episodes": episodes}


@router.post("/memory/clear")
async def clear_memory(
    memory_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    
    if memory_type == "short_term":
        conversation_memory.clear_short_term(user_id)
    else:
        conversation_memory.clear_all_memory(user_id)
    
    return {"cleared": True}


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    entry = conversation_memory.get_memory_by_id(user_id, memory_id)
    
    if entry:
        return {
            "id": entry.memory_id,
            "content": entry.content,
            "type": entry.memory_type.value,
            "importance": entry.importance_score,
            "timestamp": entry.timestamp,
            "access_count": entry.access_count,
            "tags": entry.tags
        }
    return {"error": "Memory not found"}


class WorkflowExecuteRequest(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]
    user_id: Optional[int] = None


class SingleTaskRequest(BaseModel):
    task_name: str
    required_capabilities: List[str]
    input_data: Dict[str, Any]


@router.get("/orchestrator/workflows")
async def get_workflows():
    return {"workflows": agent_orchestrator.get_workflows()}


@router.get("/orchestrator/agents")
async def get_agents():
    return {"agents": agent_orchestrator.get_agents()}


@router.get("/orchestrator/stats")
async def get_orchestrator_stats():
    return agent_orchestrator.get_orchestrator_stats()


@router.post("/orchestrator/execute")
async def execute_workflow(
    request: WorkflowExecuteRequest,
    user: dict = Depends(get_current_user)
):
    user_id = request.user_id or int(user.get("sub"))
    result = await agent_orchestrator.execute_workflow(
        request.workflow_id,
        request.input_data,
        user_id
    )
    return {
        "workflow_id": result.workflow_id,
        "status": result.status,
        "tasks_completed": result.tasks_completed,
        "total_tasks": result.total_tasks,
        "duration_ms": round(result.duration_ms, 2),
        "results": result.results,
        "errors": result.errors
    }


@router.post("/orchestrator/task")
async def execute_single_task(
    request: SingleTaskRequest,
    user: dict = Depends(get_current_user)
):
    result = await agent_orchestrator.execute_single_task(
        request.task_name,
        request.required_capabilities,
        request.input_data
    )
    return result


@router.get("/orchestrator/history")
async def get_execution_history(limit: int = 10):
    history = agent_orchestrator.get_execution_history(limit)
    return {"history": history}


class AnalyticsRequest(BaseModel):
    user_id: Optional[int] = None
    level_db: Optional[float] = None
    sentiment: Optional[str] = None
    score: Optional[float] = None


@router.get("/analytics/dashboard")
async def get_dashboard_data(user_id: Optional[int] = None):
    return real_time_analytics.get_dashboard_data(user_id)


@router.get("/analytics/live/{metric_name}")
async def get_live_chart_data(metric_name: str, points: int = 50):
    return real_time_analytics.get_live_chart_data(metric_name, points)


@router.get("/analytics/timeseries/{metric_name}")
async def get_time_series(
    metric_name: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
):
    data = real_time_analytics.get_time_series_data(metric_name, start_time, end_time)
    return {
        "metric": metric_name,
        "points": [
            {"timestamp": p.timestamp, "value": p.value, "label": p.label}
            for p in data
        ]
    }


@router.get("/analytics/alerts")
async def get_recent_alerts(limit: int = 10):
    return {"alerts": real_time_analytics.get_recent_alerts(limit)}


@router.post("/analytics/audio-level")
async def record_audio_level(level_db: float, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    waveform = real_time_analytics.record_audio_level(user_id, level_db)
    return {
        "peak": waveform.peak,
        "rms": waveform.rms,
        "average": waveform.average,
        "samples": waveform.samples
    }


@router.post("/analytics/sentiment")
async def record_sentiment(
    sentiment: str,
    score: float,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    return real_time_analytics.record_sentiment(user_id, sentiment, score)


@router.post("/analytics/interaction")
async def record_interaction(
    interaction_type: str,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    return real_time_analytics.record_interaction(user_id, interaction_type)


@router.get("/analytics/session")
async def get_session_summary(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    summary = real_time_analytics.get_session_summary(user_id)
    return summary or {"status": "no_active_session"}


@router.post("/analytics/latency")
async def record_latency(component: str, latency_ms: float):
    real_time_analytics.record_latency(component, latency_ms)
    return {"recorded": True}


@router.post("/analytics/quality")
async def record_quality_score(score: float):
    real_time_analytics.record_quality_score(score)
    return {"recorded": True}


@router.get("/analytics/performance")
async def get_performance_breakdown():
    return {"performance": real_time_analytics.get_performance_breakdown()}


@router.post("/analytics/session/start")
async def start_analytics_session(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return real_time_analytics.start_session(user_id)


@router.post("/analytics/session/end")
async def end_analytics_session(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    return real_time_analytics.end_session(user_id)


@router.get("/analytics/export")
async def export_metrics(format: str = "json"):
    return real_time_analytics.export_metrics(format)


@router.post("/analytics/reset")
async def reset_analytics(user: dict = Depends(get_current_user)):
    real_time_analytics.reset_metrics()
    return {"status": "reset"}


@router.websocket("/ws/voice/{user_id}")
async def voice_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    
    session_data = await voice_engine.start_call(user_id)
    await websocket.send_json({
        "type": "connected",
        "session": session_data,
        "streaming": True
    })
    
    last_activity = time.time()
    message_queue = asyncio.Queue()
    response_task = None
    
    async def process_queue():
        nonlocal response_task
        while True:
            try:
                message = await asyncio.wait_for(message_queue.get(), timeout=0.1)
                
                if message.get("type") == "text":
                    text = message.get("data", "")
                    language = message.get("language", "en")
                    
                    # Start response generation immediately (parallel)
                    response_task = asyncio.create_task(
                        voice_engine.parallel_llm.generate_with_prefetch(text, language)
                    )
                    
                    # Send acknowledgment immediately
                    await websocket.send_json({
                        "type": "processing",
                        "text": text[:50] + "..." if len(text) > 50 else text
                    })
                    
                    # Stream TTS as soon as response is ready
                    try:
                        response = await response_task
                        
                        # Send response text first for UI update
                        await websocket.send_json({
                            "type": "response_text",
                            "text": response,
                            "streaming": True
                        })
                        
                        # Stream audio chunks
                        async for chunk in voice_engine.stream_text_to_speech(response, user_id):
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
                    except asyncio.CancelledError:
                        pass
                        
                elif message.get("type") == "audio":
                    asyncio.create_task(process_audio_message(message))
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Queue error: {e}")
                break
    
    async def process_audio_message(message):
        try:
            result = await voice_engine.process_audio_chunk(
                user_id,
                message.get("data", "")
            )
            if result.get("state") == "success":
                await websocket.send_json({
                    "type": "response_text",
                    "text": result.get("response", "")
                })
                async for chunk in voice_engine.stream_text_to_speech(result.get("response", ""), user_id):
                    if chunk["type"] == "interrupted":
                        await websocket.send_json({"type": "interrupted"})
                        break
                    elif chunk["type"] == "audio_chunk":
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "audio": chunk.get("audio", ""),
                            "text": chunk.get("text", "")
                        })
                    elif chunk["type"] == "complete":
                        await websocket.send_json({"type": "complete"})
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
    
    queue_task = asyncio.create_task(process_queue())
    
    try:
        while True:
            data = await websocket.receive_text()
            last_activity = time.time()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "latency_ms": 0})
            elif message.get("type") in ["text", "audio"]:
                await message_queue.put(message)
            elif message.get("type") == "interrupt":
                await voice_engine.interrupt_call(user_id)
                await websocket.send_json({"type": "interrupt_ack"})
            elif message.get("type") == "end":
                await voice_engine.end_call(user_id)
                break
                
    except WebSocketDisconnect:
        queue_task.cancel()
        await voice_engine.end_call(user_id)
    except Exception as e:
        queue_task.cancel()
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


class MasterAgentRequest(BaseModel):
    prompt: str
    user_id: Optional[int] = 0


class UserPromptRequest(BaseModel):
    user_id: int
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class StreamingRequest(BaseModel):
    user_id: int
    session_id: str
    chunks: List[str]


@router.post("/prompt/process")
async def process_prompt(request: UserPromptRequest, user=Depends(get_current_user)):
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    session_id = await master_agent.process(
        prompt=request.message,
        user_id=request.user_id,
        session_id=session_id
    )
    
    await asyncio.sleep(0.2)
    state = await master_agent.get_session(session_id)
    
    return {
        "session_id": session_id,
        "user_id": request.user_id,
        "prompt": request.message,
        "intent": state.get("intent", "unknown"),
        "status": state.get("status", "unknown"),
        "agents_triggered": state.get("total_tasks", 0),
        "completed": state.get("completed_tasks", 0),
        "failed": state.get("failed_tasks", 0),
        "results": state.get("tasks", []),
        "context": request.context or {}
    }


@router.post("/prompt/stream")
async def stream_prompt(request: StreamingRequest, user=Depends(get_current_user)):
    results = []
    
    for i, chunk in enumerate(request.chunks):
        session_id = await master_agent.process(
            prompt=chunk,
            user_id=request.user_id,
            session_id=f"{request.session_id}_chunk_{i}"
        )
        
        await asyncio.sleep(0.1)
        state = await master_agent.get_session(session_id)
        
        results.append({
            "chunk_index": i,
            "session_id": session_id,
            "prompt": chunk,
            "intent": state.get("intent"),
            "tasks_triggered": state.get("total_tasks", 0)
        })
    
    return {
        "stream_id": request.session_id,
        "chunks_processed": len(request.chunks),
        "results": results
    }


@router.get("/prompt/history/{user_id}")
async def get_user_prompt_history(user_id: int, user=Depends(get_current_user)):
    all_sessions = await master_agent.get_all_sessions()
    
    user_sessions = [s for s in all_sessions if s.get("session_id", "").startswith(str(user_id)) 
                     or s.get("user_id") == user_id]
    
    return {
        "user_id": user_id,
        "total_prompts": len(user_sessions),
        "sessions": user_sessions[-10:]
    }


@router.get("/prompt/context/{session_id}")
async def get_prompt_context(session_id: str, user=Depends(get_current_user)):
    state = await master_agent.get_session(session_id)
    
    if not state:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "prompt": state.get("prompt"),
        "conversation_context": state.get("conversation_context", []),
        "intent": state.get("intent"),
        "agents": state.get("agents_used", []),
        "tools": state.get("tools_used", []),
        "memory_stats": state.get("memory_stats", {})
    }


@router.post("/prompt/follow-up")
async def continue_conversation(request: UserPromptRequest, user=Depends(get_current_user)):
    if request.session_id:
        prev_state = await master_agent.get_session(request.session_id)
        if prev_state:
            context = prev_state.get("conversation_context", [])
            enriched_prompt = f"Context: {' '.join(context[-3:])} | Follow-up: {request.message}"
        else:
            enriched_prompt = request.message
    else:
        enriched_prompt = request.message
    
    session_id = await master_agent.process(
        prompt=enriched_prompt,
        user_id=request.user_id,
        session_id=str(uuid.uuid4())[:8]
    )
    
    await asyncio.sleep(0.2)
    state = await master_agent.get_session(session_id)
    
    return {
        "session_id": session_id,
        "original_session": request.session_id,
        "prompt": request.message,
        "enriched_prompt": enriched_prompt[:100] + "..." if len(enriched_prompt) > 100 else enriched_prompt,
        "intent": state.get("intent"),
        "status": state.get("status"),
        "results": state.get("tasks", [])
    }


@router.post("/master-agent/process")
async def process_with_master_agent(request: MasterAgentRequest, user=Depends(get_current_user)):
    session_id = await master_agent.process(request.prompt, request.user_id)
    await asyncio.sleep(0.2)
    state = await master_agent.get_session(session_id)
    
    return {
        "session_id": session_id,
        "status": state["status"],
        "intent": state["intent"],
        "agents_triggered": state["total_tasks"],
        "results": [
            {
                "name": a["name"],
                "type": a["type"],
                "status": a["status"],
                "duration_ms": a["duration_ms"],
                "result": a["result"],
                "error": a["error"]
            }
            for a in state["tasks"]
        ]
    }


@router.get("/master-agent/sessions")
async def get_all_sessions(user=Depends(get_current_user)):
    sessions = await master_agent.get_all_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/master-agent/sessions/active")
async def get_active_sessions(user=Depends(get_current_user)):
    sessions = await master_agent.get_active_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/master-agent/session/{session_id}")
async def get_session_state(session_id: str, user=Depends(get_current_user)):
    state = await master_agent.get_session(session_id)
    if not state:
        return {"error": "Session not found"}
    return state


@router.get("/master-agent/stats")
async def get_master_agent_stats(user=Depends(get_current_user)):
    return await master_agent.get_stats()


@router.get("/master-agent/registry")
async def get_agent_registry(user=Depends(get_current_user)):
    return {
        "agents": master_agent.agents,
        "tools": master_agent.tools,
        "intents": master_agent.intents
    }


@router.delete("/master-agent/session/{session_id}")
async def clear_session(session_id: str, user=Depends(get_current_user)):
    await master_agent.clear_session(session_id)
    return {"cleared": session_id}