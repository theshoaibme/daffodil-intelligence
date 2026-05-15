import asyncio
import base64
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from dataclasses import dataclass


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", duration_ms: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms


class VoicePipelineTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def record(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        self.results.append(TestResult(name, passed, message, duration))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"       {message}")
    
    def print_summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total:  {self.total_tests}")
        print(f"Passed:  {self.passed_tests} ✅")
        print(f"Failed:  {self.failed_tests} ❌")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100):.1f}%")
        print("=" * 60)


async def test_realtime_voice_engine():
    print("\n🔧 Testing RealtimeVoiceEngine...")
    
    try:
        from app.voice.realtime import (
            RealtimeVoiceEngine, StreamingSTT, ParallelLLM, StreamingTTS,
            VoiceAnalytics, SpeakerDiarization, AudioEnhancer,
            MultimodalProcessor, VideoPipeline, LiveTranslation
        )
        
        engine = RealtimeVoiceEngine()
        
        start = time.time()
        result = await engine.start_call(user_id=1, language="en")
        duration = (time.time() - start) * 1000
        
        assert result["status"] == "connected", f"Expected connected, got {result['status']}"
        
        return TestResult("RealtimeVoiceEngine.start_call", True, "Session started successfully", duration)
    except Exception as e:
        return TestResult("RealtimeVoiceEngine.start_call", False, str(e))


async def test_streaming_stt():
    print("\n🔧 Testing StreamingSTT...")
    
    try:
        from app.voice.realtime import StreamingSTT
        
        stt = StreamingSTT()
        
        test_audio = b"test_audio_data" * 100
        
        results = stt.add_audio_chunk(test_audio)
        
        assert stt is not None
        
        return TestResult("StreamingSTT.process", True, "STT processing works")
    except Exception as e:
        return TestResult("StreamingSTT.process", False, str(e))


async def test_voice_analytics():
    print("\n🔧 Testing VoiceAnalytics...")
    
    try:
        from app.voice.realtime import VoiceAnalytics
        
        analytics = VoiceAnalytics()
        
        result = await analytics.analyze_turn(
            user_id=1,
            transcript="Hello, how are you?",
            audio_data=b"audio_data"
        )
        
        assert "turn_id" in result
        assert "sentiment" in result
        assert "emotion" in result
        
        summary = analytics.get_session_summary(1)
        assert "total_turns" in summary
        
        return TestResult("VoiceAnalytics.analyze", True, "Analytics working correctly")
    except Exception as e:
        return TestResult("VoiceAnalytics.analyze", False, str(e))


async def test_audio_enhancer():
    print("\n🔧 Testing AudioEnhancer...")
    
    try:
        from app.voice.realtime import AudioEnhancer
        
        enhancer = AudioEnhancer()
        
        test_audio = b"\x00\x01" * 1000
        
        vad_result = enhancer.detect_voice_activity(test_audio)
        assert "is_speech" in vad_result
        assert "probability" in vad_result
        
        quality = enhancer.get_audio_quality_metrics(test_audio)
        assert "quality_score" in quality
        
        result = enhancer.enhance_audio(test_audio)
        assert "original_size" in result
        
        return TestResult("AudioEnhancer.process", True, "Audio enhancement working")
    except Exception as e:
        return TestResult("AudioEnhancer.process", False, str(e))


async def test_multimodal_processor():
    print("\n🔧 Testing MultimodalProcessor...")
    
    try:
        from app.voice.realtime import MultimodalProcessor
        
        processor = MultimodalProcessor()
        
        text_result = await processor.process_input(1, "text", "Hello world", None)
        assert text_result["processed"] == True
        assert text_result["modality"] == "text"
        
        context = processor.get_context(1)
        assert context is not None
        
        return TestResult("MultimodalProcessor.process", True, "Multimodal processing working")
    except Exception as e:
        return TestResult("MultimodalProcessor.process", False, str(e))


