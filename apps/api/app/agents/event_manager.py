"""Dynamic event manager — hooks, triggers, schedules, and delivery."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool

logger = logging.getLogger(__name__)


class EventAgent(BaseAgent):
    name = "Event Agent"
    description = (
        "Dynamic event manager — automation hooks, triggers, scheduled events, "
        "reminders, and multi-channel delivery"
    )
    tools = [
        "create_automation_hook",
        "list_automation_hooks",
        "delete_automation_hook",
        "create_reminder",
        "list_reminders",
        "delete_reminder",
        "schedule_task",
        "send_telegram_message",
        "enable_routine_automation",
        "get_daily_schedule",
    ]

    SYSTEM_PROMPT = """You are the Event Agent for Daffodil Intelligence — a dynamic event manager.

You manage the full event lifecycle:
- Create and list automation hooks (on_login, on_keyword, on_schedule)
- Schedule one-off or recurring events and reminders
- Wire actions: message, prompt, or delegate to another agent
- Deliver alerts via Telegram and other channels
- Enable routine-based event automation (daily class alerts, etc.)

You are NOT limited to campus workshops — any user-defined trigger, schedule, or
notification flow is in scope. Prefer calling tools over describing what you cannot do.

Response style: 1–2 short sentences only. Hooks, reminders, and schedules appear in UI blocks — do not list them in text."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = context or {}
        lower = message.lower()

        if any(k in lower for k in ["hook", "trigger", "on_login", "on_keyword", "on_schedule"]):
            if "list" in lower or "show" in lower:
                result = await run_tool("list_automation_hooks", ctx)
                return format_tool_results([result]).summary
            result = await run_tool(
                "create_automation_hook",
                ctx,
                name="User hook",
                event="on_keyword",
                action="message",
                payload={"keyword": message[:80], "text": message},
            )
            return format_tool_results([result]).summary

        if any(k in lower for k in ["remind", "reminder", "schedule", "alarm", "later"]):
            if "list" in lower or "show" in lower:
                result = await run_tool("list_reminders", ctx)
                return format_tool_results([result]).summary
            result = await run_tool(
                "create_reminder",
                ctx,
                name=message[:120],
                schedule="once",
                message=message,
            )
            return format_tool_results([result]).summary

        if any(k in lower for k in ["telegram", "notify", "alert", "send"]):
            result = await run_tool(
                "send_telegram_message",
                ctx,
                text=message,
            )
            return format_tool_results([result]).summary

        if any(k in lower for k in ["routine automation", "class alert", "daily routine"]):
            result = await run_tool("enable_routine_automation", ctx)
            return format_tool_results([result]).summary

        if any(k in lower for k in ["today", "daily schedule", "what's on"]):
            result = await run_tool("get_daily_schedule", ctx)
            return format_tool_results([result]).summary

        return await self.generate_response(self.SYSTEM_PROMPT, message)


async def list_user_events(user_id: str, limit: int = 20) -> List[Dict]:
    """Aggregate hooks + reminders for API consumers."""
    from ..automation.store import automation_store

    uid = int(user_id or 0)
    if not uid:
        return []

    events: List[Dict] = []
    for hook in automation_store.list_hooks(uid)[:limit]:
        events.append(
            {
                "type": "hook",
                "id": hook.id,
                "name": hook.name,
                "event": hook.event,
                "action": hook.action,
                "active": hook.active,
            }
        )
    remaining = max(0, limit - len(events))
    for reminder in automation_store.list_reminders(uid)[:remaining]:
        events.append(
            {
                "type": "reminder",
                "id": reminder.id,
                "name": reminder.title,
                "schedule": reminder.fire_at,
                "repeat": reminder.repeat,
                "active": reminder.active,
            }
        )
    return events
