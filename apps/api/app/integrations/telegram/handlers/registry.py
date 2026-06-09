"""Register product command handlers (agents, skills, automation, runtime)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from telegram.ext import CallbackQueryHandler, CommandHandler

from .agents import AgentHandlers
from .automation import AutomationHandlers
from .copycat import CopycatHandlers
from .registration import RegistrationHandlers
from .runtime import RuntimeHandlers
from .skills import SkillHandlers

if TYPE_CHECKING:
    from telegram.ext import Application

    from ..bot import TelegramBot


async def dispatch_product_command(
    bot: "TelegramBot",
    update,
    ctx,
    cmd: str,
    args: list[str],
) -> bool:
    """Run a product slash command by name. Returns True if handled."""
    cmd = (cmd or "").lower()
    agents = AgentHandlers(bot)
    skills = SkillHandlers(bot)
    copycat = CopycatHandlers(bot)
    automation = AutomationHandlers(bot)
    registration = RegistrationHandlers(bot)
    runtime = RuntimeHandlers(bot)

    ctx.args = args

    handlers = {
        "skip": registration.cmd_skip,
        "agent": agents.cmd_agent,
        "agents": agents.cmd_agents,
        "agentinfo": agents.cmd_agentinfo,
        "createagent": agents.cmd_createagent,
        "createsubagent": agents.cmd_createsubagent,
        "editagent": agents.cmd_editagent,
        "deleteagent": agents.cmd_deleteagent,
        "skills": skills.cmd_skills,
        "createskill": skills.cmd_createskill,
        "editskill": skills.cmd_editskill,
        "deleteskill": skills.cmd_deleteskill,
        "agentskills": skills.cmd_agentskills,
        "automation": automation.cmd_automation,
        "automate": automation.cmd_automate,
        "loop": automation.cmd_loop,
        "createhook": automation.cmd_createhook,
        "reminders": automation.cmd_reminders,
        "tools": runtime.cmd_tools,
        "mcp": runtime.cmd_mcp,
        "flow": runtime.cmd_flow,
        "logs": runtime.cmd_logs,
        "shell": runtime.cmd_shell,
        "copycat": copycat.cmd_copycat,
        "recordings": copycat.cmd_recordings,
        "record": copycat.cmd_record,
        "replay": copycat.cmd_replay,
    }
    handler = handlers.get(cmd)
    if not handler:
        return False
    await handler(update, ctx)
    return True


def register_product_handlers(app: "Application", bot: "TelegramBot") -> None:
    agents = AgentHandlers(bot)
    skills = SkillHandlers(bot)
    copycat = CopycatHandlers(bot)
    automation = AutomationHandlers(bot)
    registration = RegistrationHandlers(bot)
    runtime = RuntimeHandlers(bot)

    app.add_handler(CommandHandler("skip", registration.cmd_skip))

    # Agents
    app.add_handler(CommandHandler("agent", agents.cmd_agent))
    app.add_handler(CommandHandler("agents", agents.cmd_agents))
    app.add_handler(CommandHandler("agentinfo", agents.cmd_agentinfo))
    app.add_handler(CommandHandler("createagent", agents.cmd_createagent))
    app.add_handler(CommandHandler("createsubagent", agents.cmd_createsubagent))
    app.add_handler(CommandHandler("editagent", agents.cmd_editagent))
    app.add_handler(CommandHandler("deleteagent", agents.cmd_deleteagent))

    # Skills
    app.add_handler(CommandHandler("skills", skills.cmd_skills))
    app.add_handler(CommandHandler("createskill", skills.cmd_createskill))
    app.add_handler(CommandHandler("editskill", skills.cmd_editskill))
    app.add_handler(CommandHandler("deleteskill", skills.cmd_deleteskill))
    app.add_handler(CommandHandler("agentskills", skills.cmd_agentskills))

    # Automation
    app.add_handler(CommandHandler("automation", automation.cmd_automation))
    app.add_handler(CommandHandler("automate", automation.cmd_automate))
    app.add_handler(CommandHandler("loop", automation.cmd_loop))
    app.add_handler(CommandHandler("createhook", automation.cmd_createhook))
    app.add_handler(CommandHandler("reminders", automation.cmd_reminders))

    # Runtime & observability
    app.add_handler(CommandHandler("tools", runtime.cmd_tools))
    app.add_handler(CommandHandler("mcp", runtime.cmd_mcp))
    app.add_handler(CommandHandler("flow", runtime.cmd_flow))
    app.add_handler(CommandHandler("logs", runtime.cmd_logs))
    app.add_handler(CommandHandler("shell", runtime.cmd_shell))
    app.add_handler(CallbackQueryHandler(runtime.on_shell_callback, pattern=r"^shell:"))

    # CopyCat
    app.add_handler(CommandHandler("copycat", copycat.cmd_copycat))

    # Legacy aliases (kept for existing users & tests)
    app.add_handler(CommandHandler("recordings", copycat.cmd_recordings))
    app.add_handler(CommandHandler("record", copycat.cmd_record))
    app.add_handler(CommandHandler("replay", copycat.cmd_replay))