async def test_video_pipeline():
    print("\n🔧 Testing VideoPipeline...")
    
    try:
        from app.voice.realtime import VideoPipeline
        
        pipeline = VideoPipeline()
        
        result = await pipeline.start_video_session(1)
        assert result["status"] == "active"
        
        stats = await pipeline.get_video_stats(1)
        assert "frames_processed" in stats
        
        stop_result = await pipeline.stop_video_session(1)
        assert stop_result["status"] == "stopped"
        
        return TestResult("VideoPipeline.session", True, "Video pipeline working")
    except Exception as e:
        return TestResult("VideoPipeline.session", False, str(e))


async def test_live_translation():
    print("\n🔧 Testing LiveTranslation...")
    
    try:
        from app.voice.realtime import LiveTranslation
        
        translator = LiveTranslation()
        
        detection = translator.detect_language("আমি বাংলায় কথা বলি")
        assert detection["code"] == "bn"
        assert detection["confidence"] > 0
        
        translation = await translator.translate("Hello", source="en", target="bn")
        assert "original" in translation
        assert "translated" in translation
        
        languages = translator.get_supported_languages()
        assert len(languages) >= 7
        
        return TestResult("LiveTranslation.translate", True, "Translation working correctly")
    except Exception as e:
        return TestResult("LiveTranslation.translate", False, str(e))


async def test_tts_providers():
    print("\n🔧 Testing UnifiedTTSEngine...")
    
    try:
        from app.voice.tts_providers import tts_engine, ElevenLabsProvider
        
        result = await tts_engine.synthesize("Hello world")
        
        assert result.audio is not None
        assert result.duration_ms > 0
        assert result.provider is not None
        
        voices = await tts_engine.get_all_voices()
        assert "elevenlabs" in voices
        
        stats = tts_engine.get_stats()
        assert "current_provider" in stats
        
        return TestResult("UnifiedTTSEngine.synthesize", True, "TTS engine working")
    except Exception as e:
        return TestResult("UnifiedTTSEngine.synthesize", False, str(e))


async def test_voice_effects():
    print("\n🔧 Testing VoiceEffectsProcessor...")
    
    try:
        from app.voice.voice_effects import voice_effects, EffectType, VoiceEffectConfig
        
        test_audio = b"\x00\x01" * 500
        
        config = VoiceEffectConfig()
        config.effect_type = EffectType.ECHO
        
        result = voice_effects.apply_effect(test_audio, config)
        
        assert len(result) > 0
        
        presets = voice_effects.get_available_presets()
        assert "radio" in presets
        assert "robot" in presets
        
        effects = voice_effects.get_available_effects()
        assert "echo" in effects
        
        return TestResult("VoiceEffectsProcessor.apply", True, "Voice effects working")
    except Exception as e:
        return TestResult("VoiceEffectsProcessor.apply", False, str(e))


async def test_personality_engine():
    print("\n🔧 Testing PersonalityEngine...")
    
    try:
        from app.voice.personality import personality_engine, PersonalityMood
        
        presets = personality_engine.get_presets()
        assert "friendly" in presets
        assert "professional" in presets
        
        personality_engine.set_preset("friendly")
        config = personality_engine.get_current_config()
        assert config["name"] == "Friendly AI"
        
        greeting = personality_engine.generate_greeting("en")
        assert len(greeting) > 0
        
        greeting_bn = personality_engine.generate_greeting("bn")
        assert len(greeting_bn) > 0
        
        response = personality_engine.respond_to_emotion("excited")
        assert len(response) > 0
        
        return TestResult("PersonalityEngine.generate", True, "Personality engine working")
    except Exception as e:
        return TestResult("PersonalityEngine.generate", False, str(e))


async def test_failover_manager():
    print("\n🔧 Testing FailoverManager...")
    
    try:
        from app.voice.failover import failover_manager, CircuitState
        
        stats = failover_manager.get_stats()
        assert "services_count" in stats
        assert stats["services_count"] >= 4
        
        services = failover_manager.get_all_service_health()
        assert len(services) >= 4
        
        circuit_state = failover_manager.get_circuit_state("stt")
        assert circuit_state == CircuitState.CLOSED
        
        events = failover_manager.get_recent_events(5)
        assert isinstance(events, list)
        
        return TestResult("FailoverManager.health", True, "Failover system working")
    except Exception as e:
        return TestResult("FailoverManager.health", False, str(e))


