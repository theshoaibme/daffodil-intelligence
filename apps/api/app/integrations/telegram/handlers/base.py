"""Shared helpers for Telegram command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..commands import auth_required_message
from ..keyboards import auth_suggestion_keyboard

if TYPE_CHECKING:
    from telegram import Update

    from ..bot import TelegramBot


class HandlerBase:
    def __init__(self, bot: "TelegramBot"):
        self.bot = bot

    async def require_auth(self, update: "Update") -> Optional[int]:
        uid = update.effective_user.id
        if not self.bot._is_authenticated(uid):
            await update.message.reply_text(
                auth_required_message(),
                parse_mode="Markdown",
                reply_markup=auth_suggestion_keyboard(),
            )
            return None
        return uid
