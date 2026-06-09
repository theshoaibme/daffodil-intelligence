"""
Telegram session profiles
=========================
In-progress registration/login state per Telegram user (PostgreSQL).
Completed accounts live in ``auth_store`` (users table).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Optional

from sqlalchemy import select

from ...core.database import is_mock_database
from ...models.telegram import TelegramProfileSession
from .pg_sync import sync_session

ROLES = ("student", "teacher", "staff", "manager")

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
    mode: str = ""
    selected_agent_id: str = ""

    @property
    def is_complete(self) -> bool:
        return self.step == STEP_COMPLETE

    def sync_telegram_names(self, user) -> "TelegramProfile":
        if not user:
            return self
        self.username = user.username or ""
        preserve_names = (
            self.mode == "register"
            and self.step not in ("", STEP_AUTH_MENU, STEP_REGISTER_EMAIL, STEP_REGISTER_OTP)
        ) or (
            self.mode == "login"
            and self.step in (STEP_LOGIN_FIRST_NAME, STEP_LOGIN_LAST_NAME, STEP_LOGIN_PASSWORD)
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


def _row_to_profile(row: TelegramProfileSession) -> TelegramProfile:
    return TelegramProfile(
        telegram_id=int(row.telegram_id),
        username=row.username or "",
        first_name=row.first_name or "",
        last_name=row.last_name or "",
        full_name=row.full_name or "",
        role=row.role or "",
        phone=row.phone or "",
        email=row.email or "",
        pending_password=row.pending_password or "",
        student_id=row.student_id or "",
        department=row.department or "",
        step=row.step or STEP_AUTH_MENU,
        mode=row.mode or "",
        selected_agent_id=row.selected_agent_id or "",
    )


def _apply_profile_to_row(row: TelegramProfileSession, profile: TelegramProfile) -> None:
    row.username = profile.username
    row.first_name = profile.first_name
    row.last_name = profile.last_name
    row.full_name = profile.full_name
    row.role = profile.role
    row.phone = profile.phone
    row.email = profile.email
    row.pending_password = profile.pending_password
    row.student_id = profile.student_id
    row.department = profile.department
    row.step = profile.step
    row.mode = profile.mode
    row.selected_agent_id = profile.selected_agent_id


class TelegramProfileStore:
    def __init__(self, path: str = ""):
        self._lock = threading.Lock()
        self._memory: Dict[str, TelegramProfile] = {}
        self._use_memory = is_mock_database() or bool(path)

    def get(self, telegram_id: int) -> TelegramProfile:
        with self._lock:
            if self._use_memory:
                key = str(telegram_id)
                if key not in self._memory:
                    self._memory[key] = TelegramProfile(telegram_id=telegram_id)
                return self._memory[key]
            with sync_session() as db:
                row = db.get(TelegramProfileSession, telegram_id)
                if row is None:
                    row = TelegramProfileSession(telegram_id=telegram_id)
                    db.add(row)
                    db.flush()
                return _row_to_profile(row)

    def save(self, profile: TelegramProfile):
        with self._lock:
            if self._use_memory:
                self._memory[str(profile.telegram_id)] = profile
                return
            with sync_session() as db:
                row = db.get(TelegramProfileSession, profile.telegram_id)
                if row is None:
                    row = TelegramProfileSession(telegram_id=profile.telegram_id)
                    db.add(row)
                _apply_profile_to_row(row, profile)

    def reset_session(self, telegram_id: int) -> TelegramProfile:
        p = TelegramProfile(telegram_id=telegram_id, step=STEP_AUTH_MENU)
        self.save(p)
        return p

    def mark_complete(self, profile: TelegramProfile):
        profile.step = STEP_COMPLETE
        self.save(profile)


profile_store = TelegramProfileStore()