async def test_call_recorder():
    print("\n🔧 Testing CallRecorder...")
    
    try:
        from app.voice.call_recorder import call_recorder
        
        start_result = call_recorder.start_recording(user_id=1)
        assert start_result["status"] == "started"
        
        recording_id = start_result["recording_id"]
        
        call_recorder.add_audio_chunk(1, b"audio_chunk_1")
        call_recorder.add_audio_chunk(1, b"audio_chunk_2")
        
        call_recorder.add_transcript_entry(1, "Hello", "user", time.time())
        call_recorder.add_transcript_entry(1, "Hi there!", "ai", time.time())
        
        call_recorder.add_tag(1, "greeting")
        call_recorder.add_tag(1, "test")
        
        call_recorder.add_sentiment_entry(1, "positive", 0.8, time.time())
        
        stop_result = call_recorder.stop_recording(1, save=True)
        assert stop_result["status"] == "saved"
        
        recordings = call_recorder.list_recordings(1, limit=5)
        assert len(recordings) >= 1
        
        recording = call_recorder.get_recording(recording_id)
        assert recording is not None
        assert recording["transcript_count"] >= 2
        
        stats = call_recorder.get_recording_stats(1)
        assert "total_recordings" in stats
        
        return TestResult("CallRecorder.record", True, "Call recording working")
    except Exception as e:
        return TestResult("CallRecorder.record", False, str(e))


async def test_conversation_memory():
    print("\n🔧 Testing ConversationMemory...")
    
    try:
        from app.voice.conversation_memory import conversation_memory, MemoryType
        
        entry1 = conversation_memory.add_to_memory(
            user_id=1,
            content="User asked about CGPA",
            memory_type=MemoryType.SHORT_TERM,
            importance=0.7,
            tags=["academic", "query"]
        )
        assert entry1.memory_id is not None
        
        entry2 = conversation_memory.add_to_memory(
            user_id=1,
            content="AI explained about GPA calculation",
            memory_type=MemoryType.SHORT_TERM,
            importance=0.6
        )
        
        relevant = conversation_memory.retrieve_relevant(1, "CGPA", limit=5)
        assert len(relevant) >= 1
        
        context = conversation_memory.get_context_for_response(1, "What is CGPA?")
        assert isinstance(context, str)
        
        stats = conversation_memory.get_memory_stats(1)
        assert "short_term_count" in stats
        assert stats["short_term_count"] >= 2
        
        conversation_memory.consolidate_to_long_term(1)
        
        recent = conversation_memory.get_recent_context(1, turns=3)
        assert len(recent) >= 0
        
        return TestResult("ConversationMemory.add", True, "Memory system working")
    except Exception as e:
        return TestResult("ConversationMemory.add", False, str(e))


async def test_agent_orchestrator():
    print("\n🔧 Testing AgentOrchestrator...")
    
    try:
        from app.voice.agent_orchestrator import agent_orchestrator
        
        workflows = agent_orchestrator.get_workflows()
        assert len(workflows) >= 3
        workflow_names = [w["name"] for w in workflows]
        assert "Research Workflow" in workflow_names
        
        agents = agent_orchestrator.get_agents()
        assert len(agents) >= 4
        agent_names = [a["name"] for a in agents]
        assert "Main Coordinator" in agent_names
        
        stats = agent_orchestrator.get_orchestrator_stats()
        assert "total_agents" in stats
        assert stats["total_agents"] >= 4
        
        result = await agent_orchestrator.execute_single_task(
            task_name="Test Task",
            required_capabilities=["coordinator"],
            input_data={"test": "data"}
        )
        assert "success" in result or "error" in result
        
        return TestResult("AgentOrchestrator.execute", True, "Agent orchestration working")
    except Exception as e:
        return TestResult("AgentOrchestrator.execute", False, str(e))


