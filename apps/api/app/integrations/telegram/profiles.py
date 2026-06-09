"""
Telegram session profiles
=========================
In-progress registration/login state per Telegram user.
Completed accounts live in ``auth_store`` (telegram_users.json).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

ROLES = ("student", "teacher", "staff", "manager")

# Auth / registration steps
STEP_AUTH_MENU = "auth_menu"
STEP_REGISTER_ROLE = "register_role"
STEP_REGISTER_PHONE = "register_phone"
STEP_REGISTER_EMAIL = "register_email"
STEP_REGISTER_OTP = "register_otp"
STEP_REGISTER_FIRST_NAME = "register_first_name"
STEP_REGISTER_LAST_NAME = "register_last_name"
STEP_REGISTER_PASSWORD = "register_password"
STEP_REGISTER_STUDENT_ID = "register_student_id"
STEP_REGISTER_DEPARTMENT = "register_department"
STEP_LOGIN_EMAIL = "login_email"
STEP_LOGIN_FIRST_NAME = "login_first_name"
STEP_LOGIN_LAST_NAME = "login_last_name"
STEP_LOGIN_PASSWORD = "login_password"
STEP_COMPLETE = "complete"

# Legacy aliases kept for tests
STEP_ROLE = STEP_REGISTER_ROLE
STEP_STUDENT_ID = STEP_REGISTER_STUDENT_ID
STEP_DEPARTMENT = STEP_REGISTER_DEPARTMENT


@dataclass
class TelegramProfile:
    telegram_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    role: str = ""
    phone: str = ""
    email: str = ""
    pending_password: str = ""
    student_id: str = ""
    department: str = ""
    step: str = STEP_AUTH_MENU
    mode: str = ""  # register | login
    selected_agent_id: str = ""  # empty = workspace default

    @property
    def is_complete(self) -> bool:
        return self.step == STEP_COMPLETE

    def sync_telegram_names(self, user) -> "TelegramProfile":
        if not user:
            return self
        self.username = user.username or ""
        preserve_names = (
            self.mode == "register"
            and self.step
            not in ("", STEP_AUTH_MENU, STEP_REGISTER_EMAIL, STEP_REGISTER_OTP)
        ) or (
            self.mode == "login"
            and self.step
            in (STEP_LOGIN_FIRST_NAME, STEP_LOGIN_LAST_NAME, STEP_LOGIN_PASSWORD)
        )
        if preserve_names:
            return self
        self.first_name = (user.first_name or "").strip()
        self.last_name = (user.last_name or "").strip()
        parts = [self.first_name, self.last_name]
        self.full_name = " ".join(p for p in parts if p).strip()
        return self

    def context_line(self) -> str:
        parts = []
        if self.role:
            parts.append(f"role={self.role}")
        if self.email:
            parts.append(f"email={self.email}")
        if self.phone:
            parts.append(f"phone={self.phone}")
        if self.student_id:
            parts.append(f"student_id={self.student_id}")
        if self.department:
            parts.append(f"department={self.department}")
        return "User profile: " + ", ".join(parts) if parts else ""


class TelegramProfileStore:
    def __init__(self, path: str = "telegram_profiles.json"):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._cache: Dict[str, TelegramProfile] = {}
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                for tid, data in raw.items():
                    self._cache[tid] = TelegramProfile(**data)
            except Exception:
                self._cache = {}
        self._loaded = True

    def _save(self):
        data = {tid: asdict(p) for tid, p in self._cache.items()}
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    def get(self, telegram_id: int) -> TelegramProfile:
        with self._lock:
            self._load()
            key = str(telegram_id)
            if key not in self._cache:
                self._cache[key] = TelegramProfile(telegram_id=telegram_id)
            return self._cache[key]

    def save(self, profile: TelegramProfile):
        with self._lock:
            self._load()
            self._cache[str(profile.telegram_id)] = profile
            self._save()

    def reset_session(self, telegram_id: int) -> TelegramProfile:
        p = TelegramProfile(telegram_id=telegram_id, step=STEP_AUTH_MENU)
        self.save(p)
        return p

    def mark_complete(self, profile: TelegramProfile):
        profile.step = STEP_COMPLETE
        self.save(profile)


profile_store = TelegramProfileStore()
