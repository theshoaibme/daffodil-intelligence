"""Resolve voice attachments in chat metadata into transcribed user text."""

from __future__ import annotations

import base64
import logging
from typing import Any, Optional, Tuple

from .stt import transcribe_audio_bytes_async

logger = logging.getLogger(__name__)


def _decode_voice_payload(payload: dict) -> Tuple[bytes, str]:
    raw = payload.get("data") or payload.get("audio") or ""
    if isinstance(raw, str):
        if "," in raw and raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        audio_bytes = base64.b64decode(raw)
    elif isinstance(raw, (bytes, bytearray)):
        audio_bytes = bytes(raw)
    else:
        raise ValueError("Voice payload missing base64 data")

    mime_type = (
        payload.get("mime_type")
        or payload.get("mimeType")
        or "audio/webm"
    )
    return audio_bytes, str(mime_type)


def _extract_voice_payload(metadata: Optional[dict]) -> Optional[dict]:
    if not metadata:
        return None

    voice = metadata.get("voice")
    if isinstance(voice, dict) and (voice.get("data") or voice.get("audio")):
        return voice

    attachments = metadata.get("attachments")
    if isinstance(attachments, list):
        for item in attachments:
            if not isinstance(item, dict):
                continue
            kind = (item.get("kind") or item.get("type") or "").lower()
            if kind in ("voice", "audio") or item.get("voice_message"):
                return item

    return None


async def resolve_voice_message(
    content: str,
    metadata: Optional[dict],
) -> Tuple[str, dict]:
    """
    If metadata includes a voice recording, transcribe it and use the text as the user message.
    Stores transcript details in metadata for debugging; strips raw audio before pipeline.
    """
    meta = dict(metadata or {})
    payload = _extract_voice_payload(meta)
    if not payload:
        return content, meta

    try:
        audio_bytes, mime_type = _decode_voice_payload(payload)
    except Exception as exc:
        logger.warning("Invalid voice payload: %s", exc)
        raise ValueError("Invalid voice message data") from exc

    result = await transcribe_audio_bytes_async(audio_bytes, mime_type)
    transcript = (result.text or "").strip()
    if not transcript:
        raise ValueError("Could not transcribe voice message")

    meta["voice_transcript"] = {
        "text": transcript,
        "language": result.language,
        "confidence": result.confidence,
        "duration_sec": result.duration_sec,
        "processing_ms": result.processing_ms,
        "mime_type": mime_type,
    }
    if payload.get("duration_ms") is not None:
        meta["voice_transcript"]["recording_duration_ms"] = payload.get("duration_ms")

    meta.pop("voice", None)
    if isinstance(meta.get("attachments"), list):
        meta["attachments"] = [
            a
            for a in meta["attachments"]
            if not (
                isinstance(a, dict)
                and (
                    (a.get("kind") or a.get("type") or "").lower() in ("voice", "audio")
                    or a.get("voice_message")
                )
            )
        ]
        if not meta["attachments"]:
            meta.pop("attachments")

    return transcript, meta
