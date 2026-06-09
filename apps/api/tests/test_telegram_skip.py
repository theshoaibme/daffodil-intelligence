"""Telegram /skip registration command tests."""

import types

import pytest

from app.integrations.telegram import bot as bot_mod
from app.integrations.telegram import profiles as prof_mod
from app.integrations.telegram.profiles import (
    STEP_REGISTER_DEPARTMENT,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_ROLE,
    profile_store,
)
from app.integrations.telegram.services.registration import SKIP_HELP_TEXT, is_skippable_step


class _FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class _FakeUser:
    id = 5555
    username = "skipper"
    first_name = "Skip"
    last_name = "Test"


class _FakeUpdate:
    message = _FakeMessage()
    effective_user = _FakeUser()


def test_skip_help_lists_optional_fields():
    assert "Phone number" in SKIP_HELP_TEXT
    assert "Student ID" in SKIP_HELP_TEXT
    assert "Department" in SKIP_HELP_TEXT
    assert "Cannot be skipped" in SKIP_HELP_TEXT


def test_skippable_steps():
    assert is_skippable_step(STEP_REGISTER_PHONE)
    assert not is_skippable_step(STEP_REGISTER_ROLE)


def _patch_profile_store(monkeypatch, prof_store):
    monkeypatch.setattr(prof_mod, "profile_store", prof_store)
    monkeypatch.setattr(bot_mod, "profile_store", prof_store)
    monkeypatch.setattr(
        "app.integrations.telegram.handlers.registration.profile_store",
        prof_store,
    )


@pytest.mark.asyncio
async def test_skip_command_shows_help_outside_registration(tmp_path, monkeypatch):
    prof_store = profile_store.__class__(str(tmp_path / "p.json"))
    _patch_profile_store(monkeypatch, prof_store)
    prof_store.get(5555).step = STEP_REGISTER_ROLE

    from app.integrations.telegram.handlers.registration import RegistrationHandlers

    await RegistrationHandlers(bot_mod.TelegramBot()).cmd_skip(
        _FakeUpdate(), types.SimpleNamespace()
    )
    assert "Optional registration fields" in _FakeUpdate.message.replies[0]


@pytest.mark.asyncio
async def test_skip_command_advances_phone_step(tmp_path, monkeypatch):
    prof_store = profile_store.__class__(str(tmp_path / "p.json"))
    _patch_profile_store(monkeypatch, prof_store)
    profile = prof_store.get(5555)
    profile.step = STEP_REGISTER_PHONE
    profile.role = "teacher"
    prof_store.save(profile)

    from app.integrations.telegram.handlers.registration import RegistrationHandlers

    await RegistrationHandlers(bot_mod.TelegramBot()).cmd_skip(
        _FakeUpdate(), types.SimpleNamespace()
    )
    assert prof_store.get(5555).step == STEP_REGISTER_DEPARTMENT
    assert "Skipped" in _FakeUpdate.message.replies[-1]
    assert "department" in _FakeUpdate.message.replies[0].lower()
