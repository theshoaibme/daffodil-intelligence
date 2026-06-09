"""`/copycat` and legacy recording commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..services.copycat import run_copycat_subcommand
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update


class CopycatHandlers(HandlerBase):
    async def cmd_copycat(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        if await self.require_auth(update) is None:
            return
        msg = await run_copycat_subcommand(ctx.args or [])
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_recordings(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        if await self.require_auth(update) is None:
            return
        msg = await run_copycat_subcommand(["list"])
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_record(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        if await self.require_auth(update) is None:
            return
        args = ctx.args or []
        if args and args[0] == "stop":
            msg = await run_copycat_subcommand(["stop"])
        else:
            msg = await run_copycat_subcommand(["record", *args])
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_replay(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        if await self.require_auth(update) is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: /replay <name> [speed]")
            return
        msg = await run_copycat_subcommand(["replay", *args])
        await update.message.reply_text(msg)
