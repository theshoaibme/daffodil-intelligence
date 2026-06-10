"""Telegram slash-command definitions, default messages, and menu sync."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Sequence

if TYPE_CHECKING:
    from telegram import Bot

from ...prompts.manager import GREETING_EN

logger = logging.getLogger(__name__)

try:
    from telegram import BotCommand
except Exception:  # pragma: no cover
    BotCommand = None  # type: ignore

# Guest users (not signed in)
GUEST_COMMANDS: List[tuple[str, str]] = [
    ("start", "Welcome & home"),
    ("register", "Create account (Google or email)"),
    ("login", "Sign in (Google or email)"),
    ("help", "Commands & how to use the bot"),
]

# Signed-in users (grouped by category for the / menu)
AUTHENTICATED_COMMANDS: List[tuple[str, str]] = [
    ("start", "Welcome back"),
    ("help", "Commands & tips"),
    # Agents
    ("agents", "List all agents"),
    ("agent", "Switch chat agent"),
    ("createagent", "Create a custom agent"),
    ("editagent", "Edit a custom agent"),
    ("deleteagent", "Delete a custom agent"),
    ("createsubagent", "Create a sub-agent"),
    ("agentinfo", "Agent details"),
    # Skills
    ("skills", "List skills"),
    ("createskill", "Create a skill"),
    ("editskill", "Edit a skill"),
    ("deleteskill", "Delete a skill"),
    ("agentskills", "Assign skills to an agent"),
    # Automation
    ("automate", "Loops, hooks & reminders"),
    ("loop", "Recurring prompt"),
    ("createhook", "Event trigger"),
    ("reminders", "Your reminders"),
    ("automation", "Workflow skills & agents"),
    ("copycat", "Desktop macro record & replay"),
    # Runtime & observability
    ("tools", "Available tools"),
    ("mcp", "MCP status"),
    ("flow", "Live agent/tool flow"),
    ("logs", "Recent agent runs"),
    # Account
    ("profile", "View your account"),
    ("logout", "Sign out on this device"),
]

# Fallback when BotCommand import fails (tests without PTB)
GUEST_COMMAND_LABELS = [name for name, _ in GUEST_COMMANDS]
AUTHENTICATED_COMMAND_LABELS = [name for name, _ in AUTHENTICATED_COMMANDS]


def _to_bot_commands(spec: Sequence[tuple[str, str]]):
    if BotCommand is None:
        return []
    return [BotCommand(command=name, description=desc) for name, desc in spec]


def help_text(*, authenticated: bool) -> str:
    if authenticated:
        return (
            "*Daffodil Intelligence — commands*\n\n"
            "*Chat*\n"
            "Send any message, photo, or voice note. The active agent uses tools, "
            "MCP, and memory automatically.\n\n"
            "*Agents*\n"
            "/agents — list builtin + custom agents\n"
            "/agent \\<id\\> — switch (e.g. /agent coding)\n"
            "/agent default — reset to workspace default\n"
            "/agentinfo \\<id\\> — details\n"
            "/createagent \\<name\\> | \\<desc\\> | \\<prompt\\>\n"
            "/editagent \\<id\\> \\<name\\> | \\<desc\\> | \\<prompt\\>\n"
            "/deleteagent \\<id\\>\n"
            "/createsubagent \\<parent\\> \\<name\\> | \\<role\\>\n\n"
            "*Skills*\n"
            "/skills — list skills\n"
            "/createskill \\<name\\> | \\<content\\> | tools\n"
            "/editskill \\<id\\> … · /deleteskill \\<id\\>\n"
            "/agentskills \\<agent\\> \\<skill...\\> — assign\n\n"
            "*Automation*\n"
            "/automate — loops, hooks, reminders\n"
            "/loop \\<minutes\\> | \\<prompt\\> — recurring\n"
            "/createhook \\<event\\> \\<action\\> | \\<text\\>\n"
            "/reminders — your reminders\n"
            "/automation — workflow skills & agents\n"
            "/copycat — desktop macros\n\n"
            "*Runtime*\n"
            "/tools — available tools\n"
            "/mcp — MCP status\n"
            "/flow — live agent/tool flow\n"
            "/logs — recent agent runs\n"
            "/shell \\<cmd\\> — admin only\n\n"
            "*Account*\n"
            "/start — welcome back\n"
            "/profile · /logout · /help\n\n"
            "_Tip: tap / below the message field to see these commands._"
        )
    return (
        "*Daffodil Intelligence — get started*\n\n"
        "*Account*\n"
        "/start — welcome & menu\n"
        "/register — Google or email OTP, then profile\n"
        "/login — Google or email, name & password\n"
        "/help — this message\n\n"
        "_During registration you can reply *skip* or send /skip for optional fields "
        "(phone, student ID, department)._\n\n"
        "You can also tap *Register* or *Login* on the keyboard.\n\n"
        "_After sign-in you unlock chat, agents, copycat, and automation._"
    )


async def sync_default_commands(bot: "Bot") -> None:
    """Set global default command menu for new private chats."""
    if BotCommand is None:
        return
    try:
        await bot.set_my_commands(_to_bot_commands(GUEST_COMMANDS))
    except Exception as e:
        logger.warning("Failed to set default Telegram commands: %s", e)


async def sync_user_commands(bot: "Bot", telegram_id: int, *, authenticated: bool) -> None:
    """Set slash-command suggestions for a private chat."""
    if BotCommand is None:
        return
    spec = AUTHENTICATED_COMMANDS if authenticated else GUEST_COMMANDS
    commands = _to_bot_commands(spec)
    try:
        from telegram import BotCommandScopeChat, MenuButtonCommands

        await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=telegram_id))
        await bot.set_chat_menu_button(
            chat_id=telegram_id,
            menu_button=MenuButtonCommands(),
        )
    except Exception as e:
        logger.warning("Failed to set Telegram commands for %s: %s", telegram_id, e)


def auth_required_message() -> str:
    return (
        "Please sign in to use Daffodil Intelligence.\n\n"
        "Tap *Register* or *Login* below, or send /register or /login.\n"
        "/help — see all commands"
    )


def default_guest_message() -> str:
    return (
        "*Welcome to Daffodil Intelligence*\n\n"
        "I did not receive a message to work with.\n\n"
        "• Tap *Register* or *Login* on the keyboard\n"
        "• Or send /start for the menu\n"
        "• /help — commands and setup guide"
    )


def default_authenticated_message() -> str:
    return (
        f"{GREETING_EN}\n\n"
        "Send me a question, photo, or voice note.\n"
        "/agent — switch agent · /help — all commands"
    )


def chat_turn_fallback_message(user_text: str) -> str:
    """Reply when the runtime returns no content (not for empty user input)."""
    from .services.chat_runtime import is_simple_greeting

    if is_simple_greeting(user_text):
        return GREETING_EN
    return "Sorry, I couldn't reply just now. Please try again in a moment."


def unsupported_media_message(*, authenticated: bool) -> str:
    if authenticated:
        return (
            "I can read *text*, *photos*, and *voice* messages.\n\n"
            "Send one of those, or use /help for commands."
        )
    return (
        "Sign in first to chat with Daffodil Intelligence.\n\n"
        "Send /register or /login — text, photos, and voice work after sign-in."
    )


def step_empty_prompt(step: str) -> str:
    """Reminder when the user sends an empty message during a guided flow."""
    prompts = {
        "auth_menu": default_guest_message(),
        "register_email": "Send your *email address* (required) to continue registration.",
        "register_otp": "Enter the *6-digit verification code* sent to your email.",
        "register_first_name": "Send your *first name* (at least 2 characters).",
        "register_last_name": "Send your *last name* (at least 2 characters).",
        "register_password": "Choose a *password* (minimum 6 characters).",
        "register_role": "Tap one of the *role* buttons above (Student, Teacher, Staff, Manager).",
        "register_phone": "Send your *phone number* (e.g. +8801XXXXXXXXX), or reply *skip* or /skip.",
        "register_student_id": "Send your *Student ID* (e.g. 221-15-1234), or reply *skip* or /skip.",
        "register_department": "Send your *department* (e.g. CSE), or reply *skip* or /skip.",
        "login_email": "Send the *email* for your account.",
        "login_first_name": "Send your *first name*.",
        "login_last_name": "Send your *last name*.",
        "login_password": "Send your *password*.",
    }
    return prompts.get(
        step,
        "Send a text message to continue, or /help for available commands.",
    )


def step_unknown_input_prompt(step: str) -> str:
    """Reminder when input does not match what the current step expects."""
    if step == "register_role":
        return step_empty_prompt(step)
    if step.startswith("register_") or step.startswith("login_"):
        return (
            f"{step_empty_prompt(step)}\n\n"
            "_Send /register or /login to restart if you are stuck._"
        )
    if step == "auth_menu":
        return default_guest_message()
    return default_authenticated_message()


def parse_inline_command(text: str) -> Optional[tuple[str, list[str]]]:
    """Parse `/command arg1 arg2` from plain text (when Telegram omits command entity)."""
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return None
    parts = raw.split()
    if not parts:
        return None
    head = parts[0].lstrip("/")
    cmd = head.split("@", 1)[0].lower()
    return cmd, parts[1:]


def parse_suggestion_text(text: str) -> Optional[str]:
    """Map reply-keyboard labels to command names (no leading slash)."""
    normalized = (text or "").strip().lower()
    aliases = {
        "register": "register",
        "login": "login",
        "help": "help",
        "profile": "profile",
        "logout": "logout",
        "start": "start",
        "recordings": "recordings",
        "agent": "agent",
        "agents": "agents",
        "skills": "skills",
        "copycat": "copycat",
        "automation": "automation",
        "automate": "automate",
        "tools": "tools",
        "flow": "flow",
        "logs": "logs",
    }
    return aliases.get(normalized)
