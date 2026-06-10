"""Hugging Face chat helpers."""

from app.core.hf_models import is_hf_model, resolve_hf_model_id
from app.runtime.chat_router import should_use_hf_chat


def test_resolve_hf_model_id():
    assert resolve_hf_model_id("glm-5.1") == "zai-org/GLM-5.1"
    assert resolve_hf_model_id("zai-org/GLM-5.1") == "zai-org/GLM-5.1"


def test_is_hf_model():
    assert is_hf_model("glm-5.1")
    assert is_hf_model("zai-org/GLM-5.1")
    assert not is_hf_model("gpt-4o")


def test_should_use_hf_chat(monkeypatch):
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "hf-test")
    monkeypatch.setenv("HUGGINGFACE_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert should_use_hf_chat(model_id="glm-5.1", attachments=False, include_tools=None)
    assert not should_use_hf_chat(model_id="glm-5.1", attachments=True)
    assert not should_use_hf_chat(model_id="gpt-4o")
    assert not should_use_hf_chat(
        model_id="glm-5.1",
        metadata={"selected_tools": ["Agent"], "_message": "class routine Monday"},
    )
