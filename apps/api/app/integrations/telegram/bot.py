"""
Telegram Bot — Daffodil Intelligence
====================================
Auth flows live in this module; product commands are in ``handlers/``:
  /agent, /copycat, /automation (+ legacy /record, /recordings, /replay).
"""

from __future__ import annotations

import logging
import time
from types import SimpleNamespace
from typing import Any, List, Optional

from ...core.config import get_settings
from ...prompts.manager import GREETING_EN
from ...memory import memory_service
from ...runtime.pipeline import run_turn, run_turn_stream
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
    chat_turn_fallback_message,
    default_authenticated_message,
    default_guest_message,
    help_text,
    parse_inline_command,
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
from .queue import QueuedOutbound, outbound_queue
from .services.agents import resolve_agent_id
from .services.chat_runtime import build_telegram_turn
from .services.registration import is_skip_input
from .tokens import google_login_url, google_oauth_menu_hint, google_oauth_uses_inline_url, is_telegram_inline_url

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
        TypeHandler,
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


def _login_menu_text(telegram_id: int) -> str:
    return (
        "*Sign in to Daffodil Intelligence*\n\n"
        "Choose how you want to log in:\n"
        "• *Email & password* — email, first name, last name, and password\n"
        "• *Login with Google* — secure sign-in in your browser"
        f"{google_oauth_menu_hint(telegram_id)}"
    )