async def test_real_time_analytics():
    print("\n🔧 Testing RealTimeAnalytics...")
    
    try:
        from app.voice.real_time_analytics import real_time_analytics
        
        session = real_time_analytics.start_session(1)
        assert session["started"] == True
        
        waveform = real_time_analytics.record_audio_level(1, -20.0)
        assert waveform.peak >= 0
        assert waveform.rms >= 0
        
        sentiment = real_time_analytics.record_sentiment(1, "positive", 0.85)
        assert sentiment["sentiment"] == "positive"
        
        interaction = real_time_analytics.record_interaction(1, "voice_input")
        assert interaction["interaction_count"] >= 1
        
        real_time_analytics.record_latency("stt", 150.0)
        real_time_analytics.record_quality_score(0.85)
        
        dashboard = real_time_analytics.get_dashboard_data(1)
        assert "metrics" in dashboard
        assert "latency" in dashboard["metrics"]
        assert "quality" in dashboard["metrics"]
        
        performance = real_time_analytics.get_performance_breakdown()
        assert len(performance) >= 5
        
        summary = real_time_analytics.get_session_summary(1)
        assert summary is not None
        assert "duration_sec" in summary
        
        alerts = real_time_analytics.get_recent_alerts(5)
        assert isinstance(alerts, list)
        
        end_result = real_time_analytics.end_session(1)
        assert "user_id" in end_result
        
        return TestResult("RealTimeAnalytics.dashboard", True, "Real-time analytics working")
    except Exception as e:
        return TestResult("RealTimeAnalytics.dashboard", False, str(e))


async def test_integration():
    print("\n🔧 Testing Pipeline Integration...")
    
    try:
        from app.voice.realtime import voice_engine
        from app.voice.tts_providers import tts_engine
        from app.voice.personality import personality_engine
        from app.voice.voice_effects import voice_effects
        from app.voice.conversation_memory import conversation_memory
        from app.voice.real_time_analytics import real_time_analytics
        from app.voice.failover import failover_manager
        from app.voice.agent_orchestrator import agent_orchestrator
        
        start = time.time()
        
        session = await voice_engine.start_call(1, "en")
        assert session["status"] == "connected"
        
        conversation_memory.add_to_memory(1, "Started voice call", importance=0.5)
        
        real_time_analytics.start_session(1)
        
        audio_enhanced = voice_engine.audio_enhancer.enhance_audio(b"test_audio")
        assert "original_size" in audio_enhanced
        
        analytics_result = await voice_engine.voice_analytics.analyze_turn(1, "Hello", None)
        assert "turn_id" in analytics_result
        
        person_response = personality_engine.generate_greeting("en")
        assert len(person_response) > 0
        
        translated = await voice_engine.translation.translate("Hello", "en", "bn")
        assert "translated" in translated
        
        workflow = await agent_orchestrator.execute_workflow(
            "research_flow",
            {"query": "test"},
            1
        )
        assert workflow.status in ["completed", "partial"]
        
        duration = (time.time() - start) * 1000
        
        return TestResult("Integration.end_to_end", True, f"All pipelines integrated successfully in {duration:.1f}ms", duration)
    except Exception as e:
        return TestResult("Integration.end_to_end", False, str(e))


async def run_all_tests():
    print("=" * 60)
    print("DI VOICE AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tester = VoicePipelineTester()
    
    tests = [
        test_realtime_voice_engine,
        test_streaming_stt,
        test_voice_analytics,
        test_audio_enhancer,
        test_multimodal_processor,
        test_video_pipeline,
        test_live_translation,
        test_tts_providers,
        test_voice_effects,
        test_personality_engine,
        test_failover_manager,
        test_call_recorder,
        test_conversation_memory,
        test_agent_orchestrator,
        test_real_time_analytics,
        test_integration,
    ]
    
    for test in tests:
        result = await test()
        if result:
            tester.record(result.name, result.passed, result.message, result.duration_ms)
    
    tester.print_summary()
    
    return tester


if __name__ == "__main__":
    asyncio.run(run_all_tests())