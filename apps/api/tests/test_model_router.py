"""Tests for Auto model routing heuristics."""

from app.core.model_router import resolve_model_for_turn
from app.core.models_catalog import AUTO_MODEL_ID


def test_manual_model_bypasses_auto():
    resolved, was_auto, reason = resolve_model_for_turn(
        model_id="gpt-4o",
        message="hello",
    )
    assert resolved == "gpt-4o"
    assert was_auto is False
    assert reason == "manual"


def test_auto_defaults_for_simple_message():
    from app.core.config import get_settings

    resolved, was_auto, reason = resolve_model_for_turn(
        model_id=AUTO_MODEL_ID,
        message="Tell me about the weather today.",
    )
    assert was_auto is True
    assert reason == "default"
    assert resolved == get_settings().ANTIGRAVITY_MODEL


def test_auto_picks_pro_for_reasoning():
    resolved, was_auto, reason = resolve_model_for_turn(
        model_id=AUTO_MODEL_ID,
        message="Please analyze step by step why this algorithm fails.",
    )
    assert was_auto is True
    assert reason == "reasoning"
    assert resolved == "gemini-2.5-pro"


def test_auto_picks_flash_for_code():
    resolved, was_auto, reason = resolve_model_for_turn(
        model_id=AUTO_MODEL_ID,
        message="Write a python function to sort a list.",
    )
    assert was_auto is True
    assert reason == "code"
    assert resolved == "gemini-2.5-flash"
