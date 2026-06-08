"""Telegram auth store and OTP unit tests."""

from app.integrations.telegram.auth_store import TelegramAuthStore
from app.integrations.telegram.otp import otp_service, OTPService


def test_otp_verify(tmp_path):
    svc = OTPService()
    code = svc.generate("user@test.com")
    assert svc.verify("user@test.com", code)
    assert not svc.verify("user@test.com", code)


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
