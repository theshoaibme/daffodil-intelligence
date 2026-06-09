"""`/skills` and skill CRUD + `/agentskills` for Telegram."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..services.agent_admin import assign_skills
from ..services.skill_admin import (
    create_skill,
    delete_skill,
    format_skill_info,
    format_skill_list,
    update_skill,
)
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update


def _split_pipe(args, count):
    raw = " ".join(args)
    parts = [p.strip() for p in raw.split("|")]
    while len(parts) < count:
        parts.append("")
    return parts[:count]


def _parse_tools(value: str):
    return [t.strip() for t in (value or "").replace(",", " ").split() if t.strip()]


class SkillHandlers(HandlerBase):
    async def cmd_skills(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if args and args[0] not in ("list",):
            await update.message.reply_text(format_skill_info(args[0]), parse_mode="Markdown")
            return
        await update.message.reply_text(format_skill_list(self.owner_id(uid)), parse_mode="Markdown")

    async def cmd_createskill(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text(
                "Usage: `/createskill <name> | <content> | tool1,tool2`\n"
                "Tools are optional and restrict which tools the agent may use.",
                parse_mode="Markdown",
            )
            return
        name, content, tools = _split_pipe(args, 3)
        ok, message = create_skill(
            owner_id=self.owner_id(uid),
            name=name,
            content=content,
            tool_names=_parse_tools(tools),
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_editskill(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/editskill <skill_id> <name> | <content> | tool1,tool2`\n"
                "Leave a field blank to keep it.",
                parse_mode="Markdown",
            )
            return
        skill_id = args[0]
        name, content, tools = _split_pipe(args[1:], 3)
        ok, message = update_skill(
            skill_id,
            self.owner_id(uid),
            name=name or None,
            content=content or None,
            tool_names=_parse_tools(tools) if tools else None,
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_deleteskill(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: `/deleteskill <skill_id>`", parse_mode="Markdown")
            return
        ok, message = delete_skill(args[0], self.owner_id(uid))
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_agentskills(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text(
                "Usage: `/agentskills <agent_id> <skill_id> [skill_id...]`\n"
                "Send just the agent id with no skills to clear them.",
                parse_mode="Markdown",
            )
            return
        agent_id = args[0]
        skill_ids = args[1:]
        ok, message = assign_skills(agent_id, self.owner_id(uid), list(skill_ids))
        await update.message.reply_text(message, parse_mode="Markdown")
