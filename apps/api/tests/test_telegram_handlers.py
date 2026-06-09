"""Telegram agent / copycat / automation handler tests."""

import types

import pytest

from app.integrations.telegram import bot as bot_mod
from app.integrations.telegram.profiles import STEP_COMPLETE, profile_store
from app.integrations.telegram.services.agents import resolve_agent_id, set_agent_for_profile
from app.integrations.telegram.services.copycat import run_copycat_subcommand


class _FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append({"text": text, **kwargs})


class _FakeUser:
    id = 9001
    username = "tester"
    first_name = "Test"
    last_name = "User"


class _FakeUpdate:
    message = _FakeMessage()
    effective_user = _FakeUser()


@pytest.mark.asyncio
async def test_agent_lists_builtin_agents(monkeypatch, tmp_path):
    from app.integrations.telegram import auth_store as astore_mod

    astore = astore_mod.TelegramAuthStore(str(tmp_path / "u.json"))
    prof_store = profile_store.__class__(str(tmp_path / "p.json"))
    astore.create_or_link_google(telegram_id=9001, email="a@test.com", full_name="Test User")
    p = prof_store.get(9001)
    p.step = STEP_COMPLETE
    prof_store.save(p)

    monkeypatch.setattr(bot_mod, "auth_store", astore)
    monkeypatch.setattr(bot_mod, "profile_store", prof_store)

    from app.integrations.telegram.handlers.agents import AgentHandlers

    bot = bot_mod.TelegramBot()
    await AgentHandlers(bot).cmd_agent(_FakeUpdate(), types.SimpleNamespace(args=[]))

    body = _FakeUpdate.message.replies[0]["text"]
    assert "Available agents" in body
    assert "`coding`" in body


def test_set_agent_and_resolve(tmp_path):
    prof_store = profile_store.__class__(str(tmp_path / "p.json"))
    profile = prof_store.get(42)
    ok, msg = set_agent_for_profile(profile, "academic")
    assert ok
    assert "academic" in msg
    assert resolve_agent_id(profile) == "academic"

    ok, _ = set_agent_for_profile(profile, "default")
    assert ok
    assert profile.selected_agent_id == ""


@pytest.mark.asyncio
async def test_copycat_help():
    msg = await run_copycat_subcommand([])
    assert "/copycat record" in msg


@pytest.mark.asyncio
async def test_copycat_list_mock_registry(monkeypatch):
    class _Result:
        success = True
        data = {"recordings": [{"name": "demo_flow"}]}
        error = ""

    class _Registry:
        async def execute(self, *_a, **_k):
            return _Result()

    monkeypatch.setattr(
        "app.integrations.telegram.services.copycat.get_registry",
        lambda: _Registry(),
    )
    msg = await run_copycat_subcommand(["list"])
    assert "demo_flow" in msg
