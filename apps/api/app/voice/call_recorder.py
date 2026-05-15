import asyncio
import base64
import time
import json
import os
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import struct


class RecordingFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    WEBM = "webm"
    MP4 = "mp4"


class RecordingStatus(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    SAVED = "saved"
    ERROR = "error"


@dataclass
class RecordingMetadata:
    recording_id: str
    user_id: int
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    format: RecordingFormat = RecordingFormat.WAV
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    file_size_bytes: int = 0
    transcript: List[Dict] = field(default_factory=list)
    sentiment_timeline: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Recording:
    id: str
    metadata: RecordingMetadata
    audio_chunks: List[bytes] = field(default_factory=list)
    audio_data: Optional[bytes] = None


class CallRecorder:
    def __init__(self, storage_path: str = "./recordings"):
        self.storage_path = storage_path
        self.active_recordings: Dict[int, Recording] = {}
        self.completed_recordings: Dict[str, Recording] = {}
        self._max_recordings = 100
        self._auto_transcribe = True
        
        os.makedirs(storage_path, exist_ok=True)
        
        self._wav_header_size = 44
    
    def start_recording(self, user_id: int, format: RecordingFormat = RecordingFormat.WAV) -> Dict[str, Any]:
        recording_id = f"rec_{user_id}_{int(time.time() * 1000)}"
        
        metadata = RecordingMetadata(
            recording_id=recording_id,
            user_id=user_id,
            start_time=time.time(),
            format=format
        )
        
        recording = Recording(
            id=recording_id,
            metadata=metadata
        )
        
        self.active_recordings[user_id] = recording
        
        return {
            "recording_id": recording_id,
            "status": "started",
            "format": format.value,
            "user_id": user_id
        }
    
    def pause_recording(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.active_recordings:
            return {"error": "No active recording"}
        
        recording = self.active_recordings[user_id]
        recording.metadata.end_time = time.time()
        recording.metadata.duration_ms = (recording.metadata.end_time - recording.metadata.start_time) * 1000
        
        return {
            "recording_id": recording.id,
            "status": "paused",
            "duration_ms": recording.metadata.duration_ms
        }
    
    def resume_recording(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.active_recordings:
            return {"error": "No recording to resume"}
        
        recording = self.active_recordings[user_id]
        pause_duration = time.time() - (recording.metadata.end_time or time.time())
        
        new_start = recording.metadata.start_time + pause_duration
        recording.metadata.start_time = new_start
        recording.metadata.end_time = None
        
        return {
            "recording_id": recording.id,
            "status": "recording"
        }
    
    def stop_recording(self, user_id: int, save: bool = True) -> Dict[str, Any]:
        if user_id not in self.active_recordings:
            return {"error": "No active recording"}
        
        recording = self.active_recordings[user_id]
        end_time = time.time()
        
        recording.metadata.end_time = end_time
        recording.metadata.duration_ms = (end_time - recording.metadata.start_time) * 1000
        
        if recording.audio_chunks:
            recording.audio_data = self._merge_chunks(recording.audio_chunks)
            recording.metadata.file_size_bytes = len(recording.audio_data)
        
        del self.active_recordings[user_id]
        
        if save:
            self.completed_recordings[recording.id] = recording
            self._cleanup_old_recordings()
        
        return {
            "recording_id": recording.id,
            "status": "saved" if save else "stopped",
            "duration_ms": recording.metadata.duration_ms,
            "file_size_bytes": recording.metadata.file_size_bytes,
            "chunks_count": len(recording.audio_chunks)
        }
    
    def add_audio_chunk(self, user_id: int, audio_data: bytes) -> bool:
        if user_id not in self.active_recordings:
            return False
        
        recording = self.active_recordings[user_id]
        recording.audio_chunks.append(audio_data)
        
        return True
    
    def add_transcript_entry(self, user_id: int, text: str, speaker: str, timestamp: float):
        if user_id not in self.active_recordings:
            return False
        
        recording = self.active_recordings[user_id]
        recording.metadata.transcript.append({
            "text": text,
            "speaker": speaker,
            "timestamp": timestamp,
            "offset_ms": int((timestamp - recording.metadata.start_time) * 1000)
        })
        
        return True
    
    def add_sentiment_entry(self, user_id: int, sentiment: str, score: float, timestamp: float):
        if user_id not in self.active_recordings:
            return False
        
        recording = self.active_recordings[user_id]
        recording.metadata.sentiment_timeline.append({
            "sentiment": sentiment,
            "score": score,
            "timestamp": timestamp,
            "offset_ms": int((timestamp - recording.metadata.start_time) * 1000)
        })
        
        return True
    
    def add_tag(self, user_id: int, tag: str) -> bool:
        if user_id not in self.active_recordings:
            return False
        
        recording = self.active_recordings[user_id]
        if tag not in recording.metadata.tags:
            recording.metadata.tags.append(tag)
        
        return True
    
    def set_notes(self, user_id: int, notes: str) -> bool:
        if user_id not in self.active_recordings:
            return False
        
        self.active_recordings[user_id].metadata.notes = notes
        return True
    
    def _merge_chunks(self, chunks: List[bytes]) -> bytes:
        return b"".join(chunks)
    
    def _cleanup_old_recordings(self):
        while len(self.completed_recordings) > self._max_recordings:
            oldest = min(
                self.completed_recordings.items(),
                key=lambda x: x[1].metadata.start_time
            )
            del self.completed_recordings[oldest[0]]
    
    def get_recording(self, recording_id: str) -> Optional[Dict[str, Any]]:
        if recording_id in self.completed_recordings:
            return self._format_recording(self.completed_recordings[recording_id])
        
        for rec in self.active_recordings.values():
            if rec.id == recording_id:
                return self._format_recording(rec)
        
        return None
    
    def _format_recording(self, recording: Recording) -> Dict[str, Any]:
        return {
            "id": recording.id,
            "user_id": recording.metadata.user_id,
            "start_time": recording.metadata.start_time,
            "end_time": recording.metadata.end_time,
            "duration_ms": recording.metadata.duration_ms,
            "format": recording.metadata.format.value,
            "file_size_bytes": recording.metadata.file_size_bytes,
            "transcript_count": len(recording.metadata.transcript),
            "transcript": recording.metadata.transcript,
            "sentiment_timeline": recording.metadata.sentiment_timeline,
            "tags": recording.metadata.tags,
            "notes": recording.metadata.notes,
            "has_audio": recording.audio_data is not None
        }
    
    def list_recordings(self, user_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        recordings = []
        
        for rec in self.completed_recordings.values():
            if user_id is None or rec.metadata.user_id == user_id:
                recordings.append(self._format_recording(rec))
        
        recordings.sort(key=lambda x: x["start_time"], reverse=True)
        
        return recordings[:limit]
    
    def delete_recording(self, recording_id: str) -> bool:
        if recording_id in self.completed_recordings:
            del self.completed_recordings[recording_id]
            return True
        return False
    
    def get_audio_base64(self, recording_id: str) -> Optional[str]:
        if recording_id in self.completed_recordings:
            rec = self.completed_recordings[recording_id]
            if rec.audio_data:
                return base64.b64encode(rec.audio_data).decode()
        return None
    
    def export_recording(self, recording_id: str, format: str = "wav") -> Optional[Dict[str, Any]]:
        if recording_id not in self.completed_recordings:
            return None
        
        rec = self.completed_recordings[recording_id]
        
        if format == "wav" and rec.audio_data:
            wav_data = self._create_wav_header(len(rec.audio_data)) + rec.audio_data
            return {
                "format": "wav",
                "data": base64.b64encode(wav_data).decode(),
                "size_bytes": len(wav_data)
            }
        
        return None
    
    def _create_wav_header(self, data_size: int) -> bytes:
        sample_rate = 24000
        channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        chunk_size = 36 + data_size
        
        header = struct.pack('<4sI4s', b'RIFF', chunk_size, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        header += struct.pack('<4sI', b'data', data_size)
        
        return header
    
    def get_recording_stats(self, user_id: int = None) -> Dict[str, Any]:
        recordings = self.list_recordings(user_id)
        
        total_duration_ms = sum(r["duration_ms"] for r in recordings)
        total_size = sum(r["file_size_bytes"] for r in recordings)
        
        return {
            "total_recordings": len(recordings),
            "total_duration_sec": round(total_duration_ms / 1000, 1),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "avg_duration_sec": round(total_duration_ms / len(recordings) / 1000, 1) if recordings else 0,
            "active_recordings": len(self.active_recordings)
        }
    
    def search_transcripts(self, query: str, user_id: int = None) -> List[Dict[str, Any]]:
        results = []
        query_lower = query.lower()
        
        for rec in self.completed_recordings.values():
            if user_id and rec.metadata.user_id != user_id:
                continue
            
            for entry in rec.metadata.transcript:
                if query_lower in entry["text"].lower():
                    results.append({
                        "recording_id": rec.id,
                        "start_time": rec.metadata.start_time,
                        "text": entry["text"],
                        "speaker": entry["speaker"],
                        "offset_ms": entry["offset_ms"]
                    })
        
        return results[:20]
    
    def get_transcript_with_timestamps(self, recording_id: str) -> List[Dict[str, Any]]:
        if recording_id not in self.completed_recordings:
            return []
        
        rec = self.completed_recordings[recording_id]
        return rec.metadata.transcript
    
    def add_speaker_label(self, recording_id: str, speaker: str, start_ms: int, end_ms: int):
        if recording_id not in self.completed_recordings:
            return
        
        rec = self.completed_recordings[recording_id]
        
        for entry in rec.metadata.transcript:
            if entry["offset_ms"] >= start_ms and entry["offset_ms"] <= end_ms:
                entry["speaker"] = speaker
    
    def get_active_recording_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        if user_id not in self.active_recordings:
            return None
        
        rec = self.active_recordings[user_id]
        current_duration = (time.time() - rec.metadata.start_time) * 1000
        
        return {
            "recording_id": rec.id,
            "status": "recording",
            "duration_ms": current_duration,
            "chunks_count": len(rec.audio_chunks),
            "estimated_size_bytes": sum(len(c) for c in rec.audio_chunks)
        }
    
    def merge_recordings(self, recording_ids: List[str]) -> Optional[str]:
        if not recording_ids:
            return None
        
        first = self.completed_recordings.get(recording_ids[0])
        if not first:
            return None
        
        merged_chunks = list(first.audio_chunks)
        merged_transcript = list(first.metadata.transcript)
        
        for rid in recording_ids[1:]:
            rec = self.completed_recordings.get(rid)
            if rec:
                merged_chunks.extend(rec.audio_chunks)
                merged_transcript.extend(rec.metadata.transcript)
        
        new_id = f"merged_{int(time.time() * 1000)}"
        new_metadata = RecordingMetadata(
            recording_id=new_id,
            user_id=first.metadata.user_id,
            start_time=first.metadata.start_time,
            format=first.metadata.format
        )
        
        new_recording = Recording(
            id=new_id,
            metadata=new_metadata,
            audio_chunks=merged_chunks
        )
        
        if merged_chunks:
            new_recording.audio_data = self._merge_chunks(merged_chunks)
            new_metadata.file_size_bytes = len(new_recording.audio_data)
        
        new_metadata.transcript = sorted(merged_transcript, key=lambda x: x["offset_ms"])
        
        self.completed_recordings[new_id] = new_recording
        return new_id


class MediaStreamRecorder:
    def __init__(self):
        self.recorders: Dict[int, CallRecorder] = {}
    
    def get_recorder(self, user_id: int) -> CallRecorder:
        if user_id not in self.recorders:
            self.recorders[user_id] = CallRecorder()
        return self.recorders[user_id]


call_recorder = CallRecorder()