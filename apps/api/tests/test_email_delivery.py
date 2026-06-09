"""Email OTP delivery tests."""

from unittest.mock import MagicMock, patch

import httpx

from app.core.config import Settings
from app.integrations.email.delivery import EmailDelivery


def _settings(**overrides) -> Settings:
    base = {
        "EMAIL_PROVIDER": "auto",
        "SMTP_HOST": "",
        "SMTP_PORT": 587,
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM": "",
        "SMTP_USE_SSL": False,
        "SMTP_STARTTLS": True,
        "RESEND_API_KEY": "",
        "NODE_ENV": "development",
    }
    base.update(overrides)
    return Settings(**base)


def test_provider_auto_prefers_resend():
    delivery = EmailDelivery(_settings(RESEND_API_KEY="re_test", SMTP_HOST="smtp.example.com"))
    assert delivery.provider == "resend"
    assert delivery.is_configured()


def test_provider_auto_uses_smtp_when_no_resend():
    delivery = EmailDelivery(_settings(SMTP_HOST="localhost", SMTP_PORT=1025))
    assert delivery.provider == "smtp"
    assert delivery.is_configured()


def test_provider_none_when_unconfigured():
    delivery = EmailDelivery(_settings())
    assert delivery.provider == "none"
    assert not delivery.is_configured()


def test_send_smtp_success():
    delivery = EmailDelivery(
        _settings(
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="mail.mock.local",
            SMTP_PORT=1025,
            SMTP_FROM="noreply@test.local",
            SMTP_STARTTLS=False,
        )
    )
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    ctx.__exit__.return_value = False
    with patch("app.integrations.email.delivery.smtplib.SMTP", return_value=ctx) as factory:
        result = delivery.send_verification_code("user@test.com", "123456")

    assert result.sent is True
    assert result.provider == "smtp"
    factory.assert_called_once_with("mail.mock.local", 1025, timeout=20)
    conn.send_message.assert_called_once()


def test_send_smtp_ssl_success():
    delivery = EmailDelivery(
        _settings(
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=465,
            SMTP_USE_SSL=True,
            SMTP_USER="user@gmail.com",
            SMTP_PASSWORD="secret",
        )
    )
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    ctx.__exit__.return_value = False
    with patch("app.integrations.email.delivery.smtplib.SMTP_SSL", return_value=ctx):
        result = delivery.send_verification_code("user@test.com", "654321")

    assert result.sent is True
    conn.login.assert_called_once_with("user@gmail.com", "secret")


def test_smtp_requires_user_when_password_set():
    delivery = EmailDelivery(
        _settings(
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_PASSWORD="secret",
        )
    )
    assert not delivery.is_configured()
    result = delivery.send_verification_code("user@test.com", "123456")
    assert result.sent is False
    assert result.error == "smtp_user_required"


def test_smtp_uses_from_address_as_login_user():
    delivery = EmailDelivery(
        _settings(
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="mail.mock.local",
            SMTP_PORT=1025,
            SMTP_PASSWORD="secret",
            SMTP_FROM="noreply@test.local",
            SMTP_STARTTLS=False,
        )
    )
    assert delivery.is_configured()
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    ctx.__exit__.return_value = False
    with patch("app.integrations.email.delivery.smtplib.SMTP", return_value=ctx):
        result = delivery.send_verification_code("user@test.com", "123456")

    assert result.sent is True
    conn.login.assert_called_once_with("noreply@test.local", "secret")


def test_send_resend_success():
    delivery = EmailDelivery(
        _settings(
            EMAIL_PROVIDER="resend",
            RESEND_API_KEY="re_test_key",
            SMTP_FROM="Daffodil <noreply@daffodil.edu.bd>",
        )
    )
    response = httpx.Response(200, json={"id": "email_123"})
    with patch("app.integrations.email.delivery.httpx.post", return_value=response) as post:
        result = delivery.send_verification_code("user@test.com", "111222")

    assert result.sent is True
    assert result.provider == "resend"
    post.assert_called_once()
    payload = post.call_args.kwargs["json"]
    assert payload["to"] == ["user@test.com"]
    assert "111222" in payload["text"]


def test_send_resend_http_error():
    delivery = EmailDelivery(
        _settings(EMAIL_PROVIDER="resend", RESEND_API_KEY="re_test_key", SMTP_FROM="noreply@test.local")
    )
    response = httpx.Response(422, text="invalid from")
    with patch("app.integrations.email.delivery.httpx.post", return_value=response):
        result = delivery.send_verification_code("user@test.com", "111222")

    assert result.sent is False
    assert result.provider == "resend"
    assert "resend_http_422" in result.error


def test_otp_deliver_returns_dev_code_in_development():
    from app.integrations.telegram.otp import OTPService

    svc = OTPService()
    code = svc.generate("dev@test.com")
    with patch(
        "app.integrations.telegram.otp.send_verification_email",
        return_value=type("R", (), {"sent": False, "provider": "none", "error": "not_configured"})(),
    ):
        with patch("app.integrations.telegram.otp.settings") as mock_settings:
            mock_settings.NODE_ENV = "development"
            result = svc.deliver("dev@test.com", code)

    assert result.sent is False
    assert result.dev_code == code


def test_otp_deliver_fails_in_production_without_email():
    from app.integrations.telegram.otp import OTPService

    svc = OTPService()
    code = svc.generate("prod@test.com")
    with patch(
        "app.integrations.telegram.otp.send_verification_email",
        return_value=type("R", (), {"sent": False, "provider": "none", "error": "not_configured"})(),
    ):
        with patch("app.integrations.telegram.otp.settings") as mock_settings:
            mock_settings.NODE_ENV = "production"
            result = svc.deliver("prod@test.com", code)

    assert result.sent is False
    assert result.dev_code == ""


def test_otp_deliver_success():
    from app.integrations.telegram.otp import OTPService

    svc = OTPService()
    code = svc.generate("ok@test.com")
    with patch(
        "app.integrations.telegram.otp.send_verification_email",
        return_value=type("R", (), {"sent": True, "provider": "smtp", "error": ""})(),
    ):
        result = svc.deliver("ok@test.com", code)

    assert result.sent is True
    assert result.dev_code == ""