def _register_menu_text(telegram_id: int) -> str:
    return (
        "*Register for Daffodil Intelligence*\n\n"
        "Choose how you want to sign up:\n"
        "• *Email & password* — OTP verification, then profile setup\n"
        "• *Register with Google* — quick sign-up in your browser"
        f"{google_oauth_menu_hint(telegram_id)}"
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
    if google_oauth_uses_inline_url():
        await query.edit_message_text(
            f"Tap *{label}* below to continue in your browser.\n\n"
            "After success, return to Telegram for confirmation.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_google_auth_button(uid, label=label)]]),
        )
        return
    await query.message.reply_text(
        f"{label}\n\nOpen this link to continue:\n{url}\n\n"
        "After Google sign-in, return to Telegram.",
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
        "We will send a one-time verification code — registration continues only after you enter the correct OTP.\n\n"
        "_Optional later: phone, student ID, department — reply *skip* or /skip on those steps._"
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
        self._online_at: float = 0.0
        self._backlog_notified: set[int] = set()

    @property
    def enabled(self) -> bool:
        return bool(_PTB_AVAILABLE and settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN)

    def _allowed(self, user_id: int) -> bool:
        allow = (settings.TELEGRAM_ALLOWED_USER_IDS or "").strip()
        if not allow:
            return True
        return str(user_id) in {x.strip() for x in allow.split(",") if x.strip()}

    def _is_admin(self, user_id: int) -> bool:
        admins = (settings.TELEGRAM_ADMIN_USER_IDS or "").strip()
        if not admins:
            return False
        return str(user_id) in {x.strip() for x in admins.split(",") if x.strip()}

    def _ready_for_sends(self) -> bool:
        return bool(self._started and self._app and self._app.bot)

    async def start(self):
        if not self.enabled or self._started:
            return
        async def _post_init(app: "Application") -> None:
            await sync_default_commands(app.bot)

        self._app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .concurrent_updates(False)
            .post_init(_post_init)
            .build()
        )
        self._register_handlers(self._app)
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(
            drop_pending_updates=settings.TELEGRAM_DROP_PENDING_UPDATES,
        )
        self._online_at = time.time()
        self._backlog_notified.clear()
        self._started = True
        pending_outbound = outbound_queue.size()
        logger.info(
            "Telegram bot online — processing queued updates one by one"
            + (f" ({pending_outbound} outbound queued)" if pending_outbound else "")
        )
        await self._drain_outbound_queue()
        logger.debug("Telegram bot polling active.")

    async def _drain_outbound_queue(self) -> None:
        if not self._app or not self._app.bot:
            return
        for item in outbound_queue.pop_all():
            try:
                if item.kind == "login_success":
                    account_data = item.payload.get("account") or {}
                    account = SimpleNamespace(**account_data)
                    await send_auth_welcome(
                        self._app.bot,
                        item.telegram_id,
                        account,
                        title=item.payload.get("title", "Login successful"),
                        photo_url=item.payload.get("photo_url"),
                        telegram_id=item.telegram_id,
                    )
                else:
                    text = item.payload.get("text")
                    if text:
                        await self._app.bot.send_message(
                            chat_id=item.telegram_id,
                            text=text,
                            parse_mode=item.payload.get("parse_mode"),
                        )
            except Exception as e:
                logger.warning(
                    "Failed to deliver queued Telegram %s to %s: %s",
                    item.kind,
                    item.telegram_id,
                    e,
                )

    async def _maybe_notify_backlog(self, update: "Update") -> None:
        if not self._online_at:
            return
        user = update.effective_user
        if not user or user.id in self._backlog_notified:
            return
        message = update.effective_message
        if not message or not message.date:
            return
        sent_at = message.date.timestamp()
        if sent_at >= self._online_at - 2:
            return
        try:
            await message.reply_text(
                "Bot is back online — processing your queued message…",
            )
        except Exception as e:
            logger.debug("Backlog notice skipped for %s: %s", user.id, e)
        self._backlog_notified.add(user.id)

    async def notify_login_success(
        self,
        telegram_id: int,
        account,
        *,
        photo_url: Optional[str] = None,
    ) -> None:
        if not self._ready_for_sends():
            from dataclasses import asdict, is_dataclass

            account_payload = asdict(account) if is_dataclass(account) else dict(vars(account))
            outbound_queue.enqueue(
                QueuedOutbound(
                    kind="login_success",
                    telegram_id=telegram_id,
                    payload={
                        "title": "Login successful",
                        "photo_url": photo_url,
                        "account": account_payload,
                    },
                )
            )
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
        app.add_handler(
            TypeHandler(Update, self._maybe_notify_backlog),
            group=-1,
        )
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
            _login_menu_text(uid),
            parse_mode="Markdown",
            reply_markup=_login_keyboard(uid),
        )

    async def _show_register_menu(self, update: "Update", uid: int):
        profile = profile_store.get(uid)
        profile.step = STEP_AUTH_MENU
        profile.mode = "register"
        profile_store.save(profile)
        await update.message.reply_text(
            _register_menu_text(uid),
            parse_mode="Markdown",
            reply_markup=_register_keyboard(uid),
        )

    async def _on_unknown_command(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        text = (update.message.text or "").strip()
        parsed = parse_inline_command(text)
        if parsed:
            cmd, args = parsed
            from .handlers.registry import dispatch_product_command

            if await dispatch_product_command(self, update, ctx, cmd, args):
                return
        raw = text.split()[0].lower().lstrip("/").split("@", 1)[0]
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
        from .web_auth import resolve_runtime_user_id

        await memory_service.remember(
            acct.context_line(),
            user_id=resolve_runtime_user_id(uid, acct),
            metadata={"source": "telegram_login", "email": acct.email},
        )
        await send_auth_welcome(
            ctx.bot,
            uid,
            acct,
            title="Login successful",
            telegram_id=uid,
        )
        await self._fire_login_hooks(uid, acct)

    async def _fire_login_hooks(self, uid: int, account) -> None:
        try:
            from ...automation.scheduler_logic import trigger_event_hooks
            from .web_auth import resolve_runtime_user_id

            owner = resolve_runtime_user_id(uid, account)
            await trigger_event_hooks("on_login", owner, telegram_chat_id=uid)
        except Exception as e:
            logger.debug("on_login hooks skipped: %s", e)

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
                _register_menu_text(uid),
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
                _login_menu_text(uid),
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
            f"Role: *{role.capitalize()}*\n\n"
            "Send your *phone number* (e.g. +8801XXXXXXXXX), or reply *skip* or /skip.",
            parse_mode="Markdown",
        )

    async def _finish_registration(
        self,
        update: "Update",
        ctx: "ContextTypes.DEFAULT_TYPE",
        profile: TelegramProfile,
        uid: int,
    ):
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
        from .web_auth import resolve_runtime_user_id

        await memory_service.remember(
            account.context_line(),
            user_id=resolve_runtime_user_id(uid, account),
            metadata={"source": "telegram_register", "email": account.email},
        )
        await send_auth_welcome(
            ctx.bot,
            uid,
            account,
            title="Registration complete",
            telegram_id=uid,
        )
        await self._fire_login_hooks(uid, account)

    async def _apply_registration_optional_field(
        self,
        update: "Update",
        ctx: "ContextTypes.DEFAULT_TYPE",
        profile: TelegramProfile,
        uid: int,
        text: str,
    ):
        if profile.step == STEP_REGISTER_PHONE:
            profile.phone = "" if is_skip_input(text) else text
            if profile.role == "student":
                profile.step = STEP_REGISTER_STUDENT_ID
                profile_store.save(profile)
                await update.message.reply_text(
                    "Send your *Student ID* (e.g. 221-15-1234), or reply *skip* or /skip:",
                    parse_mode="Markdown",
                )
            else:
                profile.step = STEP_REGISTER_DEPARTMENT
                profile_store.save(profile)
                await update.message.reply_text(
                    "Send your *department* (e.g. CSE), or reply *skip* or /skip:",
                    parse_mode="Markdown",
                )
            return

        if profile.step == STEP_REGISTER_STUDENT_ID:
            profile.student_id = "" if is_skip_input(text) else text
            profile.step = STEP_REGISTER_DEPARTMENT
            profile_store.save(profile)
            await update.message.reply_text(
                "Send your *department* (e.g. CSE), or reply *skip* or /skip:",
                parse_mode="Markdown",
            )
            return

        if profile.step == STEP_REGISTER_DEPARTMENT:
            profile.department = "" if is_skip_input(text) else text
            profile_store.save(profile)
            await self._finish_registration(update, ctx, profile, uid)

    async def _apply_registration_skip(
        self,
        update: "Update",
        ctx: "ContextTypes.DEFAULT_TYPE",
        profile: TelegramProfile,
        uid: int,
    ):
        await self._apply_registration_optional_field(update, ctx, profile, uid, "skip")

    async def _on_text(self, update: "Update", ctx: "ContextTypes.DEFAULT_TYPE"):
        uid = update.effective_user.id
        if not self._allowed(uid):
            await update.message.reply_text("Not authorized.")
            return

        text = (update.message.text or "").strip()
        profile = profile_store.get(uid)
        self._sync(update, profile)

        if text.startswith("/") and self._is_authenticated(uid):
            parsed = parse_inline_command(text)
            if parsed:
                from .handlers.registry import dispatch_product_command

                cmd, args = parsed
                if await dispatch_product_command(self, update, ctx, cmd, args):
                    return

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
        if quick == "agents" and self._is_authenticated(uid):
            from .handlers.agents import AgentHandlers

            await AgentHandlers(self).cmd_agents(update, ctx)
            return
        if quick == "skills" and self._is_authenticated(uid):
            from .handlers.skills import SkillHandlers

            await SkillHandlers(self).cmd_skills(update, ctx)
            return
        if quick == "automate" and self._is_authenticated(uid):
            from .handlers.automation import AutomationHandlers

            await AutomationHandlers(self).cmd_automate(update, ctx)
            return
        if quick == "tools" and self._is_authenticated(uid):
            from .handlers.runtime import RuntimeHandlers

            await RuntimeHandlers(self).cmd_tools(update, ctx)
            return
        if quick == "flow" and self._is_authenticated(uid):
            from .handlers.runtime import RuntimeHandlers

            await RuntimeHandlers(self).cmd_flow(update, ctx)
            return
        if quick == "logs" and self._is_authenticated(uid):
            from .handlers.runtime import RuntimeHandlers

            await RuntimeHandlers(self).cmd_logs(update, ctx)
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

        if profile.step in (STEP_REGISTER_PHONE, STEP_REGISTER_STUDENT_ID, STEP_REGISTER_DEPARTMENT):
            await self._apply_registration_optional_field(update, ctx, profile, uid, text)
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
        chat_id = f"tg-{uid}"

        runtime_user_id, metadata, model_id, turn_index = build_telegram_turn(
            telegram_id=uid,
            account=account,
            agent_id=agent_id,
            chat_id=chat_id,
        )

        try:
            from ...automation.scheduler_logic import trigger_event_hooks

            await trigger_event_hooks(
                "on_keyword", runtime_user_id, telegram_chat_id=uid, keyword_text=text
            )
        except Exception as hook_err:
            logger.debug("on_keyword hooks skipped: %s", hook_err)

        content_parts: List[str] = []
        tool_calls: List[str] = []
        resolved_agent = agent_id
        flow_msg = None
        had_stream = False
        try:
            async for event in run_turn_stream(
                text,
                user_id=runtime_user_id,
                chat_id=chat_id,
                agent_id=agent_id,
                context_prefix=prefix,
                attachments=attachments,
                model_id=model_id,
                metadata=metadata,
            ):
                if not isinstance(event, dict):
                    continue
                etype = event.get("type")
                if etype == "content":
                    had_stream = True
                    content_parts.append(event.get("content") or "")
                elif etype == "agent":
                    resolved_agent = event.get("agent_id") or resolved_agent
                elif etype == "tool":
                    name = event.get("name")
                    if event.get("status") == "active" and name and name not in tool_calls:
                        tool_calls.append(name)
                        flow_msg = await self._update_flow_message(
                            update, flow_msg, resolved_agent, tool_calls
                        )
                elif etype == "subagent":
                    flow_msg = await self._update_flow_message(
                        update, flow_msg, resolved_agent, tool_calls, subagent=True
                    )
        except Exception as stream_err:
            logger.warning("Telegram stream failed, falling back: %s", stream_err)

        content = "".join(content_parts).strip()
        if not had_stream or not content:
            result = await run_turn(
                text,
                user_id=runtime_user_id,
                chat_id=chat_id,
                agent_id=agent_id,
                context_prefix=prefix,
                attachments=attachments,
                model_id=model_id,
                metadata=metadata,
            )
            content = (result.get("content") or "").strip()
            tool_calls = result.get("tool_calls") or tool_calls
            resolved_agent = result.get("agent_id") or resolved_agent

        if not content and model_id is not None:
            result = await run_turn(
                text,
                user_id=runtime_user_id,
                chat_id=chat_id,
                agent_id=agent_id,
                context_prefix=prefix,
                attachments=attachments,
                model_id=None,
                metadata=metadata,
            )
            content = (result.get("content") or "").strip()
            tool_calls = result.get("tool_calls") or tool_calls
            resolved_agent = result.get("agent_id") or resolved_agent

        if not content:
            try:
                from ...runtime.orchestrator import _legacy_run

                legacy = await _legacy_run(text, runtime_user_id)
                content = (legacy.get("content") or "").strip()
            except Exception as legacy_err:
                logger.debug("Telegram legacy fallback failed: %s", legacy_err)

        if flow_msg is not None:
            try:
                await flow_msg.edit_text(
                    self._render_flow_text(resolved_agent, tool_calls, done=True),
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        elif tool_calls:
            try:
                await update.message.reply_text(
                    f"_Used tools: {', '.join(tool_calls)}_",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

        if not content:
            content = chat_turn_fallback_message(text)
        for chunk in _chunk(content, 4000):
            await update.message.reply_text(chunk)
        try:
            await memory_service.process_turn_memory(
                user_id=runtime_user_id,
                agent_id=resolved_agent,
                chat_id=chat_id,
                user_msg=text,
                assistant_msg=content,
                turn_index=turn_index,
            )
        except Exception as mem_err:
            logger.warning("Telegram turn memory failed: %s", mem_err)

    @staticmethod
    def _render_flow_text(agent_id: str, tool_calls: List[str], *, done: bool = False, subagent: bool = False) -> str:
        head = "✅ *Flow*" if done else "⚙️ *Working…*"
        lines = [head, f"🤖 agent: `{agent_id}`"]
        if tool_calls:
            lines.append("🔧 tools: " + ", ".join(f"`{t}`" for t in tool_calls))
        if subagent:
            lines.append("🧩 sub-agent delegating…")
        return "\n".join(lines)

    async def _update_flow_message(
        self,
        update: "Update",
        flow_msg,
        agent_id: str,
        tool_calls: List[str],
        *,
        subagent: bool = False,
    ):
        text = self._render_flow_text(agent_id, tool_calls, subagent=subagent)
        try:
            if flow_msg is None:
                return await update.message.reply_text(text, parse_mode="Markdown")
            await flow_msg.edit_text(text, parse_mode="Markdown")
            return flow_msg
        except Exception:
            return flow_msg

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
