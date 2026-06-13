"""Tests for voice STT service and chat voice resolution."""

import base64
import uuid

import pytest

pytest.importorskip("fastapi")


@pytest.fixture()
def mock_transcribe(monkeypatch):
    from app.voice import stt as stt_module

    async def fake_async(audio_bytes: bytes, mime_type: str = "audio/webm"):
        return stt_module.TranscriptionResult(
            text="Hello from voice",
            language="en",
            confidence=0.95,
            duration_sec=1.2,
            processing_ms=42.0,
        )

    monkeypatch.setattr(stt_module, "transcribe_audio_bytes_async", fake_async)
    return fake_async


def test_transcribe_mock_mode(monkeypatch):
    from app.core.config import get_settings
    from app.voice.stt import transcribe_audio_bytes

    get_settings.cache_clear()
    monkeypatch.setenv("WHISPER_MOCK", "true")

    result = transcribe_audio_bytes(b"\x00\x01", "audio/webm")
    assert result.text == "[mock transcription]"
    assert result.language == "en"

    get_settings.cache_clear()


def test_resolve_voice_message_transcribes(mock_transcribe):
    from conftest import run_async
    from app.voice.chat_voice import resolve_voice_message

    async def _run():
        payload = {
            "data": base64.b64encode(b"fake-audio").decode(),
            "mime_type": "audio/webm",
            "duration_ms": 1500,
        }
        return await resolve_voice_message("", {"voice": payload})

    content, meta = run_async(_run())

    assert content == "Hello from voice"
    assert meta["voice_transcript"]["text"] == "Hello from voice"
    assert meta["voice_transcript"]["language"] == "en"
    assert "voice" not in meta


def test_resolve_voice_message_passthrough_without_voice():
    from conftest import run_async
    from app.voice.chat_voice import resolve_voice_message

    content, meta = run_async(resolve_voice_message("plain text", {"channel": "chat"}))
    assert content == "plain text"
    assert "voice_transcript" not in meta


@pytest.fixture()
def chat_client(monkeypatch, mock_transcribe):
    pytest.importorskip("jose")
    import app.api.chat as chat_module

    async def fake_stream(message, **kwargs):
        yield {"type": "content", "content": f"echo: {message}"}

    monkeypatch.setattr(chat_module, "run_turn_stream", fake_stream)

    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client


@pytest.fixture()
def auth_headers(chat_client):
    email = f"voice-test-{uuid.uuid4().hex[:12]}@example.com"
    password = "testpass123"
    res = chat_client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Voice Test"},
    )
    assert res.status_code == 200, res.text
    res = chat_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_voice_message_streams_transcribed_text(chat_client, auth_headers):
    res = chat_client.post(
        "/api/chats/",
        json={"title": "Voice", "agent_type": "supervisor"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    chat_id = res.json()["id"]

    voice_b64 = base64.b64encode(b"fake-webm-audio").decode()
    res = chat_client.post(
        f"/api/chats/{chat_id}/messages",
        json={
            "content": "",
            "metadata": {
                "voice": {
                    "data": voice_b64,
                    "mime_type": "audio/webm",
                    "duration_ms": 800,
                }
            },
        },
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert "echo: Hello from voice" in res.text
    assert "[DONE]" in res.text
