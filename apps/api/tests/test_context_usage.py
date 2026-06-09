"""Tests for chat context usage estimation."""

import pytest

from app.core.context_usage import (
    build_context_usage_payload,
    estimate_tokens,
    resolve_context_limit,
)


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_text():
    assert estimate_tokens("hello world") == 2


def test_resolve_context_limit_known_model():
    assert resolve_context_limit("gpt-4o") == 128_000


def test_build_context_usage_payload_ratio():
    payload = build_context_usage_payload(
        used_tokens=64_000,
        max_tokens=128_000,
        breakdown={"messages": 50_000, "draft": 0, "memory_recall": 10_000, "system_overhead": 4_000},
        message_count=8,
        model_id="gpt-4o",
    )
    assert payload["usage_ratio"] == 0.5
    assert payload["usage_percent"] == 50
    assert payload["used_tokens"] == 64_000
