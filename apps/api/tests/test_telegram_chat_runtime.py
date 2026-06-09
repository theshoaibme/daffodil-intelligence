"""Telegram full agent runtime bridge tests."""

import types

import pytest

from app.integrations.telegram.auth_store import TelegramAccount, auth_store as global_auth_store
from app.integrations.telegram.services.chat_runtime import (
    build_turn_metadata,
    build_telegram_turn,
    is_known_agent_id,
    is_simple_greeting,
    telegram_model_id,
)
from app.integrations.telegram.web_auth import parse_web_user_id, resolve_runtime_user_id
from app.automation import telegram_notify


def test_parse_web_user_id():
    acct = TelegramAccount(user_id="web:42", telegram_id=9, email="a@b.com", full_name="A")
    assert parse_web_user_id(acct) == 42
    assert parse_web_user_id(None) is None


def test_resolve_runtime_user_id_prefers_web():
    acct = TelegramAccount(user_id="web:7", telegram_id=99, email="a@b.com", full_name="A")
    assert resolve_runtime_user_id(99, acct) == 7
    assert resolve_runtime_user_id(99, None) == 99


def test_build_turn_metadata_enables_mcp_and_agent(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "MCP_ENABLED", True)
    acct = TelegramAccount(
        user_id="web:1",
        telegram_id=5,
        email="s@diu.edu.bd",
        full_name="S",
        student_id="221-15-1",
        department="CSE",
    )
    meta = build_turn_metadata(telegram_id=5, account=acct, agent_id="coding")
    assert meta["student_id"] == "221-15-1"
    assert meta["telegram_chat_id"] == 5
    assert meta["channel"] == "telegram"
    assert "MCP" in meta["selected_tools"]
    assert "Agent" in meta["selected_tools"]


def test_telegram_model_id_defaults_to_auto(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "TELEGRAM_CHAT_MODEL", "auto")
    assert telegram_model_id() is None


def test_is_simple_greeting():
    assert is_simple_greeting("Hello!")
    assert is_simple_greeting("hi")
    assert not is_simple_greeting("Amar vlo lagteche na")
    assert not is_simple_greeting("hello how are you")


def test_build_telegram_turn_returns_runtime_user(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "TELEGRAM_CHAT_MODEL", "gemini-2.0-flash-lite")
    acct = TelegramAccount(user_id="web:3", telegram_id=8, email="x@y.com", full_name="X")
    uid, meta, model_id, turn_index = build_telegram_turn(
        telegram_id=8,
        account=acct,
        agent_id="main",
        chat_id="tg-8",
    )
    assert uid == 3
    assert meta["telegram_chat_id"] == 8
    assert model_id == "gemini-2.0-flash-lite"
    assert turn_index == 1


def test_is_known_agent_id_builtin():
    assert is_known_agent_id("coding")
    assert not is_known_agent_id("not-a-real-agent-id-xyz")


@pytest.mark.asyncio
async def test_resolve_telegram_chat_id_from_telegram_user(tmp_path, monkeypatch):
    store = global_auth_store.__class__(str(tmp_path / "tg_users.json"))
    store.save(
        TelegramAccount(
            user_id="web:10",
            telegram_id=424242,
            email="tg@diu.edu.bd",
            full_name="TG",
        )
    )
    monkeypatch.setattr("app.integrations.telegram.auth_store.auth_store", store)
    chat_id = await telegram_notify.resolve_telegram_chat_id_for_user(424242)
    assert chat_id == 424242
