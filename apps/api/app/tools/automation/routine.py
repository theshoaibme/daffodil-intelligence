"""Class routine and automation subscription tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.routines_data import get_section_routine
from ...automation.store import automation_store
from ...automation.telegram_notify import resolve_telegram_chat_id_for_user
from ...runtime.tool_context import get_section, get_user_id


class GetClassRoutineTool(BaseTool):
    name = "get_class_routine"
    description = (
        "Get class routine for a CSE section (time, room, course, teacher). "
        "Optionally filter by weekday name (Monday, Tuesday, ...)."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="section",
            type="string",
            description="Section id e.g. 64_I",
            required=False,
            default="64_I",
        ),
        ToolParameter(
            name="day",
            type="string",
            description="Weekday name e.g. Monday (optional; omit for full week)",
            required=False,
        ),
    ]

    async def execute(self, section: str = "64_I", day: str = None, **kwargs) -> ToolResult:
        sec = section or get_section()
        data = get_section_routine(sec, day.strip() if day else None)
        return self.ok(data)


class EnableRoutineAutomationTool(BaseTool):
    name = "enable_routine_automation"
    description = (
        "Enable automated Telegram notifications: (1) daily tomorrow routine at 9 PM, "
        "(2) class reminders 1 hour before each class. Requires linked Telegram account."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="section",
            type="string",
            description="Section e.g. 64_I",
            required=False,
            default="64_I",
        ),
        ToolParameter(
            name="daily_tomorrow",
            type="boolean",
            description="Send tomorrow's routine each evening",
            required=False,
            default=True,
        ),
        ToolParameter(
            name="hour_before_class",
            type="boolean",
            description="Send alert 1 hour before each class",
            required=False,
            default=True,
        ),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(
        self,
        section: str = "64_I",
        daily_tomorrow: bool = True,
        hour_before_class: bool = True,
        user_id: str = None,
        **kwargs,
    ) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        if not uid:
            return self.fail("user_id required")
        chat_id = await resolve_telegram_chat_id_for_user(uid)
        if not chat_id:
            return self.fail(
                "Link Telegram first: open the DI Telegram bot and log in with the same email."
            )
        sec = section or get_section()
        created = []
        if daily_tomorrow:
            sub = automation_store.upsert_subscription(
                user_id=uid,
                kind="routine_daily",
                section=sec,
                telegram_chat_id=chat_id,
            )
            created.append(sub.to_dict())
        if hour_before_class:
            sub = automation_store.upsert_subscription(
                user_id=uid,
                kind="class_hourly",
                section=sec,
                telegram_chat_id=chat_id,
            )
            created.append(sub.to_dict())
        return self.ok(
            {
                "status": "enabled",
                "section": sec,
                "telegram_chat_id": chat_id,
                "subscriptions": created,
                "note": "Requires Celery beat worker for scheduled delivery.",
            }
        )
