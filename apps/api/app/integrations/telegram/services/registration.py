"""Registration flow helpers (optional fields, skip)."""

from __future__ import annotations

from ..profiles import (
    STEP_REGISTER_DEPARTMENT,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_STUDENT_ID,
    TelegramProfile,
)

SKIPPABLE_STEPS = frozenset({
    STEP_REGISTER_PHONE,
    STEP_REGISTER_STUDENT_ID,
    STEP_REGISTER_DEPARTMENT,
})

SKIP_HELP_TEXT = (
    "*Optional registration fields*\n\n"
    "During sign-up you can skip:\n"
    "• *Phone number* — after you pick a role\n"
    "• *Student ID* — students only, after phone\n"
    "• *Department* — after phone (students: after student ID)\n\n"
    "At any optional step, reply *skip* or send /skip.\n\n"
    "_Cannot be skipped: email, OTP, first name, last name, password, and role._"
)


def is_skippable_step(step: str) -> bool:
    return step in SKIPPABLE_STEPS


def skip_target_label(profile: TelegramProfile) -> str:
    """Human label for the field /skip will clear on the current step."""
    if profile.step == STEP_REGISTER_PHONE:
        return "phone number"
    if profile.step == STEP_REGISTER_STUDENT_ID:
        return "student ID"
    if profile.step == STEP_REGISTER_DEPARTMENT:
        return "department"
    return "field"


def is_skip_input(text: str) -> bool:
    return (text or "").strip().lower() == "skip"
