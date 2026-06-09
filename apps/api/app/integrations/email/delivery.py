"""Transactional email delivery for OTP and notifications."""

from __future__ import annotations

import logging
import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional

import httpx

from ...core.config import Settings, get_settings

logger = logging.getLogger(__name__)

OTP_SUBJECT = "Daffodil Intelligence — verification code"
_EMAIL_IN_ANGLE_RE = re.compile(r"<([^>]+@[^>]+)>")


@dataclass(frozen=True)
class EmailDeliveryResult:
    sent: bool
    provider: str = ""
    error: str = ""


def _otp_body(code: str, ttl_minutes: int) -> str:
    return (
        f"Your Daffodil Intelligence verification code is: {code}\n\n"
        f"This code expires in {ttl_minutes} minutes.\n"
        "If you did not request this, ignore this email."
    )


class EmailDelivery:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @property
    def provider(self) -> str:
        explicit = (self._settings.EMAIL_PROVIDER or "auto").strip().lower()
        if explicit != "auto":
            return explicit
        if (self._settings.RESEND_API_KEY or "").strip():
            return "resend"
        if (self._settings.SMTP_HOST or "").strip():
            return "smtp"
        return "none"

    def is_configured(self) -> bool:
        provider = self.provider
        if provider == "resend":
            return True
        if provider != "smtp":
            return False
        host = (self._settings.SMTP_HOST or "").strip()
        if not host:
            return False
        password = (self._settings.SMTP_PASSWORD or "").strip()
        if password and not self._smtp_login_user():
            return False
        return True

    @staticmethod
    def _extract_email_address(value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        match = _EMAIL_IN_ANGLE_RE.search(raw)
        if match:
            return match.group(1).strip().lower()
        if "@" in raw and " " not in raw:
            return raw.lower()
        return ""

    def _smtp_login_user(self) -> str:
        user = (self._settings.SMTP_USER or "").strip()
        if user:
            return user
        return self._extract_email_address(self._from_address())

    def _from_address(self) -> str:
        from_addr = (self._settings.SMTP_FROM or "").strip()
        if from_addr:
            return from_addr
        return (self._settings.SMTP_USER or "").strip()

    def _message_from(self) -> str:
        return self._from_address() or "noreply@daffodil.edu.bd"

    def send_verification_code(self, email: str, code: str, *, ttl_minutes: int = 10) -> EmailDeliveryResult:
        to_addr = (email or "").strip().lower()
        if not to_addr:
            return EmailDeliveryResult(sent=False, provider=self.provider, error="missing_recipient")

        provider = self.provider
        body = _otp_body(code, ttl_minutes)
        subject = OTP_SUBJECT

        if provider == "resend":
            return self._send_resend(to_addr, subject, body)
        if provider == "smtp":
            return self._send_smtp(to_addr, subject, body)
        return EmailDeliveryResult(sent=False, provider="none", error="not_configured")

    def _send_smtp(self, to_addr: str, subject: str, body: str) -> EmailDeliveryResult:
        host = (self._settings.SMTP_HOST or "").strip()
        port = int(self._settings.SMTP_PORT or 587)
        password = (self._settings.SMTP_PASSWORD or "").strip()
        login_user = self._smtp_login_user()
        from_addr = self._message_from()
        use_ssl = bool(self._settings.SMTP_USE_SSL)
        starttls = bool(self._settings.SMTP_STARTTLS) and not use_ssl

        if password and not login_user:
            logger.error("SMTP_PASSWORD is set but SMTP_USER/SMTP_FROM is missing")
            return EmailDeliveryResult(sent=False, provider="smtp", error="smtp_user_required")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.set_content(body)

        try:
            if use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, timeout=20, context=context) as smtp:
                    if password:
                        smtp.login(login_user, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=20) as smtp:
                    if starttls:
                        smtp.starttls(context=ssl.create_default_context())
                    if password:
                        smtp.login(login_user, password)
                    smtp.send_message(msg)
            logger.info("Sent verification email to %s via SMTP (%s:%s)", to_addr, host, port)
            return EmailDeliveryResult(sent=True, provider="smtp")
        except Exception as exc:
            logger.error("SMTP delivery failed for %s: %s", to_addr, exc)
            return EmailDeliveryResult(sent=False, provider="smtp", error=str(exc))

    def _send_resend(self, to_addr: str, subject: str, body: str) -> EmailDeliveryResult:
        api_key = (self._settings.RESEND_API_KEY or "").strip()
        from_addr = self._from_address()
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_addr,
                    "to": [to_addr],
                    "subject": subject,
                    "text": body,
                },
                timeout=20.0,
            )
            if response.status_code >= 400:
                detail = response.text[:300]
                logger.error("Resend API error for %s: %s %s", to_addr, response.status_code, detail)
                return EmailDeliveryResult(
                    sent=False,
                    provider="resend",
                    error=f"resend_http_{response.status_code}",
                )
            logger.info("Sent verification email to %s via Resend", to_addr)
            return EmailDeliveryResult(sent=True, provider="resend")
        except Exception as exc:
            logger.error("Resend delivery failed for %s: %s", to_addr, exc)
            return EmailDeliveryResult(sent=False, provider="resend", error=str(exc))


email_delivery = EmailDelivery()


def send_verification_email(email: str, code: str, *, ttl_minutes: int = 10) -> EmailDeliveryResult:
    return email_delivery.send_verification_code(email, code, ttl_minutes=ttl_minutes)
