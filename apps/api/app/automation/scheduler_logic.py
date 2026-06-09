"""Logic for due reminders and class routine Telegram notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from .routines_data import get_section_routine
from .store import automation_store
from .telegram_notify import resolve_telegram_chat_id_for_user, send_telegram_message

logger = logging.getLogger(__name__)


def _parse_time_hm(value: str) -> Optional[tuple[int, int]]:
    try:
        parts = value.strip().split(":")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None


def format_routine_message(section: str, day_name: str) -> str:
    data = get_section_routine(section, day_name)
    items = data.get("items") or []
    if not items:
        return f"📅 *No classes scheduled* for {day_name} (section {section})."
    lines = [f"📅 *{day_name} routine* — Section {section} CSE\n"]
    for item in items:
        lines.append(
            f"⏰ {item['time']} — *{item['course']}* {item.get('title', '')}\n"
            f"   Room: {item.get('room', 'TBA')} | Teacher: {item.get('teacher', 'TBA')}"
        )
    return "\n".join(lines)


def classes_starting_in_one_hour(section: str, now: Optional[datetime] = None) -> List[dict]:
    now = now or datetime.now()
    target = now + timedelta(hours=1)
    day_name = now.strftime("%A")
    data = get_section_routine(section, day_name)
    items = data.get("items") or []
    matches = []
    for item in items:
        parsed = _parse_time_hm(item.get("time", ""))
        if not parsed:
            continue
        hour, minute = parsed
        if now.hour == hour - 1 and now.minute == minute:
            matches.append(item)
        elif target.hour == hour and target.minute == minute:
            matches.append(item)
    return matches


async def process_due_reminders(now: Optional[datetime] = None) -> int:
    now = now or datetime.utcnow()
    sent = 0
    for rec in automation_store.due_reminders(now):
        chat_id = await resolve_telegram_chat_id_for_user(rec.user_id)
        if not chat_id:
            continue
        body = rec.payload.get("body") or f"⏰ *Reminder:* {rec.title}"
        if await send_telegram_message(chat_id, body):
            automation_store.mark_reminder_sent(rec.id)
            sent += 1
    return sent


async def process_routine_subscriptions(now: Optional[datetime] = None) -> int:
    now = now or datetime.now()
    sent = 0
    for sub in automation_store.list_subscriptions():
        chat_id = sub.telegram_chat_id or await resolve_telegram_chat_id_for_user(sub.user_id)
        if not chat_id:
            continue

        if sub.kind == "routine_daily" and now.hour == 21:
            tomorrow = (now + timedelta(days=1)).strftime("%A")
            msg = format_routine_message(sub.section, tomorrow)
            msg = f"🌙 *Tomorrow's plan*\n\n{msg}"
            if await send_telegram_message(chat_id, msg):
                sent += 1

        if sub.kind == "class_hourly":
            upcoming = classes_starting_in_one_hour(sub.section, now)
            for item in upcoming:
                msg = (
                    f"🔔 *Class in 1 hour*\n\n"
                    f"*{item['course']}* — {item.get('title', '')}\n"
                    f"⏰ {item['time']}\n"
                    f"📍 Room: {item.get('room', 'TBA')}\n"
                    f"👨‍🏫 {item.get('teacher', 'TBA')}"
                )
                if await send_telegram_message(chat_id, msg):
                    sent += 1
    return sent


async def _execute_action(
    *,
    user_id: int,
    action: str,
    payload: dict,
    chat_id: str,
    telegram_chat_id: Optional[int] = None,
) -> Optional[str]:
    """Resolve a hook/loop action into a message to deliver."""
    text = (payload.get("text") or "").strip()
    if action == "message":
        return text or None
    if action in ("prompt", "agent"):
        from ..runtime.pipeline import run_turn

        result = await run_turn(
            text,
            user_id=user_id,
            chat_id=chat_id,
            agent_id=payload.get("agent_id") or None,
            metadata={"telegram_chat_id": telegram_chat_id} if telegram_chat_id else None,
        )
        return (result.get("content") or "").strip() or None
    return None


async def process_due_loops(now: Optional[datetime] = None) -> int:
    now = now or datetime.utcnow()
    sent = 0
    for loop in automation_store.due_loops(now):
        chat_id = await resolve_telegram_chat_id_for_user(loop.user_id)
        if not chat_id:
            continue
        try:
            content = await _execute_action(
                user_id=loop.user_id,
                action="prompt",
                payload={"text": loop.prompt, "agent_id": loop.agent_id},
                chat_id=f"loop-{loop.id}",
                telegram_chat_id=chat_id,
            )
        except Exception as e:
            logger.warning("Loop %s failed: %s", loop.id, e)
            content = None
        automation_store.mark_loop_run(loop.id, now)
        if content and await send_telegram_message(chat_id, f"🔁 *{loop.name}*\n\n{content}"):
            sent += 1
    return sent


async def process_scheduled_hooks(now: Optional[datetime] = None) -> int:
    now = now or datetime.now()
    sent = 0
    for hook in automation_store.hooks_for_event("on_schedule"):
        hour = hook.payload.get("hour")
        if hour is None or int(hour) != now.hour or now.minute != 0:
            continue
        chat_id = await resolve_telegram_chat_id_for_user(hook.user_id)
        if not chat_id:
            continue
        try:
            content = await _execute_action(
                user_id=hook.user_id,
                action=hook.action,
                payload=hook.payload,
                chat_id=f"hook-{hook.id}",
                telegram_chat_id=chat_id,
            )
        except Exception as e:
            logger.warning("Scheduled hook %s failed: %s", hook.id, e)
            content = None
        automation_store.mark_hook_fired(hook.id)
        if content and await send_telegram_message(chat_id, content):
            sent += 1
    return sent


async def trigger_event_hooks(
    event: str,
    user_id: int,
    *,
    telegram_chat_id: Optional[int] = None,
    keyword_text: Optional[str] = None,
) -> int:
    """Fire `on_login` / `on_keyword` hooks for a user (called from the bot)."""
    fired = 0
    for hook in automation_store.hooks_for_event(event, user_id=user_id):
        if event == "on_keyword":
            kw = (hook.payload.get("keyword") or "").strip().lower()
            if not kw or kw not in (keyword_text or "").lower():
                continue
        chat_id = telegram_chat_id or await resolve_telegram_chat_id_for_user(user_id)
        if not chat_id:
            continue
        try:
            content = await _execute_action(
                user_id=user_id,
                action=hook.action,
                payload=hook.payload,
                chat_id=f"hook-{hook.id}",
                telegram_chat_id=chat_id,
            )
        except Exception as e:
            logger.warning("Event hook %s failed: %s", hook.id, e)
            content = None
        automation_store.mark_hook_fired(hook.id)
        if content and await send_telegram_message(chat_id, content):
            fired += 1
    return fired


async def run_automation_tick() -> dict:
    now = datetime.now()
    reminders = await process_due_reminders()
    routines = await process_routine_subscriptions(now)
    loops = await process_due_loops(datetime.utcnow())
    scheduled_hooks = await process_scheduled_hooks(now)
    return {
        "reminders_sent": reminders,
        "routine_messages_sent": routines,
        "loop_messages_sent": loops,
        "scheduled_hooks_fired": scheduled_hooks,
    }
