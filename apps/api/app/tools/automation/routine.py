"""Class routine and automation subscription tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.routine_fetch import fetch_class_routine, routine_has_schedule
from ...automation.routine_memory import recall_user_section
from ...automation.routine_pdf_reader import read_routine_pdf_fast
from ...automation.routine_resolver import resolve_section
from ...automation.store import automation_store
from ...automation.telegram_notify import resolve_telegram_chat_id_for_user
from ...runtime.tool_context import get_department, get_section, get_user_id


class GetClassRoutineTool(BaseTool):
    name = "get_class_routine"
    description = (
        "Get class routine for a section from data/routines/*.csv, section uploads, "
        "or department PDFs under data/routines/{department}/. MCP mode uses the same "
        "registry tools (no invented schedules). Day: weekday or today/tomorrow/yesterday."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="section",
            type="string",
            description="Section id (optional — from memory or profile)",
            required=False,
        ),
        ToolParameter(
            name="day",
            type="string",
            description="Weekday (Monday) or relative: today, tomorrow, yesterday (optional; omit for full week)",
            required=False,
        ),
        ToolParameter(
            name="department",
            type="string",
            description="Department e.g. CSE (optional — from user profile)",
            required=False,
        ),
    ]

    async def execute(
        self,
        section: str = None,
        day: str = None,
        department: str = None,
        **kwargs,
    ) -> ToolResult:
        uid = get_user_id()
        dept = (department or get_department() or "").strip() or None
        explicit = (section or get_section(default="") or "").strip()
        sec = resolve_section(section=explicit, department=dept) if explicit else ""
        if not sec and uid:
            sec = await recall_user_section(uid)
        if not sec:
            return self.fail(
                "Section unknown. Ask the user for their section, or save it with "
                "store_note (tag=section) / assign a routine skill."
            )

        data = await fetch_class_routine(
            user_id=uid,
            section=sec,
            day=day,
            department=dept,
        )
        if data.get("error") == "section_required":
            return self.fail(data.get("hint") or "Section required")
        if routine_has_schedule(data):
            return self.ok(data)
        if data.get("source") == "csv" and data.get("day"):
            return self.ok(data)

        hint = data.get("hint") or (
            f"No routine in data/routines for section `{sec}`. "
            "Upload CSV/PDF to data/routines/ or save section with store_note."
        )
        return self.fail(hint)


class ReadDepartmentRoutinePdfTool(BaseTool):
    name = "read_department_routine_pdf"
    description = (
        "Legacy alias for department routine PDFs. Prefer read_routine_pdf or read_pdf."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="department", type="string", description="Department", required=False),
        ToolParameter(name="section", type="string", description="Section code", required=False),
    ]

    async def execute(
        self,
        department: str = None,
        section: str = None,
        **kwargs,
    ) -> ToolResult:
        dept = (department or get_department() or "").strip()
        if not dept:
            return self.fail("Department required — set on profile or pass department")
        sec = resolve_section(section=section or get_section(default=""), department=dept)
        if not sec:
            uid = get_user_id()
            if uid:
                sec = await recall_user_section(uid)
        if not sec:
            return self.fail("Section required for department routine PDF lookup")
        result = read_routine_pdf_fast(dept, sec, max_chars=6000)
        if not result.get("text"):
            return self.fail(f"No routine PDF/text uploaded for {dept} section {sec}")
        return self.ok({**result, "department": dept, "section": sec})


class EnableRoutineAutomationTool(BaseTool):
    name = "enable_routine_automation"
    description = (
        "Enable automated Telegram notifications: (1) daily tomorrow routine at 9 PM, "
        "(2) class reminders 1 hour before each class. Requires linked Telegram account."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="section", type="string", description="Section code", required=False),
        ToolParameter(name="department", type="string", description="Department", required=False),
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
        section: str = None,
        department: str = None,
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
        dept = (department or get_department() or "").strip() or None
        sec = resolve_section(section=section or get_section(default=""), department=dept)
        if not sec:
            sec = await recall_user_section(uid)
        if not sec:
            return self.fail("Section required before enabling routine automation")
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
                "department": dept,
                "telegram_chat_id": chat_id,
                "subscriptions": created,
                "note": "Requires Celery beat worker for scheduled delivery.",
            }
        )
