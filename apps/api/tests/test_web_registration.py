"""Web registration OTP flow (aligned with Telegram bot steps)."""

import asyncio
import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.integrations.telegram.otp import OtpSendResult
from app.main import app


@pytest.mark.asyncio
async def test_web_register_email_otp_complete_flow():
    email = f"webreg-{uuid.uuid4().hex[:8]}@diu.edu.bd"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch(
            "app.api.auth.otp_service.deliver",
            return_value=OtpSendResult(sent=True),
        ):
            send = await client.post(
                "/api/auth/register/send-otp",
                json={"email": email, "accept_terms": True},
            )
        if send.status_code == 503:
            pytest.skip("Database not available in test environment")
        assert send.status_code == 200, send.text
        payload = send.json()
        assert payload["message"] == "Verification code sent to your email"
        assert "dev_otp" not in payload or payload.get("dev_otp") is None

        from app.integrations.telegram.otp import otp_service

        code = None
        with patch.object(otp_service, "verify", return_value=True):
            verify = await client.post(
                "/api/auth/register/verify-otp",
                json={"email": email, "code": "123456"},
            )
        assert verify.status_code == 200, verify.text
        assert verify.json()["message"] == "Email verified"

        complete = await client.post(
            "/api/auth/register/complete",
            json={
                "email": email,
                "first_name": "Web",
                "last_name": "User",
                "password": "secret123",
                "role": "student",
            },
        )
        assert complete.status_code == 200, complete.text
        body = complete.json()
        assert body["email"] == email
        assert body["full_name"] == "Web User"


def test_register_send_otp_response_maps_dev_fallback():
    from app.api.auth import register_send_otp
    from app.schemas.user import RegisterSendOtpRequest

    class FakeDb:
        async def execute(self, *_args, **_kwargs):
            class Result:
                def scalar_one_or_none(self):
                    return None

            return Result()

    request = RegisterSendOtpRequest(email="devotp@diu.edu.bd", accept_terms=True)
    with patch("app.api.auth.pending_registration_store.start_email"):
        with patch(
            "app.api.auth.otp_service.deliver",
            return_value=OtpSendResult(sent=False, dev_code="998877"),
        ):
            response = asyncio.run(register_send_otp(request, FakeDb()))

    assert response.dev_otp == "998877"
    assert "development" in response.message.lower()


def test_register_send_otp_response_raises_when_delivery_fails_in_production():
    from app.api.auth import register_send_otp
    from app.schemas.user import RegisterSendOtpRequest
    from fastapi import HTTPException

    class FakeDb:
        async def execute(self, *_args, **_kwargs):
            class Result:
                def scalar_one_or_none(self):
                    return None

            return Result()

    request = RegisterSendOtpRequest(email="failotp@diu.edu.bd", accept_terms=True)
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.NODE_ENV = "production"
        with patch("app.api.auth.pending_registration_store.start_email"):
            with patch(
                "app.api.auth.otp_service.deliver",
                return_value=OtpSendResult(sent=False, error="smtp_down"),
            ):
                with pytest.raises(HTTPException) as exc:
                    asyncio.run(register_send_otp(request, FakeDb()))

    assert exc.value.status_code == 503
