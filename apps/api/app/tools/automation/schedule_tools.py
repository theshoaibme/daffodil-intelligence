"""Combined schedule view and task scheduling."""

from __future__ import annotations

from datetime import datetime, timezone

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.routine_memory import recall_class_routine, recall_user_section
from ...automation.routines_data import get_uploaded_routine
from ...automation.routine_resolver import resolve_section
from ...automation.store import automation_store
from ...runtime.tool_context import get_department, get_section, get_user_id


class GetDailyScheduleTool(BaseTool):
    name = "get_daily_schedule"
    description = (
        "Get today's overview: class blocks for a section, active reminders, "
        "and personal routines."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="section", type="string", description="Section code", required=False),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, section: str = None, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        dept = (get_department() or "").strip() or None
        sec = resolve_section(section=section or get_section(default=""), department=dept)
        if not sec and uid:
            sec = await recall_user_section(uid)

        today = datetime.now(timezone.utc).strftime("%A")
        classes = await recall_class_routine(uid, section=sec, department=dept, day=today) if uid else None
        if not classes:
            classes = get_uploaded_routine(sec, today, department=dept) if sec else {"items": []}
        reminders = automation_store.list_reminders(uid) if uid else []
        routines = automation_store.list_personal_routines(uid) if uid else []

        items = classes.get("items") or []

        return self.ok(
            {
                "section": sec,
                "day": today,
                "classes": items,
                "reminders": [r.to_dict() for r in reminders],
                "routines": [r.to_dict() for r in routines],
            }
        )


class ScheduleTaskTool(BaseTool):
    name = "schedule_task"
    description = "Schedule a one-off task (creates a reminder). Alias for create_reminder."
    category = "automation"
    parameters = [
        ToolParameter(name="title", type="string", description="Task title"),
        ToolParameter(name="fire_at", type="string", description="ISO datetime UTC"),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, title: str, fire_at: str, user_id: str = None, **kwargs) -> ToolResult:
        from .reminders import CreateReminderTool

        tool = CreateReminderTool()
        return await tool.execute(title=title, fire_at=fire_at, user_id=user_id, **kwargs)
