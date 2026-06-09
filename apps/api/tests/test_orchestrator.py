"""Orchestrator tests — antigravity path and legacy fallback (mocked)."""

import pytest

from app.runtime import orchestrator
from app.runtime.session_manager import session_manager


async def test_antigravity_path(monkeypatch):
    async def fake_chat(message, **kwargs):
        return {"content": f"echo:{message}", "tool_calls": ["t1"], "thoughts": [], "persona": "main"}

    monkeypatch.setattr(session_manager, "available", lambda: True)
    monkeypatch.setattr(session_manager, "chat", fake_chat)

    result = await orchestrator.run("hello", user_id=1, chat_id="c1")
    assert result["content"] == "echo:hello"
    assert result["engine"] == "antigravity"


async def test_fallback_to_legacy_on_error(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("agent down")

    monkeypatch.setattr(session_manager, "available", lambda: True)
    monkeypatch.setattr(session_manager, "chat", boom)

    # Patch the legacy supervisor functions so no network/LLM is used.
    import app.agents.supervisor as sup

    async def fake_process(message, agents, ctx=None):
        return {"general": "legacy answer"}

    async def fake_synth(results, msg, language=None):
        return "legacy answer"

    monkeypatch.setattr(sup, "detect_intent", lambda m: ["general"])
    monkeypatch.setattr(sup, "process_with_agents", fake_process)
    monkeypatch.setattr(sup, "synthesize_response", fake_synth)

    result = await orchestrator.run("hi", user_id=1, chat_id="c2")
    assert result["engine"] == "legacy"
    assert result["content"] == "legacy answer"


async def test_stream_antigravity(monkeypatch):
    async def fake_stream(message, **kwargs):
        for tok in ["Hel", "lo"]:
            yield tok

    monkeypatch.setattr(session_manager, "available", lambda: True)
    monkeypatch.setattr(session_manager, "stream", fake_stream)

    tokens = [t async for t in orchestrator.run_stream("x", user_id=1, chat_id="c3")]
    assert "".join(tokens) == "Hello"
