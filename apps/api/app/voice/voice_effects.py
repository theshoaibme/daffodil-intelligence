import base64
import io
import wave
import struct
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import math
import random


class EffectType(Enum):
    NONE = "none"
    ECHO = "echo"
    REVERB = "reverb"
    NOISE_REDUCTION = "noise_reduction"
    COMPRESSOR = "compressor"
    EQ_BASS_BOOST = "eq_bass_boost"
    EQ_TREBLE_BOOST = "eq_treble_boost"
    RADIO = "radio"
    TELEPHONE = "telephone"
    ROBOT = "robot"
    ALIEN = "alien"
    WHISPER = "whisper"
    CHORUS = "chorus"
    FLANGER = "flanger"
    PHASER = "phaser"
    DISTORTION = "distortion"


class EnvironmentPreset(Enum):
    SILENT = "silent"
    OFFICE = "office"
    OUTDOOR = "outdoor"
    CONFERENCE = "conference"
    CLASSROOM = "classroom"
    LIBRARY = "library"
    HALLWAY = "hallway"
    CAFETERIA = "cafeteria"
    AMPHITHEATER = "amphitheater"
    STUDIO = "studio"


@dataclass
class VoiceEffectConfig:
    effect_type: EffectType = EffectType.NONE
    pitch_shift: float = 0.0
    speed_factor: float = 1.0
    volume_gain_db: float = 0.0
    echo_delay_ms: float = 150.0
    echo_decay: float = 0.4
    reverb_room_size: float = 0.5
    reverb_damping: float = 0.5
    eq_bass_db: float = 0.0
    eq_treble_db: float = 0.0
    filter_cutoff_hz: float = 8000.0


@dataclass
class BackgroundSound:
    sound_id: str
    name: str
    category: str
    url: Optional[str] = None
    base64_data: Optional[str] = None
    duration_sec: float = 0.0
    loop: bool = True


