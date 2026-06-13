"""Tests for versioned AI event envelopes."""

from app.schemas.ai_events import legacy_event_to_envelope, AiEventEnvelope


def test_legacy_content_maps_to_message_chunk():
    env = legacy_event_to_envelope(
        {"type": "content", "content": "hello"},
        session_id="42",
        turn_id="turn-1",
        seq=1,
    )
    assert env.type == "message.chunk"
    assert env.payload["content"] == "hello"
    assert env.legacy_type == "content"


def test_legacy_tool_success_maps_to_finished():
    env = legacy_event_to_envelope(
        {"type": "tool", "name": "search", "status": "success"},
        session_id="42",
        turn_id="turn-1",
        seq=2,
    )
    assert env.type == "tool.finished"
    assert env.payload["tool_name"] == "search"


def test_envelope_sse_dict_includes_legacy_fields():
    env = AiEventEnvelope(
        session_id="1",
        turn_id="t1",
        type="message.chunk",
        payload={"content": "hi"},
        legacy_type="content",
        seq=3,
    )
    data = env.to_sse_dict()
    assert data["type"] == "content"
    assert data["content"] == "hi"
