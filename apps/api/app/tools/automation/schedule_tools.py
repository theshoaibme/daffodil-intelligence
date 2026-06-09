"""Combined schedule view and task scheduling."""

from __future__ import annotations

from datetime import datetime, timezone

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.routines_data import get_section_routine
from ...automation.store import automation_store
from ...runtime.tool_context import get_section, get_user_id


class GetDailyScheduleTool(BaseTool):
    name = "get_daily_schedule"
    description = (
        "Get today's overview: class blocks for a section, active reminders, "
        "and personal routines."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="section", type="string", description="Section e.g. 64_I", required=False, default="64_I"),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, section: str = "64_I", user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        sec = (section or get_section() or "64_I").upper()
        if sec == "CSE":
            sec = "64_I"

        today = datetime.now(timezone.utc).strftime("%A")
        classes = get_section_routine(sec, today)
        reminders = automation_store.list_reminders(uid) if uid else []
        routines = automation_store.list_personal_routines(uid) if uid else []

        summary_lines = [f"📅 **Today ({today}) — section {sec}**"]
        items = classes.get("items") or []
        if items:
            summary_lines.append("\n**Classes**")
            for it in items:
                summary_lines.append(
                    f"• {it['time']} — {it.get('course', '')} {it.get('title', '')}"
                )
        else:
            summary_lines.append("\n_No classes scheduled today._")

        if reminders:
            summary_lines.append("\n**Reminders**")
            for r in reminders[:8]:
                summary_lines.append(f"• {r.title} @ {r.fire_at}")

        if routines:
            summary_lines.append("\n**Personal routines**")
            for r in routines[:5]:
                summary_lines.append(f"• {r.name} ({r.schedule})")

        return self.ok(
            {
                "section": sec,
                "day": today,
                "classes": items,
                "reminders": [r.to_dict() for r in reminders],
                "routines": [r.to_dict() for r in routines],
                "summary": "\n".join(summary_lines),
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
