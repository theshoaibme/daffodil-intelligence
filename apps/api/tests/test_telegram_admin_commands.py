"""Telegram agent/skill/automation/runtime command handlers."""

import types

import pytest

from app.integrations.telegram import bot as bot_mod
from app.integrations.telegram.profiles import STEP_COMPLETE, profile_store


class _FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)
        return types.SimpleNamespace(edit_text=self._edit)

    async def _edit(self, text, **kwargs):
        self.replies.append(text)


def _make_user(uid=9100):
    return types.SimpleNamespace(
        id=uid, username="tester", first_name="Test", last_name="User"
    )


class _FakeUpdate:
    def __init__(self, uid=9100):
        self.message = _FakeMessage()
        self.effective_user = _make_user(uid)


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.database._use_mock", True)
    from app.skills.store import _memory
    from app.agents import builder

    _memory.reset()
    monkeypatch.setattr(builder, "AGENT_REGISTRY", {})

    from app.integrations.telegram import auth_store as astore_mod

    astore = astore_mod.TelegramAuthStore(str(tmp_path / "u.json"))
    astore.create_or_link_google(telegram_id=9100, email="a@test.com", full_name="Test User")
    prof_store = profile_store.__class__(str(tmp_path / "p.json"))
    p = prof_store.get(9100)
    p.step = STEP_COMPLETE
    prof_store.save(p)

    monkeypatch.setattr(bot_mod, "auth_store", astore)
    monkeypatch.setattr(bot_mod, "profile_store", prof_store)
    monkeypatch.setattr("app.integrations.telegram.auth_store.auth_store", astore)

    from app.automation.store import AutomationStore

    auto = AutomationStore(path=tmp_path / "auto.json")
    monkeypatch.setattr("app.integrations.telegram.services.automation_admin.automation_store", auto)
    yield


def _ctx(*args):
    return types.SimpleNamespace(args=list(args), user_data={})


@pytest.mark.asyncio
async def test_create_and_list_agent():
    from app.integrations.telegram.handlers.agents import AgentHandlers

    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    ctx = types.SimpleNamespace(args="Thesis | research aid | You help write theses.".split())
    await AgentHandlers(bot).cmd_createagent(upd, ctx)
    assert any("Created agent" in r for r in upd.message.replies)

    upd2 = _FakeUpdate()
    await AgentHandlers(bot).cmd_agents(upd2, _ctx())
    assert any("Thesis" in r for r in upd2.message.replies)


@pytest.mark.asyncio
async def test_create_skill_and_list():
    from app.integrations.telegram.handlers.skills import SkillHandlers

    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    ctx = types.SimpleNamespace(args="Notes | use store_note | store_note,recall_notes".split())
    await SkillHandlers(bot).cmd_createskill(upd, ctx)
    assert any("Created skill" in r for r in upd.message.replies)

    upd2 = _FakeUpdate()
    await SkillHandlers(bot).cmd_skills(upd2, _ctx())
    assert any("Notes" in r for r in upd2.message.replies)


@pytest.mark.asyncio
async def test_assign_skills_to_agent():
    from app.integrations.telegram.handlers.agents import AgentHandlers
    from app.integrations.telegram.handlers.skills import SkillHandlers
    from app.agents.builder import list_agents
    from app.skills.store import skill_store

    bot = bot_mod.TelegramBot()
    await AgentHandlers(bot).cmd_createagent(
        _FakeUpdate(), types.SimpleNamespace(args="Aide | desc | prompt".split())
    )
    agent_id = list_agents()[0].id
    sk = skill_store.create("S", "d", "content", tool_names=["store_note"], created_by=9100, is_public=True)

    upd = _FakeUpdate()
    await SkillHandlers(bot).cmd_agentskills(upd, _ctx(agent_id, sk.id))
    assert any("Assigned" in r for r in upd.message.replies)


@pytest.mark.asyncio
async def test_create_loop_and_hook():
    from app.integrations.telegram.handlers.automation import AutomationHandlers

    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    await AutomationHandlers(bot).cmd_loop(upd, types.SimpleNamespace(args="30 | summarize my day".split()))
    assert any("Created loop" in r for r in upd.message.replies)

    upd2 = _FakeUpdate()
    await AutomationHandlers(bot).cmd_createhook(
        upd2, _ctx("on_login", "message", "|", "Welcome", "back")
    )
    assert any("Created hook" in r for r in upd2.message.replies)

    upd3 = _FakeUpdate()
    await AutomationHandlers(bot).cmd_automate(upd3, _ctx())
    body = "\n".join(upd3.message.replies)
    assert "Loops" in body and "Hooks" in body


@pytest.mark.asyncio
async def test_tools_and_mcp():
    from app.integrations.telegram.handlers.runtime import RuntimeHandlers

    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    await RuntimeHandlers(bot).cmd_tools(upd, _ctx())
    assert any("Tools" in r for r in upd.message.replies)

    upd2 = _FakeUpdate()
    await RuntimeHandlers(bot).cmd_mcp(upd2, _ctx())
    assert any("MCP" in r for r in upd2.message.replies)


@pytest.mark.asyncio
async def test_flow_and_logs_empty():
    from app.integrations.telegram.handlers.runtime import RuntimeHandlers

    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    await RuntimeHandlers(bot).cmd_flow(upd, _ctx())
    assert any("flow" in r.lower() for r in upd.message.replies)

    upd2 = _FakeUpdate()
    await RuntimeHandlers(bot).cmd_logs(upd2, _ctx())
    assert any("logs" in r.lower() for r in upd2.message.replies)


@pytest.mark.asyncio
async def test_shell_requires_admin(monkeypatch):
    from app.integrations.telegram.handlers.runtime import RuntimeHandlers

    bot = bot_mod.TelegramBot()
    # No admin ids configured -> denied
    upd = _FakeUpdate()
    await RuntimeHandlers(bot).cmd_shell(upd, _ctx("ls"))
    assert any("restricted to admins" in r for r in upd.message.replies)


@pytest.mark.asyncio
async def test_shell_admin_prompts_confirm(monkeypatch):
    from app.integrations.telegram.handlers.runtime import RuntimeHandlers

    monkeypatch.setattr(bot_mod.settings, "TELEGRAM_ADMIN_USER_IDS", "9100", raising=False)
    bot = bot_mod.TelegramBot()
    upd = _FakeUpdate()
    ctx = _ctx("echo", "hi")
    await RuntimeHandlers(bot).cmd_shell(upd, ctx)
    assert ctx.user_data.get("pending_shell") == "echo hi"
    assert any("Run this command" in r for r in upd.message.replies)
