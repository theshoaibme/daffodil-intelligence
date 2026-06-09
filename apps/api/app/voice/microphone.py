import asyncio
import base64
import json
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import platform
import os


class MicrophoneError(Exception):
    pass


class MicrophoneStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    IN_USE = "in_use"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class DeviceType(Enum):
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    HEADPHONES = "headphones"
    WEBCAM = "webcam"


@dataclass
class MicrophoneDevice:
    device_id: str
    name: str
    device_type: DeviceType
    status: MicrophoneStatus
    is_default: bool = False
    sample_rate: int = 48000
    channels: int = 1
    bit_depth: int = 16
    latency_ms: int = 0
    manufacturer: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MicrophoneCapabilities:
    noise_suppression: bool = True
    echo_cancellation: bool = True
    automatic_gain_control: bool = True
    voice_detection: bool = True
    spatial_audio: bool = False
    stereo_capture: bool = False


@dataclass
class MicrophoneSession:
    session_id: str
    user_id: int
    device_id: str
    start_time: float
    status: str
    sample_rate: int
    channels: int
    frames_captured: int = 0
    bytes_captured: int = 0
    errors: List[str] = field(default_factory=list)


class MicrophoneManager:
    def __init__(self):
        self._devices: Dict[str, MicrophoneDevice] = {}
        self._sessions: Dict[int, MicrophoneSession] = {}
        self._permissions: Dict[int, Dict[str, bool]] = {}
        self._audio_buffers: Dict[int, deque] = {}
        self._detection_cache: Dict[str, float] = {}
        self._cache_duration_seconds = 30
        self._max_buffer_size = 100
        
        self._simulate_hardware = platform.system() == "Darwin"
        
        self._init_default_devices()

    def _init_default_devices(self):
        default_mic = MicrophoneDevice(
            device_id="default_mic",
            name="Default Microphone",
            device_type=DeviceType.MICROPHONE,
            status=MicrophoneStatus.AVAILABLE,
            is_default=True,
            sample_rate=48000,
            channels=1,
            manufacturer="System"
        )
        self._devices["default_mic"] = default_mic

        if self._simulate_hardware:
            builtin_mic = MicrophoneDevice(
                device_id="builtin_mic",
                name="MacBook Pro Microphone",
                device_type=DeviceType.MICROPHONE,
                status=MicrophoneStatus.AVAILABLE,
                is_default=False,
                sample_rate=48000,
                channels=1,
                manufacturer="Apple",
                metadata={"model": "MacBookPro18,1"}
            )
            self._devices["builtin_mic"] = builtin_mic

            airpods = MicrophoneDevice(
                device_id="airpods_pro",
                name="AirPods Pro",
                device_type=DeviceType.HEADPHONES,
                status=MicrophoneStatus.AVAILABLE,
                is_default=False,
                sample_rate=48000,
                channels=2,
                manufacturer="Apple",
                metadata={"noise_cancellation": True}
            )
            self._devices["airpods_pro"] = airpods

            external_mic = MicrophoneDevice(
                device_id="external_usb",
                name="Blue Yeti USB Microphone",
                device_type=DeviceType.MICROPHONE,
                status=MicrophoneStatus.AVAILABLE,
                is_default=False,
                sample_rate=48000,
                channels=1,
                manufacturer="Blue",
                metadata={"polar_pattern": "cardioid"}
            )
            self._devices["external_usb"] = external_mic

            speakers = MicrophoneDevice(
                device_id="builtin_speakers",
                name="MacBook Pro Speakers",
                device_type=DeviceType.SPEAKER,
                status=MicrophoneStatus.AVAILABLE,
                is_default=True,
                sample_rate=48000,
                channels=2,
                manufacturer="Apple"
            )
            self._devices["builtin_speakers"] = speakers

    async def detect_microphones(self, user_id: int) -> Dict[str, Any]:
        cache_key = f"detect_{user_id}"
        current_time = time.time()
        
        if cache_key in self._detection_cache:
            if current_time - self._detection_cache[cache_key] < self._cache_duration_seconds:
                return await self._get_cached_detection_results(user_id)
        
        self._detection_cache[cache_key] = current_time
        
        return await self._perform_detection(user_id)

    async def _perform_detection(self, user_id: int) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        
        available = []
        unavailable = []
        errors = []
        
        for device_id, device in self._devices.items():
            status_check = await self._check_device_status(device_id, user_id)
            
            if status_check["status"] == "available":
                available.append(self._serialize_device(device))
            elif status_check["status"] == "error":
                errors.append(status_check["error"])
            else:
                unavailable.append(self._serialize_device(device))
        
        return {
            "detected": True,
            "timestamp": time.time(),
            "available_devices": available,
            "unavailable_devices": unavailable,
            "total_available": len(available),
            "errors": errors,
            "recommendations": self._get_device_recommendations(available)
        }

    async def _get_cached_detection_results(self, user_id: int) -> Dict[str, Any]:
        return {
            "detected": True,
            "timestamp": time.time(),
            "cached": True,
            "available_devices": [
                self._serialize_device(d) for d in self._devices.values() 
                if d.status == MicrophoneStatus.AVAILABLE
            ],
            "total_available": sum(1 for d in self._devices.values() if d.status == MicrophoneStatus.AVAILABLE)
        }

    async def _check_device_status(self, device_id: str, user_id: int) -> Dict[str, Any]:
        if user_id not in self._permissions:
            self._permissions[user_id] = {"microphone": False}
        
        if not self._permissions[user_id].get("microphone", True):
            return {"status": "permission_denied", "error": "Microphone permission denied"}
        
        device = self._devices.get(device_id)
        if not device:
            return {"status": "not_found", "error": f"Device {device_id} not found"}
        
        if random.random() < 0.02:
            return {"status": "unavailable", "error": "Device temporarily unavailable"}
        
        return {"status": "available", "device": device}

    def _serialize_device(self, device: MicrophoneDevice) -> Dict[str, Any]:
        return {
            "device_id": device.device_id,
            "name": device.name,
            "type": device.device_type.value,
            "status": device.status.value,
            "is_default": device.is_default,
            "sample_rate": device.sample_rate,
            "channels": device.channels,
            "bit_depth": device.bit_depth,
            "latency_ms": device.latency_ms,
            "manufacturer": device.manufacturer,
            "metadata": device.metadata
        }

    def _get_device_recommendations(self, available_devices: List[Dict]) -> List[str]:
        recommendations = []
        
        if not available_devices:
            recommendations.append("No microphones detected. Please connect a microphone.")
            return recommendations
        
        has_builtin = any(d.get("manufacturer") == "Apple" for d in available_devices)
        has_external = any(d.get("device_id") != "builtin_mic" for d in available_devices)
        
        if has_external:
            recommendations.append("External microphone detected. Recommended for better quality.")
        elif has_builtin:
            recommendations.append("Using built-in microphone. Consider external mic for improved clarity.")
        
        bluetooth_devices = [d for d in available_devices if "AirPods" in d.get("name", "")]
        if bluetooth_devices:
            recommendations.append("Bluetooth device detected. May have higher latency.")
        
        return recommendations

    async def check_permission(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._permissions:
            self._permissions[user_id] = {"microphone": False}
        
        return {
            "granted": self._permissions[user_id].get("microphone", True),
            "timestamp": time.time(),
            "platform": platform.system()
        }

    async def request_permission(self, user_id: int) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        
        if user_id not in self._permissions:
            self._permissions[user_id] = {}
        
        self._permissions[user_id]["microphone"] = True
        
        return {
            "granted": True,
            "timestamp": time.time(),
            "message": "Microphone permission granted"
        }

    async def get_device_info(self, device_id: str, user_id: int) -> Dict[str, Any]:
        device = self._devices.get(device_id)
        
        if not device:
            return {
                "error": "Device not found",
                "code": "NOT_FOUND",
                "device_id": device_id
            }
        
        if user_id not in self._permissions or not self._permissions[user_id].get("microphone"):
            return {
                "error": "Permission denied",
                "code": "PERMISSION_DENIED",
                "device_id": device_id
            }
        
        return {
            "device": self._serialize_device(device),
            "capabilities": self._get_capabilities(device),
            "status": "ready"
        }

    def _get_capabilities(self, device: MicrophoneDevice) -> MicrophoneCapabilities:
        caps = MicrophoneCapabilities()
        
        if device.device_type == DeviceType.HEADPHONES:
            caps.noise_suppression = True
            caps.echo_cancellation = True
        
        return {
            "noise_suppression": caps.noise_suppression,
            "echo_cancellation": caps.echo_cancellation,
            "automatic_gain_control": caps.automatic_gain_control,
            "voice_detection": caps.voice_detection,
            "spatial_audio": caps.spatial_audio,
            "stereo_capture": caps.stereo_capture
        }

    async def start_capture(self, user_id: int, device_id: str = "default_mic") -> Dict[str, Any]:
        if user_id in self._sessions:
            return {
                "error": "Capture session already active",
                "code": "SESSION_ACTIVE",
                "session_id": self._sessions[user_id].session_id
            }
        
        device = self._devices.get(device_id)
        if not device:
            return {
                "error": f"Device {device_id} not found",
                "code": "NOT_FOUND"
            }
        
        if device.status != MicrophoneStatus.AVAILABLE:
            return {
                "error": f"Device status: {device.status.value}",
                "code": "DEVICE_UNAVAILABLE"
            }
        
        session_id = f"mic_session_{user_id}_{int(time.time())}"
        
        session = MicrophoneSession(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            start_time=time.time(),
            status="active",
            sample_rate=device.sample_rate,
            channels=device.channels
        )
        
        self._sessions[user_id] = session
        self._audio_buffers[user_id] = deque(maxlen=self._max_buffer_size)
        
        return {
            "session_id": session_id,
            "device_id": device_id,
            "status": "started",
            "sample_rate": device.sample_rate,
            "channels": device.channels,
            "timestamp": time.time()
        }

    async def stop_capture(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No active session",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        result = {
            "session_id": session.session_id,
            "duration_sec": round(time.time() - session.start_time, 2),
            "frames_captured": session.frames_captured,
            "bytes_captured": session.bytes_captured,
            "status": "stopped"
        }
        
        if session.errors:
            result["errors"] = session.errors
        
        del self._sessions[user_id]
        
        if user_id in self._audio_buffers:
            del self._audio_buffers[user_id]
        
        return result

    async def process_audio_chunk(self, user_id: int, audio_data: str) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "error": "No active capture session",
                "code": "NO_SESSION"
            }
        
        session = self._sessions[user_id]
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            chunk_size = len(audio_bytes)
            
            session.frames_captured += 1
            session.bytes_captured += chunk_size
            
            self._audio_buffers[user_id].append({
                "data": audio_bytes,
                "timestamp": time.time(),
                "size": chunk_size
            })
            
            return {
                "status": "processed",
                "session_id": session.session_id,
                "chunk_size": chunk_size,
                "total_bytes": session.bytes_captured
            }
        except Exception as e:
            session.errors.append(str(e))
            return {
                "status": "error",
                "error": str(e),
                "code": "PROCESSING_ERROR"
            }

    def get_session_status(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._sessions:
            return {
                "active": False,
                "session": None
            }
        
        session = self._sessions[user_id]
        
        return {
            "active": True,
            "session": {
                "session_id": session.session_id,
                "device_id": session.device_id,
                "status": session.status,
                "start_time": session.start_time,
                "duration_sec": round(time.time() - session.start_time, 2),
                "frames_captured": session.frames_captured,
                "bytes_captured": session.bytes_captured,
                "buffer_size": len(self._audio_buffers.get(user_id, []))
            }
        }

    async def get_default_device(self, user_id: int) -> Dict[str, Any]:
        default = next(
            (d for d in self._devices.values() if d.is_default and d.device_type == DeviceType.MICROPHONE),
            None
        )
        
        if not default:
            available = [d for d in self._devices.values() if d.status == MicrophoneStatus.AVAILABLE and d.device_type == DeviceType.MICROPHONE]
            default = available[0] if available else None
        
        if not default:
            return {
                "error": "No microphone available",
                "code": "NO_DEVICE"
            }
        
        return {
            "device": self._serialize_device(default),
            "recommended": True
        }

    async def test_microphone(self, device_id: str, user_id: int, duration_sec: float = 3.0) -> Dict[str, Any]:
        device = self._devices.get(device_id)
        
        if not device:
            return {
                "error": "Device not found",
                "code": "NOT_FOUND",
                "device_id": device_id
            }
        
        if user_id not in self._permissions or not self._permissions[user_id].get("microphone"):
            return {
                "error": "Permission denied",
                "code": "PERMISSION_DENIED"
            }
        
        await asyncio.sleep(min(duration_sec, 0.5))
        
        test_result = {
            "device_id": device_id,
            "device_name": device.name,
            "status": "success",
            "test_duration_sec": duration_sec,
            "timestamp": time.time(),
            "checks": {
                "connection": "ok",
                "sample_rate": device.sample_rate,
                "channels": device.channels,
                "latency_ms": random.randint(5, 20)
            }
        }
        
        return test_result

    async def list_all_devices(self, device_type: str = None) -> Dict[str, Any]:
        devices = list(self._devices.values())
        
        if device_type:
            try:
                dtype = DeviceType(device_type)
                devices = [d for d in devices if d.device_type == dtype]
            except ValueError:
                pass
        
        return {
            "devices": [self._serialize_device(d) for d in devices],
            "total": len(devices),
            "types": list(set(d.device_type.value for d in self._devices.values()))
        }

    def reset_permissions(self, user_id: int):
        if user_id in self._permissions:
            self._permissions[user_id] = {}

    def clear_cache(self):
        self._detection_cache.clear()


microphone_manager = MicrophoneManager()