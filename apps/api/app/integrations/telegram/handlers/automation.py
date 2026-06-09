"""`/automation` — skills and agents for workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ....skills.store import skill_store
from ..services.agents import format_automation_agents
from ..services.automation_admin import (
    create_hook_from_text,
    create_loop_from_text,
    delete_automation,
    format_automations,
    format_reminders,
)
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update

_AUTOMATION_HELP = (
    "*Automation*\n\n"
    "/automate — list loops, hooks, reminders\n"
    "/loop <minutes> | <prompt> — recurring prompt\n"
    "/createhook <event> <action> | <text> — event trigger\n"
    "/reminders — your reminders\n"
    "/automation skills — macros & workflow skills\n"
    "/automation agents — automation-focused agents\n"
    "/copycat — record & replay desktop macros"
)


class AutomationHandlers(HandlerBase):
    async def cmd_automate(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if args and args[0].lower() == "delete" and len(args) > 1:
            ok, message = delete_automation(self.owner_id(uid), args[1])
            await update.message.reply_text(message, parse_mode="Markdown")
            return
        await update.message.reply_text(format_automations(self.owner_id(uid)), parse_mode="Markdown")

    async def cmd_loop(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        raw = " ".join(ctx.args or [])
        ok, message = create_loop_from_text(self.owner_id(uid), raw)
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_createhook(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        ok, message = create_hook_from_text(self.owner_id(uid), list(ctx.args or []))
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_reminders(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        await update.message.reply_text(format_reminders(self.owner_id(uid)), parse_mode="Markdown")
    async def cmd_automation(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return

        args = ctx.args or []
        sub = args[0].lower() if args else "help"

        if sub in ("help", "?"):
            await update.message.reply_text(_AUTOMATION_HELP, parse_mode="Markdown")
            return

        if sub == "agents":
            await update.message.reply_text(format_automation_agents(), parse_mode="Markdown")
            return

        if sub in ("skills", "list"):
            await update.message.reply_text(self._format_automation_skills(uid), parse_mode="Markdown")
            return

        await update.message.reply_text(
            f"Unknown subcommand `{sub}`.\n\n{_AUTOMATION_HELP}",
            parse_mode="Markdown",
        )

    def _format_automation_skills(self, user_id: int) -> str:
        skills = skill_store.list_all(user_id=user_id)
        tagged: List = []
        for skill in skills:
            tags = {t.lower() for t in (skill.tags or [])}
            if tags & {"automation", "copycat", "desktop"} or skill.source == "copycat":
                tagged.append(skill)

        if not tagged:
            return (
                "*Automation skills*\n\n"
                "No automation skills yet.\n"
                "Record a macro with `/copycat record` — a skill is created when you stop."
            )

        lines = ["*Automation skills*", ""]
        for skill in tagged[:20]:
            rec = f" → `{skill.recording_name}`" if skill.recording_name else ""
            lines.append(f"• *{skill.name}*{rec}")
        if len(tagged) > 20:
            lines.append(f"\n_…and {len(tagged) - 20} more_")
        lines.append("\nReplay with `/copycat replay <recording_name>`.")
        return "\n".join(lines)
