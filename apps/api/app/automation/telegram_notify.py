"""Send proactive Telegram messages for automation."""

from __future__ import annotations

import logging
from typing import Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str, *, parse_mode: str = "Markdown") -> bool:
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return False
    try:
        from telegram import Bot

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


async def resolve_telegram_chat_id_for_user(user_id: int) -> Optional[int]:
    """Resolve Telegram chat id from web user id or direct Telegram id."""
    from ..integrations.telegram.auth_store import auth_store
    from ..runtime.tool_context import get_telegram_chat_id

    ctx_chat = get_telegram_chat_id()
    if ctx_chat:
        return ctx_chat

    acct = auth_store.get_by_telegram_id(user_id)
    if acct:
        return int(acct.telegram_id)

    try:
        from sqlalchemy import select
        from ..core.database import get_session_maker
        from ..models.user import User

        maker = get_session_maker()
        if not maker:
            return None
        async with maker() as session:
            row = await session.execute(select(User).where(User.id == user_id))
            user = row.scalar_one_or_none()
            if not user or not user.email:
                return None
            linked = auth_store.get_by_email(user.email)
            if linked:
                return int(linked.telegram_id)
    except Exception as e:
        logger.debug("resolve_telegram_chat_id_for_user: %s", e)
    return None
