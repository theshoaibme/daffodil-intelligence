"""Tests for mode-based system prompts."""

from app.prompts.modes import active_modes, build_mode_system_prompt, mode_status_messages


def test_default_chat_mode():
    prompt = build_mode_system_prompt(None, routing="groq_fast", model_id="llama-3.1-8b-instant", engine="groq")
    assert "MODE: CHAT" in prompt
    assert "llama-3.1-8b-instant" in prompt


def test_planning_mode_overlay():
    prompt = build_mode_system_prompt(
        {"selected_tools": ["Planning"]},
        routing="default",
        model_id="llama-3.1-8b-instant",
        engine="groq",
    )
    assert "MODE: PLANNING" in prompt
    assert active_modes({"selected_tools": ["Planning"]}) == ["Planning"]


def test_status_messages():
    lines = mode_status_messages(
        {"selected_tools": ["Research"]},
        routing="groq_fast",
        model_id="llama-3.1-8b-instant",
        engine="groq",
    )
    assert any("Research" in line for line in lines)
    assert any("llama" in line for line in lines)