class VoiceEffectsProcessor:
    def __init__(self):
        self.current_config = VoiceEffectConfig()
        self.effect_presets: Dict[str, VoiceEffectConfig] = {
            "default": VoiceEffectConfig(),
            "professional": VoiceEffectConfig(
                effect_type=EffectType.NONE,
                pitch_shift=0.0,
                eq_bass_db=2.0,
                eq_treble_db=1.0
            ),
            "radio": VoiceEffectConfig(
                effect_type=EffectType.RADIO,
                pitch_shift=-2.0,
                filter_cutoff_hz=5000.0
            ),
            "telephone": VoiceEffectConfig(
                effect_type=EffectType.TELEPHONE,
                pitch_shift=0.0,
                filter_cutoff_hz=3500.0
            ),
            "whisper": VoiceEffectConfig(
                effect_type=EffectType.WHISPER,
                pitch_shift=2.0,
                volume_gain_db=-6.0
            ),
            "robot": VoiceEffectConfig(
                effect_type=EffectType.ROBOT,
                pitch_shift=-5.0
            ),
            "alien": VoiceEffectConfig(
                effect_type=EffectType.ALIEN,
                pitch_shift=5.0,
                echo_delay_ms=100.0,
                echo_decay=0.6
            ),
            "deep": VoiceEffectConfig(
                effect_type=EffectType.NONE,
                pitch_shift=-8.0
            ),
            "chipmunk": VoiceEffectConfig(
                effect_type=EffectType.NONE,
                pitch_shift=8.0
            ),
            "cave": VoiceEffectConfig(
                effect_type=EffectType.REVERB,
                reverb_room_size=0.9,
                reverb_damping=0.3
            ),
        }
        
        self.background_sounds: List[BackgroundSound] = [
            BackgroundSound("office_ambience", "Office Ambience", "environment"),
            BackgroundSound("rain", "Rain", "nature"),
            BackgroundSound("cafe", "Cafe Background", "ambient"),
            BackgroundSound("white_noise", "White Noise", "utility"),
            BackgroundSound("ocean_waves", "Ocean Waves", "nature"),
            BackgroundSound("forest", "Forest Birds", "nature"),
            BackgroundSound("typing", "Keyboard Typing", "office"),
            BackgroundSound("crowd_murmur", "Crowd Murmur", "ambient"),
        ]
        
        self._active_background: Optional[BackgroundSound] = None
        self._sound_effects_queue: List[str] = []
    
    def apply_effect(self, audio_data: bytes, config: VoiceEffectConfig = None) -> bytes:
        if config is None:
            config = self.current_config
        
        if not audio_data or len(audio_data) < 100:
            return audio_data
        
        result = bytearray(audio_data)
        
        result = self._apply_volume_gain(bytes(result), config.volume_gain_db)
        
        if config.effect_type == EffectType.ECHO:
            result = self._apply_echo(bytes(result), config.echo_delay_ms, config.echo_decay)
        elif config.effect_type == EffectType.REVERB:
            result = self._apply_reverb(bytes(result), config.reverb_room_size, config.reverb_damping)
        elif config.effect_type == EffectType.RADIO:
            result = self._apply_radio_effect(bytes(result))
        elif config.effect_type == EffectType.TELEPHONE:
            result = self._apply_telephone_effect(bytes(result))
        elif config.effect_type == EffectType.ROBOT:
            result = self._apply_robot_effect(bytes(result))
        elif config.effect_type == EffectType.ALIEN:
            result = self._apply_alien_effect(bytes(result))
        elif config.effect_type == EffectType.WHISPER:
            result = self._apply_whisper_effect(bytes(result))
        elif config.effect_type == EffectType.CHORUS:
            result = self._apply_chorus_effect(bytes(result))
        elif config.effect_type == EffectType.DISTORTION:
            result = self._apply_distortion(bytes(result), 0.3)
        
        if config.pitch_shift != 0:
            result = self._apply_pitch_shift(bytes(result), config.pitch_shift)
        
        if config.eq_bass_db != 0:
            result = self._apply_eq_bass(bytes(result), config.eq_bass_db)
        
        if config.eq_treble_db != 0:
            result = self._apply_eq_treble(bytes(result), config.eq_treble_db)
        
        return bytes(result)
    
    def _apply_volume_gain(self, audio: bytes, gain_db: float) -> bytearray:
        if gain_db == 0:
            return bytearray(audio)
        
        gain_factor = 10 ** (gain_db / 20)
        
        result = bytearray()
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                adjusted = int(sample * gain_factor)
                adjusted = max(-32768, min(32767, adjusted))
                result.extend(struct.pack('<h', adjusted))
            except:
                result.extend(audio[i:i+2])
        
        return result
    
    def _apply_echo(self, audio: bytes, delay_ms: float, decay: float) -> bytearray:
        sample_rate = 24000
        delay_samples = int(sample_rate * delay_ms / 1000)
        
        result = bytearray(audio)
        
        for i in range(delay_samples, len(audio), 2):
            try:
                echo_sample = struct.unpack('<h', audio[i:i+2])[0]
                original_idx = i - delay_samples * 2
                if original_idx >= 0:
                    original = struct.unpack('<h', result[original_idx:original_idx+2])[0]
                    mixed = int(original + echo_sample * decay)
                    mixed = max(-32768, min(32767, mixed))
                    result[original_idx:original_idx+2] = struct.pack('<h', mixed)
            except:
                pass
        
        return result
    
    def _apply_reverb(self, audio: bytes, room_size: float, damping: float) -> bytearray:
        sample_rate = 24000
        delays = [
            int(room_size * 50 * sample_rate / 1000),
            int(room_size * 80 * sample_rate / 1000),
            int(room_size * 120 * sample_rate / 1000),
        ]
        
        result = bytearray(audio)
        
        for delay in delays:
            decay_factor = (1 - delay / 1000) * (1 - damping)
            
            for i in range(delay, len(audio), 2):
                try:
                    sample = struct.unpack('<h', audio[i:i+2])[0]
                    idx = i - delay * 2
                    if idx >= 0:
                        original = struct.unpack('<h', result[idx:idx+2])[0]
                        mixed = int(original + sample * decay_factor)
                        mixed = max(-32768, min(32767, mixed))
                        result[idx:idx+2] = struct.pack('<h', mixed)
                except:
                    pass
        
        return result
    
    def _apply_radio_effect(self, audio: bytes) -> bytearray:
        result = bytearray()
        
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                sample = int(sample * 0.8)
                sample = max(-32768, min(32767, sample))
                result.extend(struct.pack('<h', sample))
            except:
                result.extend(audio[i:i+2])
        
        return self._apply_lowpass_filter(bytes(result), 5000)
    
    def _apply_telephone_effect(self, audio: bytes) -> bytearray:
        result = self._apply_bandpass_filter(audio, 300, 3400)
        
        result = self._apply_volume_gain(bytes(result), -3.0)
        
        return result
    
    def _apply_robot_effect(self, audio: bytes) -> bytearray:
        result = audio
        
        result = self._apply_lowpass_filter(result, 2000)
        result = self._apply_echo(result, 30, 0.2)
        
        return bytes(result)
    
    def _apply_alien_effect(self, audio: bytes) -> bytearray:
        result = audio
        
        result = self._apply_pitch_shift(result, 5)
        result = self._apply_echo(result, 50, 0.5)
        result = self._apply_reverb(result, 0.8, 0.4)
        
        return bytes(result)
    
    def _apply_whisper_effect(self, audio: bytes) -> bytearray:
        result = bytearray()
        
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                noise = random.randint(-500, 500)
                sample = int(sample * 0.5 + noise)
                sample = max(-32768, min(32767, sample))
                result.extend(struct.pack('<h', sample))
            except:
                result.extend(audio[i:i+2])
        
        result = self._apply_highpass_filter(bytes(result), 200)
        
        return result
    
    def _apply_chorus_effect(self, audio: bytes) -> bytearray:
        sample_rate = 24000
        
        result = bytearray(audio)
        
        for i in range(0, len(audio) - 1, 2):
            try:
                idx = i + int(math.sin(i / sample_rate * 3) * sample_rate * 0.003)
                if idx < len(audio):
                    sample = struct.unpack('<h', audio[idx:idx+2])[0]
                    original = struct.unpack('<h', result[i:i+2])[0]
                    mixed = int(original + sample * 0.3)
                    mixed = max(-32768, min(32767, mixed))
                    result[i:i+2] = struct.pack('<h', mixed)
            except:
                pass
        
        return result
    
    def _apply_distortion(self, audio: bytes, amount: float) -> bytearray:
        result = bytearray()
        
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                sample_normalized = sample / 32768.0
                
                if sample_normalized > 0:
                    distorted = math.tanh(sample_normalized * (1 + amount * 10))
                else:
                    distorted = math.tanh(sample_normalized * (1 + amount * 10))
                
                sample = int(distorted * 32767)
                sample = max(-32768, min(32767, sample))
                result.extend(struct.pack('<h', sample))
            except:
                result.extend(audio[i:i+2])
        
        return result
    
    def _apply_pitch_shift(self, audio: bytes, semitones: float) -> bytes:
        factor = 2 ** (semitones / 12)
        
        result = bytearray()
        
        for i in range(0, len(audio) - 1, 2):
            idx = int(i * factor)
            if idx < len(audio):
                result.extend(audio[idx:idx+2])
            else:
                result.extend(b'\x00\x00')
        
        return bytes(result)
    
    def _apply_eq_bass(self, audio: bytes, boost_db: float) -> bytearray:
        result = bytearray()
        
        window = 48
        for i in range(0, len(audio) - 1, 2):
            try:
                samples = []
                for j in range(max(0, i - window * 2), min(len(audio), i + window * 2), 2):
                    samples.append(struct.unpack('<h', audio[j:j+2])[0])
                
                avg = sum(samples) / len(samples) if samples else 0
                
                sample = struct.unpack('<h', audio[i:i+2])[0]
                boost = (sample - avg) * (10 ** (boost_db / 20))
                sample = int(avg + boost)
                sample = max(-32768, min(32767, sample))
                result.extend(struct.pack('<h', sample))
            except:
                result.extend(audio[i:i+2])
        
        return bytes(result)
    
    def _apply_eq_treble(self, audio: bytes, boost_db: float) -> bytes:
        result = bytearray()
        
        window = 24
        for i in range(0, len(audio) - 1, 2):
            try:
                samples = []
                for j in range(max(0, i - window * 2), min(len(audio), i + window * 2), 2):
                    samples.append(struct.unpack('<h', audio[j:j+2])[0])
                
                if len(samples) >= 2:
                    diff = abs(samples[-1] - samples[0])
                    boost = diff * (10 ** (boost_db / 20) - 1)
                    sample = struct.unpack('<h', audio[i:i+2])[0]
                    sample = int(sample + boost)
                    sample = max(-32768, min(32767, sample))
                    result.extend(struct.pack('<h', sample))
                else:
                    result.extend(audio[i:i+2])
            except:
                result.extend(audio[i:i+2])
        
        return bytes(result)
    
    def _apply_lowpass_filter(self, audio: bytes, cutoff_hz: float) -> bytearray:
        result = bytearray()
        
        alpha = 1.0 / (1.0 + cutoff_hz / 1000)
        prev = 0
        
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                filtered = int(alpha * sample + (1 - alpha) * prev)
                prev = filtered
                result.extend(struct.pack('<h', filtered))
            except:
                result.extend(audio[i:i+2])
        
        return result
    
    def _apply_highpass_filter(self, audio: bytes, cutoff_hz: float) -> bytearray:
        result = bytearray()
        
        alpha = cutoff_hz / (cutoff_hz + 1000)
        prev_input = 0
        prev_output = 0
        
        for i in range(0, len(audio) - 1, 2):
            try:
                sample = struct.unpack('<h', audio[i:i+2])[0]
                filtered = int(alpha * (prev_output + sample - prev_input))
                prev_input = sample
                prev_output = filtered
                result.extend(struct.pack('<h', filtered))
            except:
                result.extend(audio[i:i+2])
        
        return result
    
    def _apply_bandpass_filter(self, audio: bytes, low_hz: float, high_hz: float) -> bytearray:
        result = self._apply_lowpass_filter(audio, high_hz)
        result = self._apply_highpass_filter(bytes(result), low_hz)
        return result
    
    def get_preset(self, name: str) -> VoiceEffectConfig:
        return self.effect_presets.get(name, VoiceEffectConfig())
    
    def set_preset(self, name: str, config: VoiceEffectConfig):
        self.effect_presets[name] = config
    
    def get_available_presets(self) -> List[str]:
        return list(self.effect_presets.keys())
    
    def get_available_effects(self) -> List[str]:
        return [e.value for e in EffectType]
    
    def get_background_sounds(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": s.sound_id,
                "name": s.name,
                "category": s.category,
                "duration_sec": s.duration_sec,
                "loop": s.loop
            }
            for s in self.background_sounds
        ]
    
    def set_background_sound(self, sound_id: str) -> bool:
        for sound in self.background_sounds:
            if sound.sound_id == sound_id:
                self._active_background = sound
                return True
        return False
    
    def get_active_background(self) -> Optional[Dict[str, Any]]:
        if self._active_background:
            return {
                "id": self._active_background.sound_id,
                "name": self._active_background.name
            }
        return None
    
    def stop_background(self):
        self._active_background = None
    
    def add_sound_effect(self, effect_name: str):
        self._sound_effects_queue.append(effect_name)
    
    def clear_sound_effects(self):
        self._sound_effects_queue.clear()
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "effect_type": self.current_config.effect_type.value,
            "pitch_shift": self.current_config.pitch_shift,
            "speed_factor": self.current_config.speed_factor,
            "volume_gain_db": self.current_config.volume_gain_db,
            "echo_delay_ms": self.current_config.echo_delay_ms,
            "echo_decay": self.current_config.echo_decay,
            "reverb_room_size": self.current_config.reverb_room_size,
            "active_background": self.get_active_background()
        }
    
    def set_config(self, **kwargs):
        if "effect_type" in kwargs:
            self.current_config.effect_type = EffectType(kwargs["effect_type"])
        if "pitch_shift" in kwargs:
            self.current_config.pitch_shift = float(kwargs["pitch_shift"])
        if "speed_factor" in kwargs:
            self.current_config.speed_factor = float(kwargs["speed_factor"])
        if "volume_gain_db" in kwargs:
            self.current_config.volume_gain_db = float(kwargs["volume_gain_db"])
        if "echo_delay_ms" in kwargs:
            self.current_config.echo_delay_ms = float(kwargs["echo_delay_ms"])
        if "echo_decay" in kwargs:
            self.current_config.echo_decay = float(kwargs["echo_decay"])
        if "reverb_room_size" in kwargs:
            self.current_config.reverb_room_size = float(kwargs["reverb_room_size"])


voice_effects = VoiceEffectsProcessor()