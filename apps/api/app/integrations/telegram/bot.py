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
from ...skills.store import global_config_store
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
from .otp import otp_service
from .tokens import sign_state, frontend_base

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from telegram import (
        Update,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
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


def _google_login_button(telegram_id: int) -> "InlineKeyboardButton":
    return InlineKeyboardButton("Login with Google", url=_google_login_url(telegram_id))


def _login_keyboard(telegram_id: int) -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Email & password", callback_data="auth:login_email")],
        [_google_login_button(telegram_id)],
        [InlineKeyboardButton("Back", callback_data="auth:menu")],
    ])


def _auth_keyboard(telegram_id: int) -> "InlineKeyboardMarkup":
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Register", callback_data="auth:register")],
        [InlineKeyboardButton("Login", callback_data="auth:login_menu")],
    ])


def _auth_suggestion_keyboard() -> "ReplyKeyboardMarkup":
    """Persistent bottom buttons for first-time / logged-out users."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Register"), KeyboardButton("Login")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Tap Register or Login to continue…",
    )


def _clear_suggestion_keyboard() -> "ReplyKeyboardRemove":
    return ReplyKeyboardRemove()


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
        "Tap *Register* or *Login* on the keyboard below to get started.\n"
        "• *Register* — email verification (OTP) + profile setup\n"
        "• *Login* — Google or email, first name, last name & password"
    )


def _login_menu_text() -> str:
    return (
        "*Sign in to Daffodil Intelligence*\n\n"
        "Choose how you want to log in:\n"
        "• *Email & password* — email, first name, last name, and password\n"
        "• *Login with Google* — opens secure Google sign-in in your browser"
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


def _google_login_url(telegram_id: int) -> str:
    token = sign_state(telegram_id)
    return f"{frontend_base()}/api/auth/telegram/google/start?token={token}"


def _valid_person_name(name: str) -> bool:
    return len(name.strip()) >= 2


def _register_start_text() -> str:
    return (
        "*Register for Daffodil Intelligence*\n\n"
        "Send your *email address* (required).\n"
        "We will send a one-time verification code — registration continues only after you enter the correct OTP."
    )


async def _send_register_otp(update: "Update", profile: TelegramProfile, email: str) -> None:
    code = otp_service.generate(email)
    sent, dev_code = otp_service.send(email, code)
    profile.email = email
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

    async def _cmd_login(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if auth_store.get_by_telegram_id(uid):
            await update.message.reply_text("You are already signed in. Send /start or /logout.")
            return
        profile = profile_store.get(uid)
        self._sync(update, profile)
        await self._show_login_menu(update, uid)

    async def _cmd_register(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        await self._begin_register(update)

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
        await update.message.reply_text(
            "Daffodil Intelligence\n\n"
            "/start — home\n"
            "/register — create account (email OTP + password)\n"
            "/login — sign in (Google or email & password)\n"
            "/profile — view account\n"
            "/logout — sign out\n\n"
            "You can use *Google* or *email & password* — both work on /login."
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

    async def _on_auth_callback(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        query = update.callback_query
        await query.answer()
        uid = update.effective_user.id
        action = (query.data or "").split(":", 1)[-1]

        if action == "register":
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
                "You will also need your *first name*, *last name*, and *password*.",
                parse_mode="Markdown",
            )
        elif action == "google":
            await query.edit_message_text(
                "Tap *Login with Google* below to open secure sign-in in your browser.\n\n"
                "After success, return to Telegram — you will get a confirmation message.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_google_login_button(uid)]]),
            )
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

        if text.lower() in ("login", "/login"):
            if auth_store.get_by_telegram_id(uid):
                await update.message.reply_text("You are already signed in. Send /start or /logout.")
                return
            await self._show_login_menu(update, uid)
            return

        if profile.step == STEP_AUTH_MENU:
            choice = text.lower()
            if choice == "register":
                await self._begin_register(update)
                return
            if choice == "login":
                await self._show_login_menu(update, uid)
                return
            await self._prompt_first_time_auth(update, profile, uid)
            return

        if profile.step == STEP_LOGIN_EMAIL:
            if not otp_service.is_valid_email(text):
                await update.message.reply_text("Invalid email. Try again:")
                return
            email = text.lower()
            status = auth_store.login_email_status(email)
            if status == "not_found":
                await update.message.reply_text(
                    "No account with this email.\n\nSend /register to create one, or try another email.",
                    reply_markup=_login_keyboard(uid),
                )
                profile.step = STEP_AUTH_MENU
                profile_store.save(profile)
                return
            if status == "google_only":
                profile.email = email
                profile.step = STEP_AUTH_MENU
                profile_store.save(profile)
                await update.message.reply_text(
                    f"*{email}* is registered with *Google sign-in*.\n\n"
                    "Tap the button below to continue with Google:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[_google_login_button(uid)]]),
                )
                return
            profile.email = email
            profile.step = STEP_LOGIN_FIRST_NAME
            profile_store.save(profile)
            await update.message.reply_text("Send your *first name*:", parse_mode="Markdown")
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
            acct = auth_store.verify_login_with_names(
                profile.email,
                text,
                profile.first_name,
                profile.last_name,
            )
            if not acct:
                await update.message.reply_text(
                    "Incorrect email, name, or password. Try again or send /login to restart.",
                    reply_markup=_login_keyboard(uid),
                )
                profile.step = STEP_LOGIN_EMAIL
                profile_store.save(profile)
                await update.message.reply_text("Send your *email* again:", parse_mode="Markdown")
                return
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

        if not self._is_authenticated(uid):
            profile.step = STEP_AUTH_MENU
            profile_store.save(profile)
            await self._prompt_first_time_auth(update, profile, uid)
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
        agent_id = global_config_store.get().default_agent_id
        result = await run_turn(
            text,
            user_id=uid,
            chat_id=f"tg-{uid}",
            agent_id=agent_id,
            context_prefix=prefix,
            attachments=attachments,
        )
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
            if result.success:
                skill = (result.data or {}).get("skill")
                msg = f"Saved: {result.data.get('name')} ({result.data.get('action_count')} actions)"
                if skill:
                    msg += f"\nSkill auto-created: {skill.get('name')}"
            else:
                msg = f"Error: {result.error}"
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
