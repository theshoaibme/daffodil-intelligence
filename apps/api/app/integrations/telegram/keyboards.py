"""Telegram inline and reply keyboards."""

from __future__ import annotations

from typing import List

from .tokens import google_login_url, is_telegram_inline_url

try:
    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
    )
except Exception:  # pragma: no cover
    InlineKeyboardButton = InlineKeyboardMarkup = KeyboardButton = object  # type: ignore
    ReplyKeyboardMarkup = ReplyKeyboardRemove = object  # type: ignore


def google_auth_button(telegram_id: int, *, label: str) -> "InlineKeyboardButton":
    url = google_login_url(telegram_id)
    if is_telegram_inline_url(url):
        return InlineKeyboardButton(label, url=url)
    # Telegram rejects localhost/private URLs on inline URL buttons — use callback + link in message.
    return InlineKeyboardButton("Get Google link", callback_data="auth:google")


def google_auth_row(telegram_id: int, *, label: str) -> List["InlineKeyboardButton"]:
    return [google_auth_button(telegram_id, label=label)]


def login_keyboard(telegram_id: int) -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Email & password", callback_data="auth:login_email")],
        google_auth_row(telegram_id, label="Login with Google"),
        [InlineKeyboardButton("Back", callback_data="auth:menu")],
    ])


def register_keyboard(telegram_id: int) -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Email & password", callback_data="auth:register_email")],
        google_auth_row(telegram_id, label="Register with Google"),
        [InlineKeyboardButton("Back", callback_data="auth:menu")],
    ])


def auth_keyboard(telegram_id: int) -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Register", callback_data="auth:register")],
        [InlineKeyboardButton("Login", callback_data="auth:login_menu")],
    ])


def auth_suggestion_keyboard() -> "ReplyKeyboardMarkup":
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Register"), KeyboardButton("Login")]],
        resize_keyboard=True,
        input_field_placeholder="Tap Register or Login to continue…",
    )


def clear_suggestion_keyboard() -> "ReplyKeyboardRemove":
    return ReplyKeyboardRemove()


def role_keyboard() -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Student", callback_data="role:student"),
            InlineKeyboardButton("Teacher", callback_data="role:teacher"),
        ],
        [
            InlineKeyboardButton("Staff", callback_data="role:staff"),
            InlineKeyboardButton("Manager", callback_data="role:manager"),
        ],
    ])
