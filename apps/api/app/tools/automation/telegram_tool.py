"""Telegram outbound messaging tool."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.telegram_notify import (
    resolve_telegram_chat_id_for_user,
    send_telegram_message,
)
from ...runtime.tool_context import get_telegram_chat_id, get_user_id


class SendTelegramMessageTool(BaseTool):
    name = "send_telegram_message"
    description = (
        "Send a Telegram message to the current user. Requires a linked Telegram account "
        "(register/login via the DI Telegram bot with the same email)."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="message", type="string", description="Message text (Markdown supported)"),
        ToolParameter(
            name="user_id",
            type="string",
            description="Web user id (optional)",
            required=False,
        ),
        ToolParameter(
            name="telegram_chat_id",
            type="string",
            description="Explicit Telegram chat id (optional override)",
            required=False,
        ),
    ]

    async def execute(
        self,
        message: str,
        user_id: str = None,
        telegram_chat_id: str = None,
        **kwargs,
    ) -> ToolResult:
        chat_id = int(telegram_chat_id) if telegram_chat_id else get_telegram_chat_id()
        if not chat_id:
            uid = int(user_id) if user_id else get_user_id()
            if not uid:
                return self.fail("No user_id; cannot resolve Telegram chat")
            chat_id = await resolve_telegram_chat_id_for_user(uid)
        if not chat_id:
            return self.fail(
                "Telegram not linked. User must log in via the Daffodil Intelligence Telegram bot."
            )
        ok = await send_telegram_message(chat_id, message)
        if not ok:
            return self.fail("Failed to send Telegram message (check TELEGRAM_BOT_TOKEN)")
        return self.ok({"status": "sent", "telegram_chat_id": chat_id})
