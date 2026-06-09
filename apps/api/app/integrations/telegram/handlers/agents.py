"""`/agent` + Agent Hub CRUD commands for Telegram."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..profiles import profile_store
from ..services.agent_admin import (
    create_custom_agent,
    create_subagent,
    delete_custom_agent,
    format_agent_info,
    format_full_agent_list,
    update_custom_agent,
)
from ..services.agents import format_agent_list, resolve_agent_id, set_agent_for_profile
from .base import HandlerBase

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

    from telegram import Update


def _split_pipe(args, count):
    """Split joined args on `|` into exactly `count` trimmed parts (padded)."""
    raw = " ".join(args)
    parts = [p.strip() for p in raw.split("|")]
    while len(parts) < count:
        parts.append("")
    return parts[:count]


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

    async def cmd_agents(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        await update.message.reply_text(
            format_full_agent_list(owner_id=self.owner_id(uid)),
            parse_mode="Markdown",
        )

    async def cmd_agentinfo(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: `/agentinfo <agent_id>`", parse_mode="Markdown")
            return
        await update.message.reply_text(format_agent_info(args[0]), parse_mode="Markdown")

    async def cmd_createagent(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text(
                "Usage: `/createagent <name> | <description> | <system prompt>`\n"
                "e.g. `/createagent Thesis Helper | research writing aid | You help with thesis writing.`",
                parse_mode="Markdown",
            )
            return
        name, description, prompt = _split_pipe(args, 3)
        ok, message = create_custom_agent(
            owner_id=self.owner_id(uid),
            name=name,
            description=description,
            system_prompt=prompt,
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_createsubagent(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if len(args) < 1:
            await update.message.reply_text(
                "Usage: `/createsubagent <parent_id> <name> | <role> | <instructions>`",
                parse_mode="Markdown",
            )
            return
        parent_id = args[0]
        name, role, instructions = _split_pipe(args[1:], 3)
        if not name:
            await update.message.reply_text(
                "Provide a sub-agent name: `/createsubagent <parent_id> <name> | <role>`",
                parse_mode="Markdown",
            )
            return
        ok, message = create_subagent(
            owner_id=self.owner_id(uid),
            parent_id=parent_id,
            name=name,
            description=role or name,
            instructions=instructions,
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_editagent(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/editagent <agent_id> <name> | <description> | <system prompt>`\n"
                "Leave a field blank to keep it.",
                parse_mode="Markdown",
            )
            return
        agent_id = args[0]
        name, description, prompt = _split_pipe(args[1:], 3)
        ok, message = update_custom_agent(
            agent_id,
            self.owner_id(uid),
            name=name or None,
            description=description or None,
            system_prompt=prompt or None,
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_deleteagent(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = await self.require_auth(update)
        if uid is None:
            return
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: `/deleteagent <agent_id>`", parse_mode="Markdown")
            return
        ok, message = delete_custom_agent(args[0], self.owner_id(uid))
        await update.message.reply_text(message, parse_mode="Markdown")
