"""Tests for fast Groq vs full Antigravity routing."""

from app.runtime.agent_factory import AgentPersona
from app.runtime.chat_router import groq_model_for_routing, should_use_fast_groq


def test_simple_chat_uses_fast_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_FAST_CHAT", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    assert should_use_fast_groq(
        routing="default",
        was_auto=True,
        agent_id="main",
        persona=AgentPersona.MAIN,
    )


def test_code_routing_uses_full_runtime(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_FAST_CHAT", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    assert not should_use_fast_groq(
        routing="code",
        was_auto=True,
        agent_id="main",
        persona=AgentPersona.MAIN,
    )


def test_agent_mode_uses_full_runtime(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_FAST_CHAT", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    assert not should_use_fast_groq(
        routing="default",
        was_auto=True,
        metadata={"selected_tools": ["Agent"]},
        agent_id="main",
        persona=AgentPersona.MAIN,
    )


def test_groq_model_for_simple_routing(monkeypatch):
    monkeypatch.setenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
    from app.core.config import get_settings

    get_settings.cache_clear()

    assert groq_model_for_routing("fast_simple") == "llama-3.1-8b-instant"
