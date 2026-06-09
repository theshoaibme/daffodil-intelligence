"""Telegram auth store and OTP unit tests."""

import asyncio
from unittest.mock import AsyncMock, patch

from httpx import Response

from app.api.telegram_auth import google_callback
from app.integrations.telegram.auth_store import TelegramAuthStore
from app.integrations.telegram.otp import otp_service, OTPService
from app.integrations.telegram.tokens import sign_state


def test_otp_verify(tmp_path):
    svc = OTPService()
    code = svc.generate("user@test.com")
    assert svc.verify("user@test.com", code)
    assert not svc.verify("user@test.com", code)


def test_verify_login_with_names(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_email_account(
        telegram_id=1,
        email="a@b.com",
        password="pass1234",
        full_name="Alice Bee",
        first_name="Alice",
        last_name="Bee",
        username="ab",
        phone="",
        role="student",
        student_id="",
        department="",
    )
    assert store.verify_login_with_names("a@b.com", "pass1234", "Alice", "Bee")
    assert store.verify_login_with_names("a@b.com", "pass1234", "Wrong", "Bee") is None
    assert store.verify_login_with_names("a@b.com", "wrong", "Alice", "Bee") is None


def test_auth_store_email_login(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_email_account(
        telegram_id=1,
        email="a@b.com",
        password="pass1234",
        full_name="A B",
        first_name="A",
        last_name="B",
        username="ab",
        phone="",
        role="student",
        student_id="",
        department="",
    )
    assert store.verify_login("a@b.com", "pass1234")
    assert store.verify_login("a@b.com", "wrong") is None


def test_email_validation():
    assert otp_service.is_valid_email("good@diu.edu.bd")
    assert not otp_service.is_valid_email("not-an-email")


def test_detach_telegram_session_keeps_account(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_or_link_google(
        telegram_id=5187786663,
        email="user@test.com",
        full_name="Test User",
    )
    assert store.get_by_telegram_id(5187786663) is not None

    assert store.detach_telegram_session(5187786663) is True
    assert store.get_by_telegram_id(5187786663) is None
    assert store.get_by_email("user@test.com") is not None


def test_relink_removes_stale_telegram_id(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_email_account(
        telegram_id=111,
        email="user@diu.edu.bd",
        password="pass1234",
        full_name="User One",
        first_name="User",
        last_name="One",
        username="u1",
        phone="",
        role="student",
        student_id="",
        department="",
    )
    assert store.get_by_telegram_id(111) is not None

    store.link_telegram(222, "user@diu.edu.bd")

    assert store.get_by_telegram_id(222) is not None
    assert store.get_by_telegram_id(111) is None


def test_login_email_status(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    assert store.login_email_status("missing@test.com") == "not_found"

    store.create_or_link_google(telegram_id=1, email="g@test.com", full_name="G")
    assert store.login_email_status("g@test.com") == "google_only"

    store.create_email_account(
        telegram_id=2,
        email="e@test.com",
        password="secret12",
        full_name="E",
        first_name="E",
        last_name="",
        username="",
        phone="",
        role="student",
        student_id="",
        department="",
    )
    assert store.login_email_status("e@test.com") == "has_password"


def test_google_link_keeps_password_login(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_email_account(
        telegram_id=10,
        email="hybrid@test.com",
        password="secret12",
        full_name="Hybrid",
        first_name="H",
        last_name="",
        username="",
        phone="",
        role="student",
        student_id="",
        department="",
    )
    store.create_or_link_google(
        telegram_id=10,
        email="hybrid@test.com",
        full_name="Hybrid User",
        avatar_url="https://example.com/pic.jpg",
    )
    acct = store.get_by_email("hybrid@test.com")
    assert acct.auth_provider == "both"
    assert acct.avatar_url == "https://example.com/pic.jpg"
    assert store.verify_login("hybrid@test.com", "secret12")


def test_google_relink_removes_stale_telegram_id(tmp_path):
    store = TelegramAuthStore(str(tmp_path / "u.json"))
    store.create_or_link_google(
        telegram_id=333,
        email="google@diu.edu.bd",
        full_name="Google User",
    )
    assert store.get_by_telegram_id(333) is not None

    store.create_or_link_google(
        telegram_id=444,
        email="google@diu.edu.bd",
        full_name="Google User",
    )

    assert store.get_by_telegram_id(444) is not None
    assert store.get_by_telegram_id(333) is None


async def test_send_auth_welcome_two_messages():
    from app.integrations.telegram.bot import send_auth_welcome
    from app.integrations.telegram.auth_store import TelegramAccount

    class FakeBot:
        def __init__(self):
            self.calls = []

        async def send_photo(self, **kwargs):
            self.calls.append(("photo", kwargs))

        async def send_message(self, **kwargs):
            self.calls.append(("message", kwargs))

        async def get_user_profile_photos(self, *_args, **_kwargs):
            class P:
                total_count = 0
            return P()

    bot = FakeBot()
    account = TelegramAccount(
        user_id="u1",
        telegram_id=1,
        email="user@test.com",
        full_name="Test User",
    )
    await send_auth_welcome(bot, 1, account, photo_url="https://example.com/avatar.jpg", telegram_id=1)

    assert len(bot.calls) == 2
    assert bot.calls[0][0] == "photo"
    assert "Login successful" in bot.calls[0][1]["caption"]
    assert "Test User" in bot.calls[0][1]["caption"]
    assert "user@test.com" in bot.calls[0][1]["caption"]
    assert bot.calls[1][0] == "message"
    assert "daffodil" in bot.calls[1][1]["text"].lower()

    bot.calls.clear()
    await send_auth_welcome(bot, 1, account, welcome_back=True, telegram_id=1)
    first = bot.calls[0][1]
    welcome_text = first.get("caption") or first.get("text", "")
    assert "Welcome back" in welcome_text
    assert "user@test.com" not in welcome_text
    assert "Role" not in welcome_text
    assert "Signed in via" not in welcome_text


async def test_login_shows_google_and_email_menu_after_logout(tmp_path):
    from app.integrations.telegram import bot as bot_mod
    from app.integrations.telegram import auth_store as astore_mod
    from app.integrations.telegram import profiles as prof_mod
    from app.integrations.telegram.profiles import STEP_LOGIN_EMAIL

    astore = TelegramAuthStore(str(tmp_path / "users.json"))
    prof_store = prof_mod.TelegramProfileStore(str(tmp_path / "profiles.json"))
    bot = bot_mod.TelegramBot()

    class FakeMessage:
        def __init__(self):
            self.replies = []

        async def reply_text(self, text, **kwargs):
            self.replies.append({"text": text, **kwargs})

    class FakeUser:
        id = 5187786663
        username = "the_shoaib2"
        first_name = "MD Shoaib"
        last_name = "Khan"

    class FakeUpdate:
        message = FakeMessage()
        effective_user = FakeUser()

    astore.create_or_link_google(
        telegram_id=5187786663,
        email="user@test.com",
        full_name="MD Shoaib Khan",
    )
    astore.detach_telegram_session(5187786663)

    profile = prof_store.get(5187786663)
    profile.step = STEP_LOGIN_EMAIL
    profile.mode = "login"
    prof_store.save(profile)

    import app.integrations.telegram.bot as bot_pkg

    orig_astore = bot_pkg.auth_store
    orig_prof = bot_pkg.profile_store
    bot_pkg.auth_store = astore
    bot_pkg.profile_store = prof_store
    try:
        await bot._cmd_login(FakeUpdate(), None)
    finally:
        bot_pkg.auth_store = orig_astore
        bot_pkg.profile_store = orig_prof

    assert len(FakeUpdate.message.replies) == 1
    reply = FakeUpdate.message.replies[0]
    assert "Sign in to Daffodil Intelligence" in reply["text"]
    markup = reply["reply_markup"]
    labels = [btn.text for row in markup.inline_keyboard for btn in row]
    assert "Email & password" in labels
    assert "Login with Google" in labels


async def test_register_shows_google_and_email_menu(tmp_path):
    from app.integrations.telegram import bot as bot_mod
    from app.integrations.telegram import auth_store as astore_mod
    from app.integrations.telegram import profiles as prof_mod

    astore = TelegramAuthStore(str(tmp_path / "users.json"))
    prof_store = prof_mod.TelegramProfileStore(str(tmp_path / "profiles.json"))
    bot = bot_mod.TelegramBot()

    class FakeMessage:
        def __init__(self):
            self.replies = []

        async def reply_text(self, text, **kwargs):
            self.replies.append({"text": text, **kwargs})

    class FakeUser:
        id = 424242
        username = "newuser"
        first_name = "New"
        last_name = "User"

    class FakeUpdate:
        message = FakeMessage()
        effective_user = FakeUser()

    import app.integrations.telegram.bot as bot_pkg

    orig_astore = bot_pkg.auth_store
    orig_prof = bot_pkg.profile_store
    bot_pkg.auth_store = astore
    bot_pkg.profile_store = prof_store
    try:
        await bot._cmd_register(FakeUpdate(), None)
    finally:
        bot_pkg.auth_store = orig_astore
        bot_pkg.profile_store = orig_prof

    assert len(FakeUpdate.message.replies) == 1
    reply = FakeUpdate.message.replies[0]
    assert "Register for Daffodil Intelligence" in reply["text"]
    labels = [btn.text for row in reply["reply_markup"].inline_keyboard for btn in row]
    assert "Email & password" in labels
    assert "Register with Google" in labels


def test_telegram_inline_url_rejects_localhost():
    from app.integrations.telegram.tokens import google_login_url, is_telegram_inline_url

    assert not is_telegram_inline_url("http://localhost:8000/api/auth/telegram/google/start")
    assert not is_telegram_inline_url("http://127.0.0.1:3000/foo")
    assert is_telegram_inline_url("https://api.example.com/api/auth/telegram/google/start")
    url = google_login_url(12345)
    assert "google/start?token=" in url
    assert "google:12345:" in url


def test_google_callback_redirects_to_frontend():
    mock_token = Response(200, json={"access_token": "tok123"})
    mock_user = Response(
        200,
        json={
            "email": "callback@test.com",
            "name": "Callback Test",
            "given_name": "Callback",
            "family_name": "Test",
        },
    )

    with patch("httpx.AsyncClient") as Client:
        inst = AsyncMock()
        Client.return_value.__aenter__.return_value = inst
        inst.post = AsyncMock(return_value=mock_token)
        inst.get = AsyncMock(return_value=mock_user)

        state = sign_state(999001)
        result = asyncio.run(google_callback(state=state, code="fake_code", error=None))

    assert result.status_code == 302
    assert result.headers["location"].startswith(
        "http://localhost:3000/intelligence/auth/telegram?token="
    )
