"""
Telegram Bot — Daffodil Intelligence
====================================
Registration: name (from Telegram) → role → phone → email → OTP → password → profile
Login: email + password, or Google via browser link.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from ...core.config import get_settings
from ...prompts.manager import GREETING_EN
from ...runtime import orchestrator
from ...memory import memory_service
from ...tools.registry import get_registry
from .profiles import (
    profile_store,
    ROLES,
    TelegramProfile,
    STEP_AUTH_MENU,
    STEP_REGISTER_ROLE,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_EMAIL,
    STEP_REGISTER_OTP,
    STEP_REGISTER_PASSWORD,
    STEP_REGISTER_STUDENT_ID,
    STEP_REGISTER_DEPARTMENT,
    STEP_LOGIN_EMAIL,
    STEP_LOGIN_PASSWORD,
    STEP_COMPLETE,
)
from .auth_store import auth_store
from .otp import otp_service
from .tokens import sign_state, frontend_base

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )
    _PTB_AVAILABLE = True
except Exception as e:  # pragma: no cover
    _PTB_AVAILABLE = False
    Update = Any  # type: ignore
    logger.warning(f"python-telegram-bot unavailable: {e}")

try:
    from google.antigravity.types import Image, Audio
    _MM_AVAILABLE = True
except Exception:
    Image = Audio = None  # type: ignore
    _MM_AVAILABLE = False


def _auth_keyboard() -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Register", callback_data="auth:register")],
        [InlineKeyboardButton("Login (email)", callback_data="auth:login")],
        [InlineKeyboardButton("Login with Google", callback_data="auth:google")],
    ])


def _role_keyboard() -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Student", callback_data="role:student"),
            InlineKeyboardButton("Teacher", callback_data="role:teacher"),
        ],
        [
            InlineKeyboardButton("Staff", callback_data="role:staff"),
            InlineKeyboardButton("Manager", callback_data="role:manager"),
        ],
    ])


def _welcome_unregistered(profile: TelegramProfile) -> str:
    name = profile.full_name or profile.first_name or "there"
    return (
        f"Welcome to *Daffodil Intelligence*, {name}!\n\n"
        "Create an account or sign in to continue.\n"
        "Your Telegram name is used automatically for registration."
    )


def _welcome_back(account) -> str:
    return (
        f"Welcome back, *{account.full_name}*!\n\n"
        f"• Email: {account.email}\n"
        f"• Role: {account.role.capitalize()}\n"
        f"• Signed in via: {account.auth_provider}\n\n"
        f"{GREETING_EN}"
    )


def _profile_summary(account) -> str:
    lines = [
        "Your account",
        f"• Name: {account.full_name}",
        f"• Email: {account.email}",
        f"• Role: {account.role.capitalize()}",
        f"• Provider: {account.auth_provider}",
    ]
    if account.phone:
        lines.append(f"• Phone: {account.phone}")
    if account.student_id:
        lines.append(f"• Student ID: {account.student_id}")
    if account.department:
        lines.append(f"• Department: {account.department}")
    return "\n".join(lines)


def _google_login_url(telegram_id: int) -> str:
    token = sign_state(telegram_id)
    return f"{frontend_base()}/api/auth/telegram/google/start?token={token}"


class TelegramBot:
    def __init__(self):
        self._app: Optional["Application"] = None
        self._started = False

    @property
    def enabled(self) -> bool:
        return bool(_PTB_AVAILABLE and settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN)

    def _allowed(self, user_id: int) -> bool:
        allow = (settings.TELEGRAM_ALLOWED_USER_IDS or "").strip()
        if not allow:
            return True
        return str(user_id) in {x.strip() for x in allow.split(",") if x.strip()}

    async def start(self):
        if not self.enabled or self._started:
            return
        self._app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self._register_handlers(self._app)
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)
        self._started = True
        logger.info("Telegram bot started (polling).")

    async def stop(self):
        if not self._started or self._app is None:
            return
        try:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
        except Exception as e:
            logger.warning(f"Telegram bot shutdown: {e}")
        finally:
            self._started = False

    def _register_handlers(self, app: "Application"):
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("login", self._cmd_login))
        app.add_handler(CommandHandler("register", self._cmd_register))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("profile", self._cmd_profile))
        app.add_handler(CommandHandler("logout", self._cmd_logout))
        app.add_handler(CallbackQueryHandler(self._on_auth_callback, pattern=r"^auth:"))
        app.add_handler(CallbackQueryHandler(self._on_role_callback, pattern=r"^role:"))
        app.add_handler(CommandHandler("recordings", self._cmd_recordings))
        app.add_handler(CommandHandler("record", self._cmd_record))
        app.add_handler(CommandHandler("replay", self._cmd_replay))
        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self._on_voice))
        app.add_handler(MessageHandler(filters.PHOTO, self._on_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_text))

    def _sync(self, update: "Update", profile: TelegramProfile) -> TelegramProfile:
        return profile.sync_telegram_names(update.effective_user)

    def _is_authenticated(self, telegram_id: int) -> bool:
        acct = auth_store.get_by_telegram_id(telegram_id)
        return acct is not None

    async def _cmd_start(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._allowed(uid):
            await update.message.reply_text("Sorry, you're not authorized.")
            return

        account = auth_store.get_by_telegram_id(uid)
        profile = profile_store.get(uid)
        self._sync(update, profile)

        if account:
            profile.step = STEP_COMPLETE
            profile_store.save(profile)
            await update.message.reply_text(_welcome_back(account), parse_mode="Markdown")
            return

        profile.step = STEP_AUTH_MENU
        profile.mode = ""
        profile_store.save(profile)
        await update.message.reply_text(
            _welcome_unregistered(profile),
            parse_mode="Markdown",
            reply_markup=_auth_keyboard(),
        )

    async def _cmd_login(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        profile = profile_store.get(uid)
        self._sync(update, profile)
        profile.step = STEP_LOGIN_EMAIL
        profile.mode = "login"
        profile_store.save(profile)
        await update.message.reply_text("Login — send your *email*:", parse_mode="Markdown")

    async def _cmd_register(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        await self._begin_register(update)

    async def _begin_register(self, update: "Update"):
        uid = update.effective_user.id
        profile = profile_store.get(uid)
        self._sync(update, profile)
        if not profile.first_name and not profile.full_name:
            await update.message.reply_text(
                "Your Telegram account must have a first name. Set it in Telegram Settings → Edit Profile."
            )
            return
        profile.mode = "register"
        profile.step = STEP_REGISTER_ROLE
        profile_store.save(profile)
        await update.message.reply_text(
            f"Registering as *{profile.full_name}*\n\nSelect your role:",
            parse_mode="Markdown",
            reply_markup=_role_keyboard(),
        )

    async def _cmd_help(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        await update.message.reply_text(
            "Daffodil Intelligence\n\n"
            "/start — home\n"
            "/register — create account (email OTP + password)\n"
            "/login — sign in with email & password\n"
            "/profile — view account\n"
            "/logout — sign out\n\n"
            "Google sign-in: tap *Login with Google* on /start."
        )

    async def _cmd_profile(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        account = auth_store.get_by_telegram_id(update.effective_user.id)
        if not account:
            await update.message.reply_text("Not registered. Send /register or /start.")
            return
        await update.message.reply_text(_profile_summary(account))

    async def _cmd_logout(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        profile_store.reset_session(uid)
        await update.message.reply_text(
            "Signed out of this device session. Your account data is kept.\n"
            "Send /login or /register to continue."
        )

    async def _on_auth_callback(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        query = update.callback_query
        await query.answer()
        uid = update.effective_user.id
        action = (query.data or "").split(":", 1)[-1]

        if action == "register":
            profile = profile_store.get(uid)
            self._sync(update, profile)
            if not profile.first_name and not profile.full_name:
                await query.edit_message_text("Set your first name in Telegram profile settings, then try again.")
                return
            profile.mode = "register"
            profile.step = STEP_REGISTER_ROLE
            profile_store.save(profile)
            await query.edit_message_text(
                f"Registering as *{profile.full_name}*\n\nSelect your role:",
                parse_mode="Markdown",
                reply_markup=_role_keyboard(),
            )
        elif action == "login":
            profile = profile_store.get(uid)
            profile.step = STEP_LOGIN_EMAIL
            profile.mode = "login"
            profile_store.save(profile)
            await query.edit_message_text("Login — send your *email*:", parse_mode="Markdown")
        elif action == "google":
            url = _google_login_url(uid)
            await query.edit_message_text(
                "Open this link in your browser to sign in with Google:\n\n"
                f"{url}\n\n"
                "After success, return here and send /start."
            )

    async def _on_role_callback(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        query = update.callback_query
        await query.answer()
        role = (query.data or "").split(":", 1)[-1]
        if role not in ROLES:
            return
        uid = update.effective_user.id
        profile = profile_store.get(uid)
        self._sync(update, profile)
        profile.role = role
        profile.step = STEP_REGISTER_PHONE
        profile_store.save(profile)
        await query.edit_message_text(
            f"Role: *{role.capitalize()}*\n\nSend your *phone number* (e.g. +8801XXXXXXXXX) or reply *skip*.",
            parse_mode="Markdown",
        )

    async def _on_text(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._allowed(uid):
            await update.message.reply_text("Not authorized.")
            return

        text = (update.message.text or "").strip()
        profile = profile_store.get(uid)
        self._sync(update, profile)

        if profile.step == STEP_AUTH_MENU:
            await update.message.reply_text("Choose an option:", reply_markup=_auth_keyboard())
            return

        if profile.step == STEP_LOGIN_EMAIL:
            if not otp_service.is_valid_email(text):
                await update.message.reply_text("Invalid email. Try again:")
                return
            profile.email = text.lower()
            profile.step = STEP_LOGIN_PASSWORD
            profile_store.save(profile)
            await update.message.reply_text("Send your *password*:", parse_mode="Markdown")
            return

        if profile.step == STEP_LOGIN_PASSWORD:
            acct = auth_store.verify_login(profile.email, text)
            if not acct:
                await update.message.reply_text("Invalid email or password. Send /login to try again.")
                profile.step = STEP_AUTH_MENU
                profile_store.save(profile)
                return
            acct.telegram_id = uid
            auth_store.save(acct)
            profile.step = STEP_COMPLETE
            profile.role = acct.role
            profile_store.save(profile)
            await update.message.reply_text(_welcome_back(acct), parse_mode="Markdown")
            return

        if profile.step == STEP_REGISTER_PHONE:
            profile.phone = "" if text.lower() == "skip" else text
            profile.step = STEP_REGISTER_EMAIL
            profile_store.save(profile)
            await update.message.reply_text(
                "Send your *email address* (required). We will send a verification code.",
                parse_mode="Markdown",
            )
            return

        if profile.step == STEP_REGISTER_EMAIL:
            if not otp_service.is_valid_email(text):
                await update.message.reply_text("Invalid email. Send a valid address:")
                return
            email = text.lower()
            if auth_store.email_taken(email):
                await update.message.reply_text("Email already registered. Use /login or another email.")
                return
            profile.email = email
            code = otp_service.generate(email)
            sent, dev_code = otp_service.send(email, code)
            profile.step = STEP_REGISTER_OTP
            profile_store.save(profile)
            if sent:
                await update.message.reply_text(
                    f"A 6-digit code was sent to *{email}*.\n\nEnter the code here:",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"Email delivery is not configured.\n\n"
                    f"Your verification code: `{dev_code}`\n\n"
                    "Enter the code here:",
                    parse_mode="Markdown",
                )
            return

        if profile.step == STEP_REGISTER_OTP:
            if not otp_service.verify(profile.email, text):
                await update.message.reply_text("Invalid or expired code. Send /register to start again.")
                return
            profile.step = STEP_REGISTER_PASSWORD
            profile_store.save(profile)
            await update.message.reply_text(
                "Email verified.\n\nChoose a *password* (minimum 6 characters):",
                parse_mode="Markdown",
            )
            return

        if profile.step == STEP_REGISTER_PASSWORD:
            if len(text) < 6:
                await update.message.reply_text("Password too short. Use at least 6 characters:")
                return
            profile.pending_password = text
            if profile.role == "student":
                profile.step = STEP_REGISTER_STUDENT_ID
                profile_store.save(profile)
                await update.message.reply_text(
                    "Send your *Student ID* (e.g. 221-15-1234) or *skip*:",
                    parse_mode="Markdown",
                )
            else:
                profile.step = STEP_REGISTER_DEPARTMENT
                profile_store.save(profile)
                await update.message.reply_text(
                    "Send your *department* (e.g. CSE) or *skip*:",
                    parse_mode="Markdown",
                )
            return

        if profile.step == STEP_REGISTER_STUDENT_ID:
            profile.student_id = "" if text.lower() == "skip" else text
            profile.step = STEP_REGISTER_DEPARTMENT
            profile_store.save(profile)
            await update.message.reply_text("Send your *department* or *skip*:", parse_mode="Markdown")
            return

        if profile.step == STEP_REGISTER_DEPARTMENT:
            profile.department = "" if text.lower() == "skip" else text
            account = auth_store.create_email_account(
                telegram_id=uid,
                email=profile.email,
                password=profile.pending_password,
                full_name=profile.full_name,
                first_name=profile.first_name,
                last_name=profile.last_name,
                username=profile.username,
                phone=profile.phone,
                role=profile.role,
                student_id=profile.student_id,
                department=profile.department,
            )
            profile.step = STEP_COMPLETE
            profile.pending_password = ""
            profile_store.save(profile)
            memory_service.remember(
                account.context_line(),
                user_id=uid,
                metadata={"source": "telegram_register", "email": account.email},
            )
            await update.message.reply_text(
                f"Registration complete!\n\n{_profile_summary(account)}\n\n{GREETING_EN}",
                parse_mode="Markdown",
            )
            return

        if not self._is_authenticated(uid):
            await update.message.reply_text("Please register or login first. Send /start")
            return

        await self._handle_chat(update, text, uid)

    async def _on_voice(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._is_authenticated(uid):
            await update.message.reply_text("Please /register or /login first.")
            return
        attachments: List[Any] = []
        if _MM_AVAILABLE:
            media = update.message.voice or update.message.audio
            data = await self._download(media, ctx)
            if data:
                mime = getattr(media, "mime_type", None) or "audio/ogg"
                attachments.append(Audio(data=data, mime_type=mime, description="Telegram voice"))
        prompt = update.message.caption or "Listen to this voice message and respond helpfully."
        await self._handle_chat(update, prompt, uid, attachments)

    async def _on_photo(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._is_authenticated(uid):
            await update.message.reply_text("Please /register or /login first.")
            return
        attachments: List[Any] = []
        if _MM_AVAILABLE and update.message.photo:
            photo = update.message.photo[-1]
            data = await self._download(photo, ctx)
            if data:
                attachments.append(Image(data=data, mime_type="image/jpeg", description="Telegram photo"))
        prompt = update.message.caption or "Describe this image and answer any implied question."
        await self._handle_chat(update, prompt, uid, attachments)

    async def _handle_chat(
        self,
        update: "Update",
        text: str,
        uid: int,
        attachments: Optional[List[Any]] = None,
    ):
        account = auth_store.get_by_telegram_id(uid)
        try:
            await update.message.chat.send_action("typing")
        except Exception:
            pass
        prefix = account.context_line() if account else ""
        augmented = f"{prefix}\n\n{text}" if prefix else text
        result = await orchestrator.run(augmented, user_id=uid, chat_id=f"tg-{uid}", attachments=attachments)
        content = result.get("content") or "(no response)"
        for chunk in _chunk(content, 4000):
            await update.message.reply_text(chunk)

    async def _cmd_recordings(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        result = await get_registry().execute("list_recordings")
        if result.success:
            recs = result.data.get("recordings", [])
            await update.message.reply_text(
                "No recordings yet." if not recs else "Recordings:\n" + "\n".join(
                    f"• {r['name']}" for r in recs
                )
            )
        else:
            await update.message.reply_text(f"Error: {result.error}")

    async def _cmd_record(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        args = ctx.args or []
        if args and args[0] == "stop":
            result = await get_registry().execute("stop_recording")
            msg = f"Saved: {result.data}" if result.success else f"Error: {result.error}"
        else:
            result = await get_registry().execute("start_recording", name=args[0] if args else None)
            msg = "Recording started. /record stop to finish." if result.success else f"Error: {result.error}"
        await update.message.reply_text(msg)

    async def _cmd_replay(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: /replay <name> [speed]")
            return
        result = await get_registry().execute("replay_recording", name=args[0], speed=float(args[1]) if len(args) > 1 else 1.0)
        await update.message.reply_text("Done." if result.success else f"Error: {result.error}")

    async def _download(self, media, ctx: "ContextTypes.DEFAULT_TYPE") -> Optional[bytes]:
        try:
            tg_file = await ctx.bot.get_file(media.file_id)
            return bytes(await tg_file.download_as_bytearray())
        except Exception as e:
            logger.warning(f"Media download failed: {e}")
            return None


def _chunk(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i + size]


telegram_bot = TelegramBot()
