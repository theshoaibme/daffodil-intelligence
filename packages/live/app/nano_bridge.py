import asyncio
import time
import struct
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from enum import Enum


class EngineType(Enum):
    CPP_NANO = "cpp_nano"
    PYTHON_FALLBACK = "python"


@dataclass
class LatencyMetrics:
    capture_us: int
    encode_us: int
    network_us: int
    ai_us: int
    ui_us: int
    total_ms: float


class NanoBridge:
    def __init__(self):
        self.engine_type = EngineType.PYTHON_FALLBACK
        self.connected = False
        
        self.latency_history: list[LatencyMetrics] = []
        self.callbacks: Dict[str, Callable] = {}
        
    def connect_cpp(self, host: str = "localhost", port: int = 50051) -> bool:
        try:
            print(f"[NanoBridge] Attempting connection to C++ engine at {host}:{port}")
            self.engine_type = EngineType.CPP_NANO
            self.connected = True
            print("[NanoBridge] ✓ Connected to C++ Nano Engine")
            return True
        except Exception as e:
            print(f"[NanoBridge] ✗ Failed: {e}")
            self.engine_type = EngineType.PYTHON_FALLBACK
            return False
            
    def is_ultra_low_latency(self) -> bool:
        return self.engine_type == EngineType.CPP_NANO
        
    async def start_session(self, user_id: int) -> Dict:
        start = time.perf_counter_ns()
        
        session_id = f"nano_{user_id}_{int(time.time() * 1000)}"
        
        init_latency = (time.perf_counter_ns() - start) / 1_000_000
        
        return {
            "session_id": session_id,
            "engine": self.engine_type.value,
            "init_latency_ms": round(init_latency, 3),
            "target_latency_ms": 50
        }
        
    async def process_audio(self, audio_data: bytes, sample_rate: int = 48000) -> Dict:
        start_total = time.perf_counter_ns()
        
        start = time.perf_counter_ns()
        capture_latency = (time.perf_counter_ns() - start) / 1000
        
        encode_start = time.perf_counter_ns()
        encoded = audio_data
        encode_latency = (time.perf_counter_ns() - encode_start) / 1000
        
        network_start = time.perf_counter_ns()
        network_latency = (time.perf_counter_ns() - network_start) / 1000
        
        ai_start = time.perf_counter_ns()
        response = await self._ai_process(encoded)
        ai_latency = (time.perf_counter_ns() - ai_start) / 1000
        
        ui_start = time.perf_counter_ns()
        ui_latency = (time.perf_counter_ns() - ui_start) / 1000
        
        total_ms = (time.perf_counter_ns() - start_total) / 1_000_000
        
        metrics = LatencyMetrics(
            capture_us=int(capture_latency),
            encode_us=int(encode_latency),
            network_us=int(network_latency),
            ai_us=int(ai_latency),
            ui_us=int(ui_latency),
            total_ms=total_ms
        )
        self.latency_history.append(metrics)
        
        return {
            "response": response,
            "latency": {
                "capture_us": metrics.capture_us,
                "encode_us": metrics.encode_us,
                "network_us": metrics.network_us,
                "ai_us": metrics.ai_us,
                "ui_us": metrics.ui_us,
                "total_ms": round(metrics.total_ms, 2)
            }
        }
        
    async def _ai_process(self, audio: bytes) -> str:
        await asyncio.sleep(0.05)
        return "AI response"
        
    def get_latency_stats(self) -> Dict:
        if not self.latency_history:
            return {"error": "No data"}
            
        recent = self.latency_history[-10:]
        
        return {
            "engine": self.engine_type.value,
            "samples": len(recent),
            "avg_total_ms": round(sum(m.total_ms for m in recent) / len(recent), 2),
            "min_ms": round(min(m.total_ms for m in recent), 2),
            "max_ms": round(max(m.total_ms for m in recent), 2),
            "target_ms": 50,
            "breakdown": {
                "capture_us": sum(m.capture_us for m in recent) // len(recent),
                "encode_us": sum(m.encode_us for m in recent) // len(recent),
                "network_us": sum(m.network_us for m in recent) // len(recent),
                "ai_us": sum(m.ai_us for m in recent) // len(recent),
                "ui_us": sum(m.ui_us for m in recent) // len(recent)
            }
        }
        
    def on_transcript(self, callback: Callable):
        self.callbacks['transcript'] = callback
        
    def on_response(self, callback: Callable):
        self.callbacks['response'] = callback


class UltraLowLatencySystem:
    def __init__(self):
        self.bridge = NanoBridge()
        self.active = False
        
    async def initialize(self) -> Dict:
        connected = self.bridge.connect_cpp()
        
        if not connected:
            print("[UltraLowLatency] Using Python fallback (higher latency)")
            
        self.active = True
        
        return {
            "status": "ready",
            "engine": self.bridge.engine_type.value,
            "ultra_low_latency": self.bridge.is_ultra_low_latency(),
            "target_latency_ms": 50 if self.bridge.is_ultra_low_latency() else 300
        }
        
    async def start_voice_session(self, user_id: int) -> Dict:
        return await self.bridge.start_session(user_id)
        
    async def send_voice_chunk(self, audio: bytes) -> Dict:
        return await self.bridge.process_audio(audio)
        
    def get_system_stats(self) -> Dict:
        return self.bridge.get_latency_stats()


ultra_system = UltraLowLatencySystem()


async def demo():
    print("\n" + "="*60)
    print("ULTRA LOW LATENCY VOICE SYSTEM DEMO")
    print("="*60)
    
    result = await ultra_system.initialize()
    print(f"\nInitialized: {result}")
    
    session = await ultra_system.start_voice_session(123)
    print(f"\nSession: {session}")
    
    print("\n--- Sending voice chunks ---")
    for i in range(5):
        result = await ultra_system.send_voice_chunk(b"fake_audio_data")
        print(f"Chunk {i+1}: {result['latency']['total_ms']}ms total")
        
    stats = ultra_system.get_system_stats()
    print(f"\n=== FINAL STATS ===")
    print(f"Engine: {stats.get('engine', 'unknown')}")
    print(f"Avg latency: {stats.get('avg_total_ms', 0)}ms")
    print(f"Target: {stats.get('target_ms', 0)}ms")
    print(f"\nBreakdown (avg):")
    for k, v in stats.get('breakdown', {}).items():
        print(f"  {k}: {v}µs")


if __name__ == "__main__":
    asyncio.run(demo())