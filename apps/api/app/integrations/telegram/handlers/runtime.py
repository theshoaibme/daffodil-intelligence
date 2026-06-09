"""Runtime & observability commands: /tools, /mcp, /flow, /logs, /shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..services.observability import format_flow, format_logs, format_mcp, format_tools
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except Exception:  # pragma: no cover
    InlineKeyboardButton = InlineKeyboardMarkup = None  # type: ignore

_MAX_SHELL_OUTPUT = 3500


class RuntimeHandlers(HandlerBase):
    def _chat_key(self, uid: int):
        return self.owner_id(uid), f"tg-{uid}"

    async def cmd_tools(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        await update.message.reply_text(format_tools(), parse_mode="Markdown")

    async def cmd_mcp(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        await update.message.reply_text(format_mcp(), parse_mode="Markdown")

    async def cmd_flow(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        user_id, chat_id = self._chat_key(uid)
        await update.message.reply_text(
            format_flow(user_id=user_id, chat_id=chat_id), parse_mode="Markdown"
        )

    async def cmd_logs(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        user_id, chat_id = self._chat_key(uid)
        await update.message.reply_text(
            format_logs(user_id=user_id, chat_id=chat_id), parse_mode="Markdown"
        )

    async def cmd_shell(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        if not self.bot._is_admin(uid):
            await update.message.reply_text(
                "`/shell` is restricted to admins. Ask the owner to add your id to "
                "`TELEGRAM_ADMIN_USER_IDS`.",
                parse_mode="Markdown",
            )
            return
        command = " ".join(ctx.args or []).strip()
        if not command:
            await update.message.reply_text(
                "Usage: `/shell <command>` (admin only). You will be asked to confirm.",
                parse_mode="Markdown",
            )
            return
        ctx.user_data["pending_shell"] = command
        markup = None
        if InlineKeyboardMarkup is not None:
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Run", callback_data="shell:confirm"),
                        InlineKeyboardButton("Cancel", callback_data="shell:cancel"),
                    ]
                ]
            )
        await update.message.reply_text(
            f"Run this command?\n\n`{command}`",
            parse_mode="Markdown",
            reply_markup=markup,
        )

    async def on_shell_callback(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        query = update.callback_query
        await query.answer()
        uid = update.effective_user.id
        if not self.bot._is_admin(uid):
            await query.edit_message_text("Not authorized.")
            return
        action = (query.data or "").split(":", 1)[1] if ":" in (query.data or "") else ""
        command = ctx.user_data.pop("pending_shell", None)
        if action == "cancel" or not command:
            await query.edit_message_text("Cancelled.")
            return

        from ....tools.registry import get_registry

        await query.edit_message_text(f"Running:\n`{command}`", parse_mode="Markdown")
        try:
            result = await get_registry().execute("run_shell_command", command=command)
        except Exception as e:
            await query.message.reply_text(f"Shell error: {e}")
            return
        if result.success:
            data = result.data if isinstance(result.data, str) else str(result.data)
            body = data[:_MAX_SHELL_OUTPUT] or "(no output)"
            await query.message.reply_text(f"```\n{body}\n```", parse_mode="Markdown")
        else:
            await query.message.reply_text(f"Failed: {result.error}")
