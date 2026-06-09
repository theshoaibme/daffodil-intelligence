"""Logic for due reminders and class routine Telegram notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from .routines_data import get_section_routine
from .store import AutomationSubscription, ReminderRecord, automation_store
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


async def run_automation_tick() -> dict:
    now = datetime.now()
    reminders = await process_due_reminders()
    routines = await process_routine_subscriptions(now)
    return {"reminders_sent": reminders, "routine_messages_sent": routines}
