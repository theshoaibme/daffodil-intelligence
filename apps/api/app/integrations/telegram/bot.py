"""
Telegram Bot — Daffodil Intelligence
====================================
Registration: email → OTP → first name → last name → password → role → profile
Login: email → first name → last name → password, or Google via browser link.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from ...core.config import get_settings
from ...prompts.manager import GREETING_EN
from ...runtime.pipeline import run_turn
from ...memory import memory_service
from .profiles import (
    profile_store,
    ROLES,
    TelegramProfile,
    STEP_AUTH_MENU,
    STEP_REGISTER_ROLE,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_EMAIL,
    STEP_REGISTER_OTP,
    STEP_REGISTER_FIRST_NAME,
    STEP_REGISTER_LAST_NAME,
    STEP_REGISTER_PASSWORD,
    STEP_REGISTER_STUDENT_ID,
    STEP_REGISTER_DEPARTMENT,
    STEP_LOGIN_EMAIL,
    STEP_LOGIN_FIRST_NAME,
    STEP_LOGIN_LAST_NAME,
    STEP_LOGIN_PASSWORD,
    STEP_COMPLETE,
)
from .auth_store import auth_store
from .web_auth import resolve_login_email_status, verify_web_password_login
from .commands import (
    auth_required_message,
    default_authenticated_message,
    default_guest_message,
    help_text,
    parse_suggestion_text,
    step_empty_prompt,
    step_unknown_input_prompt,
    sync_default_commands,
    sync_user_commands,
    unsupported_media_message,
)
from .handlers.registry import register_product_handlers
from .keyboards import (
    auth_keyboard as _auth_keyboard,
    auth_suggestion_keyboard as _auth_suggestion_keyboard,
    clear_suggestion_keyboard as _clear_suggestion_keyboard,
    google_auth_button as _google_auth_button,
    login_keyboard as _login_keyboard,
    register_keyboard as _register_keyboard,
    role_keyboard as _role_keyboard,
)
from .otp import otp_service
from .services.agents import resolve_agent_id
from .tokens import google_login_url, is_telegram_inline_url

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from telegram import (
        Update,
        InlineKeyboardMarkup,
    )
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


def _welcome_unregistered(profile: TelegramProfile) -> str:
    name = profile.full_name or profile.first_name or "there"
    return (
        f"Welcome to *Daffodil Intelligence*, {name}!\n\n"
        "Tap *Register* or *Login* on the keyboard below to get started.\n"
        "• *Register* — Google or email (OTP) + profile setup\n"
        "• *Login* — Google or email & password"
    )


def _login_menu_text() -> str:
    return (
        "*Sign in to Daffodil Intelligence*\n\n"
        "Choose how you want to log in:\n"
        "• *Email & password* — email, first name, last name, and password\n"
        "• *Login with Google* — opens secure Google sign-in in your browser"
    )


def _register_menu_text() -> str:
    return (
        "*Register for Daffodil Intelligence*\n\n"
        "Choose how you want to sign up:\n"
        "• *Email & password* — OTP verification, then profile setup\n"
        "• *Register with Google* — quick sign-up in your browser"
    )


def _auth_card_caption(
    account,
    title: str = "Login successful",
    *,
    welcome_back: bool = False,
) -> str:
    if welcome_back:
        return f"👋 *Welcome back, {account.full_name}!*"
    return (
        f"✅ *{title}*\n\n"
        f"👤 *{account.full_name}*\n"
        f"📧 `{account.email}`"
    )


async def send_auth_welcome(
    bot,
    chat_id: int,
    account,
    *,
    title: str = "Login successful",
    welcome_back: bool = False,
    photo_url: Optional[str] = None,
    telegram_id: Optional[int] = None,
) -> None:
    """Send profile photo card, then greeting as two separate messages."""
    caption = _auth_card_caption(account, title=title, welcome_back=welcome_back)
    sent_photo = False

    photo_candidates = [p for p in (photo_url, getattr(account, "avatar_url", "")) if p]
    for candidate in photo_candidates:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=candidate,
                caption=caption,
                parse_mode="Markdown",
            )
            sent_photo = True
            break
        except Exception as e:
            logger.warning("Profile photo send failed (%s): %s", candidate[:40], e)

    if not sent_photo and telegram_id:
        try:
            photos = await bot.get_user_profile_photos(telegram_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=caption,
                    parse_mode="Markdown",
                )
                sent_photo = True
        except Exception as e:
            logger.warning("Telegram profile photo send failed: %s", e)

    if not sent_photo:
        await bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown")

    await bot.send_message(
        chat_id=chat_id,
        text=GREETING_EN,
        reply_markup=_clear_suggestion_keyboard(),
    )
    await sync_user_commands(bot, chat_id, authenticated=True)


def _profile_summary(account) -> str:
    lines = [
        "Your account",
        f"• Name: {account.full_name}",
        f"• Email: {account.email}",
        f"• Role: {account.role.capitalize()}",
        f"• Sign-in: {_provider_label(account.auth_provider)}",
    ]
    if account.phone:
        lines.append(f"• Phone: {account.phone}")
    if account.student_id:
        lines.append(f"• Student ID: {account.student_id}")
    if account.department:
        lines.append(f"• Department: {account.department}")
    return "\n".join(lines)


def _provider_label(provider: str) -> str:
    return {
        "email": "Email & password",
        "google": "Google",
        "both": "Google + email & password",
    }.get(provider, provider)


async def _reply_google_auth_prompt(query, uid: int, *, register: bool) -> None:
    label = "Register with Google" if register else "Login with Google"
    url = google_login_url(uid)
    if is_telegram_inline_url(url):
        await query.edit_message_text(
            f"Tap *{label}* below to continue in your browser.\n\n"
            "After success, return to Telegram for confirmation.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_google_auth_button(uid, label=label)]]),
        )
        return
    await query.edit_message_text(
        f"*{label}*\n\n"
        "Open this link in your browser:\n"
        f"`{url}`\n\n"
        "_Tip: set `TELEGRAM_OAUTH_PUBLIC_URL` to a public HTTPS URL in API .env for one-tap buttons._",
        parse_mode="Markdown",
    )


def _valid_person_name(name: str) -> bool:
    return len(name.strip()) >= 2


_AUTH_FLOW_STEPS = frozenset({
    STEP_REGISTER_EMAIL,
    STEP_REGISTER_OTP,
    STEP_REGISTER_FIRST_NAME,
    STEP_REGISTER_LAST_NAME,
    STEP_REGISTER_PASSWORD,
    STEP_REGISTER_ROLE,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_STUDENT_ID,
    STEP_REGISTER_DEPARTMENT,
    STEP_LOGIN_EMAIL,
    STEP_LOGIN_FIRST_NAME,
    STEP_LOGIN_LAST_NAME,
    STEP_LOGIN_PASSWORD,
})


def _in_auth_flow(profile: TelegramProfile) -> bool:
    return profile.step in _AUTH_FLOW_STEPS


def _register_start_text() -> str:
    return (
        "*Register for Daffodil Intelligence*\n\n"
        "Send your *email address* (required).\n"
        "We will send a one-time verification code — registration continues only after you enter the correct OTP."
    )


async def _send_register_otp(update: "Update", profile: TelegramProfile, email: str) -> None:
    code = otp_service.generate(email)
    result = otp_service.deliver(email, code)
    if result.sent:
        profile.email = email
        profile.step = STEP_REGISTER_OTP
        profile_store.save(profile)
        await update.message.reply_text(
            f"A 6-digit code was sent to *{email}*.\n\nEnter the code here:",
            parse_mode="Markdown",
        )
        return
    if result.dev_code:
        profile.email = email
        profile.step = STEP_REGISTER_OTP
        profile_store.save(profile)
        await update.message.reply_text(
            f"*Development mode* — configure SMTP or Resend to send real email.\n\n"
            f"Your verification code: `{result.dev_code}`\n\n"
            "Enter the code here:",
            parse_mode="Markdown",
        )
        return
    await update.message.reply_text(
        "Could not send the verification email. Please try again in a few minutes.",
        reply_markup=_auth_suggestion_keyboard(),
    )


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
        async def _post_init(app: "Application") -> None:
            await sync_default_commands(app.bot)

        self._app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .post_init(_post_init)
            .build()
        )
        self._register_handlers(self._app)
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)
        self._started = True
        logger.debug("Telegram bot polling active.")

    async def notify_login_success(
        self,
        telegram_id: int,
        account,
        *,
        photo_url: Optional[str] = None,
    ) -> None:
        if not self._app or not self._app.bot:
            return
        await send_auth_welcome(
            self._app.bot,
            telegram_id,
            account,
            title="Login successful",
            photo_url=photo_url,
            telegram_id=telegram_id,
        )

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
        register_product_handlers(app, self)
        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self._on_voice))
        app.add_handler(MessageHandler(filters.PHOTO, self._on_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_text))
        app.add_handler(MessageHandler(filters.COMMAND, self._on_unknown_command))
        unsupported = (
            filters.Sticker.ALL
            | filters.Document.ALL
            | filters.VIDEO
            | filters.ANIMATION
            | filters.CONTACT
            | filters.LOCATION
            | filters.VENUE
        )
        app.add_handler(MessageHandler(unsupported, self._on_unsupported))

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
            await send_auth_welcome(
                ctx.bot,
                uid,
                account,
                welcome_back=True,
                telegram_id=uid,
            )
            return

        profile.step = STEP_AUTH_MENU
        profile.mode = ""
        profile_store.save(profile)
        await self._prompt_first_time_auth(update, profile, uid)

    async def _prompt_first_time_auth(self, update: "Update", profile: TelegramProfile, uid: int):
        await update.message.reply_text(
            _welcome_unregistered(profile),
            parse_mode="Markdown",
            reply_markup=_auth_suggestion_keyboard(),
        )
        try:
            await sync_user_commands(update.get_bot(), uid, authenticated=False)
        except Exception:
            pass

    async def _show_login_menu(self, update: "Update", uid: int):
        profile = profile_store.get(uid)
        profile.step = STEP_AUTH_MENU
        profile.mode = "login"
        profile_store.save(profile)
        await update.message.reply_text(
            _login_menu_text(),
            parse_mode="Markdown",
            reply_markup=_login_keyboard(uid),
        )

    async def _show_register_menu(self, update: "Update", uid: int):
        profile = profile_store.get(uid)
        profile.step = STEP_AUTH_MENU
        profile.mode = "register"
        profile_store.save(profile)
        await update.message.reply_text(
            _register_menu_text(),
            parse_mode="Markdown",
            reply_markup=_register_keyboard(uid),
        )

    async def _on_unknown_command(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        raw = (update.message.text or "").strip().split()[0].lower().lstrip("/")
        if raw in ("loginn", "loging", "signin"):
            await self._cmd_login(update, ctx)
            return
        if raw in ("registerr", "signup", "sign-up"):
            await self._cmd_register(update, ctx)
            return
        await update.message.reply_text("Unknown command. Send /help to see available commands.")

    async def _handle_login_email(
        self,
        update: "Update",
        profile: TelegramProfile,
        uid: int,
        email: str,
    ):
        status, web_only = await resolve_login_email_status(email)
        if status == "not_found":
            await update.message.reply_text(
                "No account with this email.\n\nSend /register to create one, or try another email.",
                reply_markup=_login_keyboard(uid),
            )
            profile.step = STEP_AUTH_MENU
            profile.mode = "login"
            profile_store.save(profile)
            return
        if status == "google_only":
            profile.email = email
            profile.step = STEP_AUTH_MENU
            profile.mode = "login"
            profile_store.save(profile)
            await update.message.reply_text(
                f"*{email}* is registered with *Google sign-in*.\n\n"
                "Tap the button below to continue with Google:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_google_auth_button(uid, label="Login with Google")]]),
            )
            return
        profile.email = email
        profile.mode = "login"
        if web_only:
            profile.first_name = ""
            profile.last_name = ""
            profile.step = STEP_LOGIN_PASSWORD
            profile_store.save(profile)
            await update.message.reply_text(
                "Web account found. Send your *password*:",
                parse_mode="Markdown",
            )
            return
        profile.step = STEP_LOGIN_FIRST_NAME
        profile_store.save(profile)
        await update.message.reply_text("Send your *first name*:", parse_mode="Markdown")

    async def _finish_login(
        self,
        update: "Update",
        ctx: "ContextTypes.DEFAULT_TYPE",
        profile: TelegramProfile,
        uid: int,
        acct,
    ):
        acct.telegram_id = uid
        auth_store.save(acct)
        profile.step = STEP_COMPLETE
        profile.role = acct.role
        profile.email = acct.email
        profile.full_name = acct.full_name
        profile_store.save(profile)
        await memory_service.remember(
            acct.context_line(),
            user_id=uid,
            metadata={"source": "telegram_login", "email": acct.email},
        )
        await send_auth_welcome(
            ctx.bot,
            uid,
            acct,
            title="Login successful",
            telegram_id=uid,
        )

    async def _cmd_login(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if auth_store.get_by_telegram_id(uid):
            await update.message.reply_text("You are already signed in. Send /start or /logout.")
            return
        profile = profile_store.get(uid)
        self._sync(update, profile)
        await self._show_login_menu(update, uid)

    async def _cmd_register(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if auth_store.get_by_telegram_id(uid):
            await update.message.reply_text("You are already signed in. Send /start or /profile.")
            return
        await self._show_register_menu(update, uid)

    async def _begin_register(self, update: "Update"):
        uid = update.effective_user.id
        profile = profile_store.get(uid)
        self._sync(update, profile)
        profile.mode = "register"
        profile.step = STEP_REGISTER_EMAIL
        profile.email = ""
        profile.pending_password = ""
        profile_store.save(profile)
        await update.message.reply_text(
            _register_start_text(),
            parse_mode="Markdown",
            reply_markup=_clear_suggestion_keyboard(),
        )

    async def _cmd_help(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        authed = self._is_authenticated(uid)
        await update.message.reply_text(
            help_text(authenticated=authed),
            parse_mode="Markdown",
        )

    async def _cmd_profile(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        account = auth_store.get_by_telegram_id(update.effective_user.id)
        if not account:
            await update.message.reply_text("Not registered. Send /register or /start.")
            return
        await update.message.reply_text(_profile_summary(account))

    async def _cmd_logout(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        auth_store.detach_telegram_session(uid)
        profile = profile_store.reset_session(uid)
        self._sync(update, profile)
        await update.message.reply_text(
            "Signed out of this device session. Your account data is kept.\n"
            "Send /login or /register to continue.",
            reply_markup=_auth_suggestion_keyboard(),
        )
        try:
            await sync_user_commands(ctx.bot, uid, authenticated=False)
        except Exception:
            pass

    async def _on_auth_callback(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        query = update.callback_query
        await query.answer()
        uid = update.effective_user.id
        action = (query.data or "").split(":", 1)[-1]

        if action == "register":
            profile = profile_store.get(uid)
            profile.mode = "register"
            profile.step = STEP_AUTH_MENU
            profile_store.save(profile)
            await query.edit_message_text(
                _register_menu_text(),
                parse_mode="Markdown",
                reply_markup=_register_keyboard(uid),
            )
        elif action == "register_email":
            profile = profile_store.get(uid)
            self._sync(update, profile)
            profile.mode = "register"
            profile.step = STEP_REGISTER_EMAIL
            profile.email = ""
            profile.pending_password = ""
            profile_store.save(profile)
            await query.edit_message_text(
                _register_start_text(),
                parse_mode="Markdown",
            )
            await query.message.reply_text(
                "Send your email address in chat to continue.",
                reply_markup=_clear_suggestion_keyboard(),
            )
        elif action == "login_menu":
            profile = profile_store.get(uid)
            profile.mode = "login"
            profile.step = STEP_AUTH_MENU
            profile_store.save(profile)
            await query.edit_message_text(
                _login_menu_text(),
                parse_mode="Markdown",
                reply_markup=_login_keyboard(uid),
            )
        elif action == "login_email":
            profile = profile_store.get(uid)
            profile.step = STEP_LOGIN_EMAIL
            profile.mode = "login"
            profile_store.save(profile)
            await query.edit_message_text(
                "Email login — send your *email address*.\n\n"
                "Web accounts: email + password.\n"
                "Telegram accounts: email, name, and password.",
                parse_mode="Markdown",
            )
        elif action == "google":
            profile = profile_store.get(uid)
            await _reply_google_auth_prompt(query, uid, register=profile.mode == "register")
        elif action == "menu":
            profile = profile_store.get(uid)
            profile.step = STEP_AUTH_MENU
            profile.mode = ""
            profile_store.save(profile)
            self._sync(update, profile)
            await query.edit_message_text(
                _welcome_unregistered(profile),
                parse_mode="Markdown",
                reply_markup=_auth_keyboard(uid),
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

        if not text:
            if self._is_authenticated(uid) and profile.step == STEP_COMPLETE:
                await update.message.reply_text(
                    default_authenticated_message(),
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    step_empty_prompt(profile.step),
                    parse_mode="Markdown",
                )
            return

        quick = parse_suggestion_text(text)
        if quick == "help":
            await self._cmd_help(update, ctx)
            return
        if quick == "profile":
            await self._cmd_profile(update, ctx)
            return
        if quick == "logout":
            await self._cmd_logout(update, ctx)
            return
        if quick == "start":
            await self._cmd_start(update, ctx)
            return
        if quick == "login":
            if auth_store.get_by_telegram_id(uid):
                await update.message.reply_text("You are already signed in. Send /start or /logout.")
                return
            await self._show_login_menu(update, uid)
            return
        if quick == "register":
            if auth_store.get_by_telegram_id(uid):
                await update.message.reply_text("You are already signed in. Send /start or /profile.")
                return
            await self._show_register_menu(update, uid)
            return
        if quick == "recordings" and self._is_authenticated(uid):
            from .handlers.copycat import CopycatHandlers

            await CopycatHandlers(self).cmd_recordings(update, ctx)
            return
        if quick == "agent" and self._is_authenticated(uid):
            from .handlers.agents import AgentHandlers

            await AgentHandlers(self).cmd_agent(update, ctx)
            return
        if quick == "copycat" and self._is_authenticated(uid):
            from .handlers.copycat import CopycatHandlers

            await CopycatHandlers(self).cmd_copycat(update, ctx)
            return
        if quick == "automation" and self._is_authenticated(uid):
            from .handlers.automation import AutomationHandlers

            await AutomationHandlers(self).cmd_automation(update, ctx)
            return

        if profile.step == STEP_AUTH_MENU:
            if quick in ("register", "login"):
                return
            if profile.mode == "login":
                if otp_service.is_valid_email(text):
                    await self._handle_login_email(update, profile, uid, text.lower())
                else:
                    await update.message.reply_text(
                        "Send your *email* to sign in, or use the buttons above.",
                        parse_mode="Markdown",
                        reply_markup=_login_keyboard(uid),
                    )
                return
            if profile.mode == "register":
                if otp_service.is_valid_email(text):
                    email = text.lower()
                    if auth_store.email_taken(email):
                        await update.message.reply_text(
                            "Email already registered. Use /login or another email.",
                            reply_markup=_register_keyboard(uid),
                        )
                        return
                    await _send_register_otp(update, profile, email)
                else:
                    await update.message.reply_text(
                        "Send your *email* to register, or use the buttons above.",
                        parse_mode="Markdown",
                        reply_markup=_register_keyboard(uid),
                    )
                return
            await self._prompt_first_time_auth(update, profile, uid)
            return

        if profile.step == STEP_LOGIN_EMAIL:
            if not otp_service.is_valid_email(text):
                await update.message.reply_text("Invalid email. Try again:")
                return
            await self._handle_login_email(update, profile, uid, text.lower())
            return

        if profile.step == STEP_LOGIN_FIRST_NAME:
            if not _valid_person_name(text):
                await update.message.reply_text("First name is required (at least 2 characters). Try again:")
                return
            profile.first_name = text.strip()
            profile.step = STEP_LOGIN_LAST_NAME
            profile_store.save(profile)
            await update.message.reply_text("Send your *last name*:", parse_mode="Markdown")
            return

        if profile.step == STEP_LOGIN_LAST_NAME:
            if not _valid_person_name(text):
                await update.message.reply_text("Last name is required (at least 2 characters). Try again:")
                return
            profile.last_name = text.strip()
            profile.full_name = f"{profile.first_name} {profile.last_name}".strip()
            profile.step = STEP_LOGIN_PASSWORD
            profile_store.save(profile)
            await update.message.reply_text("Send your *password*:", parse_mode="Markdown")
            return

        if profile.step == STEP_LOGIN_PASSWORD:
            acct = None
            if profile.first_name and profile.last_name:
                acct = auth_store.verify_login_with_names(
                    profile.email,
                    text,
                    profile.first_name,
                    profile.last_name,
                )
            else:
                acct = auth_store.verify_login(profile.email, text)
                if not acct:
                    acct = await verify_web_password_login(
                        telegram_id=uid,
                        email=profile.email,
                        password=text,
                        username=profile.username,
                    )
            if not acct:
                await update.message.reply_text(
                    "Incorrect email or password. Try again or send /login to restart.",
                    reply_markup=_login_keyboard(uid),
                )
                profile.step = STEP_LOGIN_EMAIL
                profile_store.save(profile)
                await update.message.reply_text("Send your *email* again:", parse_mode="Markdown")
                return
            await self._finish_login(update, ctx, profile, uid, acct)
            return

        if profile.step == STEP_REGISTER_EMAIL:
            if not otp_service.is_valid_email(text):
                await update.message.reply_text("Invalid email. Send a valid address:")
                return
            email = text.lower()
            if auth_store.email_taken(email):
                await update.message.reply_text("Email already registered. Use /login or another email.")
                return
            await _send_register_otp(update, profile, email)
            return

        if profile.step == STEP_REGISTER_OTP:
            if not otp_service.verify(profile.email, text):
                await update.message.reply_text(
                    "Invalid or expired code. Send /register to start again with your email."
                )
                return
            profile.step = STEP_REGISTER_FIRST_NAME
            profile_store.save(profile)
            await update.message.reply_text(
                "Email verified.\n\nSend your *first name* (required):",
                parse_mode="Markdown",
            )
            return

        if profile.step == STEP_REGISTER_FIRST_NAME:
            if not _valid_person_name(text):
                await update.message.reply_text("First name is required (at least 2 characters). Try again:")
                return
            profile.first_name = text.strip()
            profile.step = STEP_REGISTER_LAST_NAME
            profile_store.save(profile)
            await update.message.reply_text("Send your *last name* (required):", parse_mode="Markdown")
            return

        if profile.step == STEP_REGISTER_LAST_NAME:
            if not _valid_person_name(text):
                await update.message.reply_text("Last name is required (at least 2 characters). Try again:")
                return
            profile.last_name = text.strip()
            profile.full_name = f"{profile.first_name} {profile.last_name}".strip()
            profile.step = STEP_REGISTER_PASSWORD
            profile_store.save(profile)
            await update.message.reply_text(
                "Choose a *password* (minimum 6 characters):",
                parse_mode="Markdown",
            )
            return

        if profile.step == STEP_REGISTER_PASSWORD:
            if len(text) < 6:
                await update.message.reply_text("Password too short. Use at least 6 characters:")
                return
            profile.pending_password = text
            profile.step = STEP_REGISTER_ROLE
            profile_store.save(profile)
            await update.message.reply_text(
                "Select your *role*:",
                parse_mode="Markdown",
                reply_markup=_role_keyboard(),
            )
            return

        if profile.step == STEP_REGISTER_ROLE:
            await update.message.reply_text(
                step_empty_prompt(STEP_REGISTER_ROLE),
                parse_mode="Markdown",
                reply_markup=_role_keyboard(),
            )
            return

        if profile.step == STEP_REGISTER_PHONE:
            profile.phone = "" if text.lower() == "skip" else text
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
            await memory_service.remember(
                account.context_line(),
                user_id=uid,
                metadata={"source": "telegram_register", "email": account.email},
            )
            await send_auth_welcome(
                ctx.bot,
                uid,
                account,
                title="Registration complete",
                telegram_id=uid,
            )
            return

        if _in_auth_flow(profile):
            await update.message.reply_text(
                step_unknown_input_prompt(profile.step),
                parse_mode="Markdown",
            )
            return

        if not self._is_authenticated(uid):
            profile.step = STEP_AUTH_MENU
            profile_store.save(profile)
            await self._prompt_first_time_auth(update, profile, uid)
            return

        await self._handle_chat(update, text, uid)

    async def _on_unsupported(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._allowed(uid):
            await update.message.reply_text("Not authorized.")
            return
        authed = self._is_authenticated(uid)
        await update.message.reply_text(
            unsupported_media_message(authenticated=authed),
            parse_mode="Markdown",
        )
        if not authed:
            await update.message.reply_text(
                auth_required_message(),
                parse_mode="Markdown",
                reply_markup=_auth_suggestion_keyboard(),
            )

    async def _on_voice(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._is_authenticated(uid):
            await update.message.reply_text(
                auth_required_message(),
                parse_mode="Markdown",
                reply_markup=_auth_suggestion_keyboard(),
            )
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
            await update.message.reply_text(
                auth_required_message(),
                parse_mode="Markdown",
                reply_markup=_auth_suggestion_keyboard(),
            )
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
        if not (text or "").strip() and not attachments:
            await update.message.reply_text(
                default_authenticated_message(),
                parse_mode="Markdown",
            )
            return

        account = auth_store.get_by_telegram_id(uid)
        try:
            await update.message.chat.send_action("typing")
        except Exception:
            pass
        prefix = account.context_line() if account else ""
        profile = profile_store.get(uid)
        agent_id = resolve_agent_id(profile)
        result = await run_turn(
            text,
            user_id=uid,
            chat_id=f"tg-{uid}",
            agent_id=agent_id,
            context_prefix=prefix,
            attachments=attachments,
        )
        content = (result.get("content") or "").strip()
        if not content:
            content = default_authenticated_message()
        for chunk in _chunk(content, 4000):
            await update.message.reply_text(chunk)

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
