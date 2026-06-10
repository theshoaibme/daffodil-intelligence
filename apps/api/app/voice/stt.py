"""Speech-to-text via faster-whisper with automatic language detection."""

from __future__ import annotations

import logging
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)

_MIME_SUFFIX = {
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/ogg": ".ogg",
    "audio/opus": ".ogg",
}

_model = None
_model_lock = threading.Lock()


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    duration_sec: float
    processing_ms: float


def _suffix_for_mime(mime_type: str) -> str:
    base = (mime_type or "audio/webm").split(";")[0].strip().lower()
    return _MIME_SUFFIX.get(base, ".webm")


def _get_model():
    global _model
    with _model_lock:
        if _model is not None:
            return _model
        settings = get_settings()
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed; add it to requirements or set WHISPER_MOCK=true"
            ) from exc
        logger.info(
            "Loading Whisper model=%s device=%s compute_type=%s",
            settings.WHISPER_MODEL,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
        return _model


def _transcribe_file(path: Path) -> TranscriptionResult:
    settings = get_settings()
    if settings.WHISPER_MOCK:
        return TranscriptionResult(
            text="[mock transcription]",
            language="en",
            confidence=1.0,
            duration_sec=0.0,
            processing_ms=1.0,
        )

    start = time.perf_counter()
    model = _get_model()
    segments, info = model.transcribe(
        str(path),
        language=None,
        beam_size=5,
        vad_filter=True,
    )
    text = " ".join(seg.text.strip() for seg in segments if seg.text and seg.text.strip())
    elapsed_ms = (time.perf_counter() - start) * 1000
    return TranscriptionResult(
        text=text.strip(),
        language=getattr(info, "language", None) or "unknown",
        confidence=float(getattr(info, "language_probability", 0.0) or 0.0),
        duration_sec=float(getattr(info, "duration", 0.0) or 0.0),
        processing_ms=elapsed_ms,
    )


def transcribe_audio_bytes(audio_bytes: bytes, mime_type: str = "audio/webm") -> TranscriptionResult:
    """Transcribe raw audio bytes (webm, wav, mp3, ogg) with auto language detection."""
    if not audio_bytes:
        return TranscriptionResult(
            text="",
            language="unknown",
            confidence=0.0,
            duration_sec=0.0,
            processing_ms=0.0,
        )

    suffix = _suffix_for_mime(mime_type)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)

    try:
        return _transcribe_file(tmp_path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


async def transcribe_audio_bytes_async(
    audio_bytes: bytes, mime_type: str = "audio/webm"
) -> TranscriptionResult:
    import asyncio

    return await asyncio.to_thread(transcribe_audio_bytes, audio_bytes, mime_type)
