"""`/agent` — list and select chat agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..profiles import profile_store
from ..services.agents import format_agent_list, resolve_agent_id, set_agent_for_profile
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update


class AgentHandlers(HandlerBase):
    async def cmd_agent(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return

        profile = profile_store.get(uid)
        self.bot._sync(update, profile)
        args = ctx.args or []

        if not args:
            current = resolve_agent_id(profile)
            await update.message.reply_text(
                format_agent_list(current_id=current, telegram_id=uid),
                parse_mode="Markdown",
            )
            return

        ok, message = set_agent_for_profile(profile, args[0])
        await update.message.reply_text(message, parse_mode="Markdown")
