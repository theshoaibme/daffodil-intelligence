"""Register agent / copycat / automation command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from telegram.ext import CommandHandler

from .agents import AgentHandlers
from .automation import AutomationHandlers
from .copycat import CopycatHandlers
from .registration import RegistrationHandlers

if TYPE_CHECKING:
    from telegram.ext import Application

    from ..bot import TelegramBot


def register_product_handlers(app: "Application", bot: "TelegramBot") -> None:
    agents = AgentHandlers(bot)
    copycat = CopycatHandlers(bot)
    automation = AutomationHandlers(bot)
    registration = RegistrationHandlers(bot)

    app.add_handler(CommandHandler("skip", registration.cmd_skip))
    app.add_handler(CommandHandler("agent", agents.cmd_agent))
    app.add_handler(CommandHandler("copycat", copycat.cmd_copycat))
    app.add_handler(CommandHandler("automation", automation.cmd_automation))

    # Legacy aliases (kept for existing users & tests)
    app.add_handler(CommandHandler("recordings", copycat.cmd_recordings))
    app.add_handler(CommandHandler("record", copycat.cmd_record))
    app.add_handler(CommandHandler("replay", copycat.cmd_replay))
