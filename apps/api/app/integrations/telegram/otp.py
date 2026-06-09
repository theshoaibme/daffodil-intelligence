"""Email OTP generation, delivery, and verification."""

from __future__ import annotations

import logging
import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ...core.config import get_settings
from ..email.delivery import send_verification_email

logger = logging.getLogger(__name__)
settings = get_settings()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OTP_TTL_SECONDS = 600  # 10 minutes


@dataclass(frozen=True)
class OtpSendResult:
    sent: bool
    dev_code: str = ""
    error: str = ""


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

    def deliver(self, email: str, code: str) -> OtpSendResult:
        """Send OTP email. In development, returns dev_code when delivery is not configured."""
        result = send_verification_email(email, code, ttl_minutes=OTP_TTL_SECONDS // 60)
        if result.sent:
            return OtpSendResult(sent=True)

        if settings.NODE_ENV == "development":
            logger.info("OTP for %s: %s (email delivery: %s)", email, code, result.error or "not_configured")
            return OtpSendResult(sent=False, dev_code=code, error=result.error or "not_configured")

        logger.error("OTP delivery failed for %s: %s", email, result.error or "not_configured")
        return OtpSendResult(sent=False, error=result.error or "not_configured")

    def send(self, email: str, code: str) -> Tuple[bool, str]:
        """Backward-compatible send API. Returns (success, dev_code_or_empty)."""
        result = self.deliver(email, code)
        if result.sent:
            return True, ""
        return False, result.dev_code


otp_service = OTPService()
