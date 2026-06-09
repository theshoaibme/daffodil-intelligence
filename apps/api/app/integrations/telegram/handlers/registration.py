"""`/skip` during Telegram registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..profiles import STEP_COMPLETE, profile_store
from ..services.registration import SKIP_HELP_TEXT, is_skippable_step, skip_target_label
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update


class RegistrationHandlers(HandlerBase):
    async def cmd_skip(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        profile = profile_store.get(uid)
        self.bot._sync(update, profile)

        if not is_skippable_step(profile.step):
            await update.message.reply_text(SKIP_HELP_TEXT, parse_mode="Markdown")
            return

        label = skip_target_label(profile)
        await self.bot._apply_registration_skip(update, ctx, profile, uid)
        if profile.step != STEP_COMPLETE:
            await update.message.reply_text(
                f"Skipped *{label}*. See the next prompt above.",
                parse_mode="Markdown",
            )
