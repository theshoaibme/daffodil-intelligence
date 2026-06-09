"""Email OTP generation and verification for Telegram registration."""

from __future__ import annotations

import logging
import random
import re
import smtplib
import threading
import time
from email.message import EmailMessage
from typing import Dict, Optional, Tuple

from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OTP_TTL_SECONDS = 600  # 10 minutes


class OTPService:
    def __init__(self):
        self._lock = threading.Lock()
        self._codes: Dict[str, Tuple[str, float]] = {}  # email -> (code, expires_at)

    @staticmethod
    def is_valid_email(email: str) -> bool:
        return bool(EMAIL_RE.match((email or "").strip().lower()))

    def generate(self, email: str) -> str:
        email = email.strip().lower()
        code = f"{random.randint(0, 999999):06d}"
        with self._lock:
            self._codes[email] = (code, time.time() + OTP_TTL_SECONDS)
        return code

    def verify(self, email: str, code: str) -> bool:
        email = email.strip().lower()
        code = (code or "").strip()
        with self._lock:
            entry = self._codes.get(email)
            if not entry:
                return False
            stored, expires = entry
            if time.time() > expires:
                del self._codes[email]
                return False
            if stored != code:
                return False
            del self._codes[email]
            return True

    def send(self, email: str, code: str) -> Tuple[bool, str]:
        """Send OTP email. Returns (success, user-facing message)."""
        host = getattr(settings, "SMTP_HOST", "") or ""
        port = int(getattr(settings, "SMTP_PORT", 587) or 587)
        user = getattr(settings, "SMTP_USER", "") or ""
        password = getattr(settings, "SMTP_PASSWORD", "") or ""
        from_addr = getattr(settings, "SMTP_FROM", "") or user or "noreply@daffodil.edu.bd"

        if not host:
            logger.info("OTP for %s: %s (SMTP not configured)", email, code)
            return False, code

        msg = EmailMessage()
        msg["Subject"] = "Daffodil Intelligence — verification code"
        msg["From"] = from_addr
        msg["To"] = email
        msg.set_content(
            f"Your Daffodil Intelligence verification code is: {code}\n\n"
            f"This code expires in {OTP_TTL_SECONDS // 60} minutes.\n"
            "If you did not request this, ignore this email."
        )
        try:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.starttls()
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
            return True, ""
        except Exception as e:
            logger.error("Failed to send OTP email to %s: %s", email, e)
            return False, code


otp_service = OTPService()
