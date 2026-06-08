"""Telegram bot handler tests (no real Telegram connection)."""

import types

import pytest

from app.integrations.telegram import telegram_bot
from app.integrations.telegram.profiles import STEP_COMPLETE, STEP_REGISTER_EMAIL, STEP_REGISTER_OTP
from app.integrations.telegram.otp import otp_service
from app.integrations.telegram.tokens import sign_state, verify_state


class _FakeChat:
    async def send_action(self, *_):
        return None


class _FakeMessage:
    def __init__(self, text="hello"):
        self.text = text
        self.caption = None
        self.replies = []
        self.chat = _FakeChat()

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class _FakeUser:
    id = 4242
    username = "testuser"
    first_name = "Test"
    last_name = "User"
    full_name = "Test User"


class _FakeUpdate:
    def __init__(self, text="hello"):
        self.message = _FakeMessage(text)
        self.effective_user = _FakeUser()


async def test_text_handler_routes_through_orchestrator(monkeypatch, tmp_path):
    import app.runtime.orchestrator as orch
    from app.integrations.telegram import auth_store as astore_mod
    from app.integrations.telegram import profiles as prof_mod

    astore = astore_mod.TelegramAuthStore(str(tmp_path / "users.json"))
    prof_store = prof_mod.TelegramProfileStore(str(tmp_path / "profiles.json"))
    monkeypatch.setattr(astore_mod, "auth_store", astore)
    monkeypatch.setattr("app.integrations.telegram.bot.auth_store", astore)
    monkeypatch.setattr(prof_mod, "profile_store", prof_store)
    monkeypatch.setattr("app.integrations.telegram.bot.profile_store", prof_store)

    astore.create_email_account(
        telegram_id=4242,
        email="test@diu.edu.bd",
        password="secret12",
        full_name="Test User",
        first_name="Test",
        last_name="User",
        username="testuser",
        phone="",
        role="student",
        student_id="221-15-1234",
        department="CSE",
    )
    p = prof_store.get(4242)
    p.step = STEP_COMPLETE
    prof_store.save(p)

    async def fake_run(text, **kwargs):
        return {"content": f"answer to: {text}", "tool_calls": []}

    monkeypatch.setattr(orch, "run", fake_run)

    update = _FakeUpdate("what is my cgpa?")
    ctx = types.SimpleNamespace(bot=None, args=[])
    await telegram_bot._on_text(update, ctx)

    assert update.message.replies
    assert "answer to:" in update.message.replies[0]
    assert "test@diu.edu.bd" in update.message.replies[0]


def test_bot_disabled_when_not_configured(monkeypatch):
    from app.core.config import get_settings
    s = get_settings()
    monkeypatch.setattr(s, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(s, "TELEGRAM_BOT_TOKEN", "")
    assert telegram_bot.enabled is False


def test_allowed_list(monkeypatch):
    from app.core.config import get_settings
    s = get_settings()
    monkeypatch.setattr(s, "TELEGRAM_ALLOWED_USER_IDS", "111,222")
    assert telegram_bot._allowed(111) is True
    assert telegram_bot._allowed(999) is False


async def test_start_shows_auth_menu(monkeypatch, tmp_path):
    from app.integrations.telegram import auth_store as astore_mod
    from app.integrations.telegram import profiles as prof_mod

    astore = astore_mod.TelegramAuthStore(str(tmp_path / "users.json"))
    prof_store = prof_mod.TelegramProfileStore(str(tmp_path / "profiles.json"))
    monkeypatch.setattr(astore_mod, "auth_store", astore)
    monkeypatch.setattr("app.integrations.telegram.bot.auth_store", astore)
    monkeypatch.setattr(prof_mod, "profile_store", prof_store)
    monkeypatch.setattr("app.integrations.telegram.bot.profile_store", prof_store)

    update = _FakeUpdate()
    ctx = types.SimpleNamespace(bot=None, args=[])
    await telegram_bot._cmd_start(update, ctx)

    assert "Daffodil Intelligence" in update.message.replies[0]
    assert "JARVIS" not in update.message.replies[0].upper()


async def test_registration_email_otp_flow(monkeypatch, tmp_path):
    from app.integrations.telegram import auth_store as astore_mod
    from app.integrations.telegram import profiles as prof_mod

    astore = astore_mod.TelegramAuthStore(str(tmp_path / "users.json"))
    prof_store = prof_mod.TelegramProfileStore(str(tmp_path / "profiles.json"))
    monkeypatch.setattr(astore_mod, "auth_store", astore)
    monkeypatch.setattr("app.integrations.telegram.bot.auth_store", astore)
    monkeypatch.setattr(prof_mod, "profile_store", prof_store)
    monkeypatch.setattr("app.integrations.telegram.bot.profile_store", prof_store)

    update = _FakeUpdate()
    ctx = types.SimpleNamespace(bot=None, args=[])

    # role callback
    class _FakeQuery:
        data = "role:student"
        async def answer(self):
            pass
        async def edit_message_text(self, text, **kwargs):
            update.message.replies.append(text)

    update.callback_query = _FakeQuery()
    p = prof_store.get(4242)
    p.step = prof_mod.STEP_REGISTER_ROLE
    p.mode = "register"
    prof_store.save(p)
    await telegram_bot._on_role_callback(update, ctx)
    assert "phone" in update.message.replies[-1].lower()

    update.message.text = "+8801712345678"
    await telegram_bot._on_text(update, ctx)
    assert "email" in update.message.replies[-1].lower()

    update.message.text = "newuser@diu.edu.bd"
    await telegram_bot._on_text(update, ctx)
    assert prof_store.get(4242).step == STEP_REGISTER_OTP

    code = otp_service.generate("newuser@diu.edu.bd")
    update.message.text = code
    await telegram_bot._on_text(update, ctx)
    assert "password" in update.message.replies[-1].lower()

    update.message.text = "mypass123"
    await telegram_bot._on_text(update, ctx)
    assert "student id" in update.message.replies[-1].lower()

    update.message.text = "221-15-9999"
    await telegram_bot._on_text(update, ctx)
    update.message.text = "CSE"
    await telegram_bot._on_text(update, ctx)

    assert "Registration complete" in update.message.replies[-1]
    acct = astore.get_by_telegram_id(4242)
    assert acct and acct.email == "newuser@diu.edu.bd"


def test_oauth_state_token_roundtrip():
    token = sign_state(12345)
    assert verify_state(token) == 12345
