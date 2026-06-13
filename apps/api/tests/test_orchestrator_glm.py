"""Antigravity vs GLM 5.1 orchestration routing."""

from app.core.hf_models import GLM_5_1_CATALOG_ID
from app.runtime.agent_factory import should_run_antigravity
from app.runtime.orchestrator import run


def test_glm_model_skips_antigravity_even_with_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    from app.core.config import get_settings
    import app.runtime.agent_factory as factory

    get_settings.cache_clear()
    monkeypatch.setattr(factory, "_ANTIGRAVITY_AVAILABLE", True)
    monkeypatch.setattr(factory.settings, "GEMINI_API_KEY", "test-gemini-key")
    assert factory.should_run_antigravity(GLM_5_1_CATALOG_ID) is False
    assert factory.should_run_antigravity("gemini-2.5-flash") is True


def test_glm_skips_antigravity_without_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert should_run_antigravity(GLM_5_1_CATALOG_ID) is False
    assert should_run_antigravity(None) is False


def test_orchestrator_uses_hf_for_glm_simple_chat(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "hf-test")
    monkeypatch.setenv("HUGGINGFACE_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    calls = []

    async def fake_hf_chat(message, *, extra_system=None, model=None):
        calls.append({"message": message, "model": model})
        return {"content": "glm reply", "tool_calls": [], "engine": "huggingface"}

    monkeypatch.setattr("app.runtime.hf_chat.chat", fake_hf_chat)
    monkeypatch.setattr("app.runtime.hf_chat.is_available", lambda: True)

    import asyncio

    result = asyncio.run(
        run("hello there", model=GLM_5_1_CATALOG_ID, metadata={"_message": "hello there"})
    )
    assert result["engine"] == "huggingface"
    assert result["content"] == "glm reply"
    assert calls and calls[0]["model"] == GLM_5_1_CATALOG_ID
