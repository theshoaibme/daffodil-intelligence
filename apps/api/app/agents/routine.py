from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool
from ..automation.routine_intent import is_improvement_exam_routine, wants_class_routine
from ..automation.routine_memory import recall_user_section
from ..automation.routine_resolver import normalize_section, resolve_section
from ..runtime.intent_router import route_message

logger = logging.getLogger(__name__)

ROUTINE_TOOLS = [
    "get_class_routine",
    "read_pdf",
    "read_routine_pdf",
    "read_department_routine_pdf",
    "recall_notes",
    "store_note",
    "enable_routine_automation",
    "create_reminder",
    "list_reminders",
    "delete_reminder",
    "create_routine",
    "list_routines",
    "delete_routine",
    "get_daily_schedule",
    "schedule_task",
    "create_automation_hook",
    "list_automation_hooks",
    "delete_automation_hook",
]

_CLASS_TODAY_KEYS = (
    "today's class",
    "today class",
    "class today",
    "classes today",
    "today class routine",
    "today's class routine",
)
_CLASS_TOMORROW_KEYS = (
    "tomorrow's class",
    "tomorrow class",
    "class tomorrow",
    "classes tomorrow",
    "tomorrow class routine",
    "tomorrow's class routine",
    "tomorrow routine",
    "tomorrow's routine",
)
_CLASS_ROUTINE_KEYS = ("class routine", "class schedule", "weekly routine")
_DAILY_KEYS = (
    "today routine",
    "daily routine",
    "daily schedule",
    "plan my day",
    "my day",
    "what's on",
    "whats on",
    "day plan",
)

_SECTION_PROMPT = (
    "Which section's class routine do you need? "
    "I can also look it up from your saved memory or routine skills."
)

_TOOL_CALL_RE = re.compile(
    r"get_class_routine\s*\(\s*section\s*=\s*[\"']?([^\"',)]+)[\"']?"
    r"(?:\s*,\s*day\s*=\s*[\"']?([^\"',)]+)[\"']?)?\s*\)",
    re.I,
)


def _parse_get_class_routine_call(message: str) -> Optional[Tuple[str, Optional[str]]]:
    match = _TOOL_CALL_RE.search(message or "")
    if not match:
        return None
    section = (match.group(1) or "").strip()
    day = (match.group(2) or "").strip() or None
    return section, day


def _weekday(offset_days: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).strftime("%A")


class RoutineAgent(BaseAgent):
    name = "Routine Agent"
    description = "Schedules, class routines, reminders, habits, and automation hooks"
    tools = ROUTINE_TOOLS

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = context or {}
        plan = route_message(message)
        lower = (message or "").lower()
        results: List = []

        try:
            tool_call = _parse_get_class_routine_call(message)
            if tool_call:
                call_sec, call_day = tool_call
                sec = normalize_section(call_sec) or await self._resolve_section(ctx, plan.section)
                if not sec:
                    return _SECTION_PROMPT
                kwargs: Dict = {"section": sec}
                if call_day:
                    kwargs["day"] = call_day
                results.append(await run_tool("get_class_routine", ctx, **kwargs))
                return format_tool_results(results).summary

            if is_improvement_exam_routine(lower):
                day_hint = None
                if "tomorrow" in lower:
                    day_hint = _weekday(1)
                elif "today" in lower:
                    day_hint = _weekday(0)
                kwargs: Dict = {"routine_kind": "improvement_exam", "message": message}
                if day_hint:
                    kwargs["day"] = day_hint
                results.append(await run_tool("get_class_routine", ctx, **kwargs))
                return format_tool_results(results).summary

            sec = await self._resolve_section(ctx, plan.section)

            if any(k in lower for k in _CLASS_TOMORROW_KEYS):
                if not sec:
                    return _SECTION_PROMPT
                results.append(
                    await run_tool("get_class_routine", ctx, section=sec, day=_weekday(1))
                )

            elif any(k in lower for k in _CLASS_TODAY_KEYS):
                if not sec:
                    return _SECTION_PROMPT
                results.append(
                    await run_tool("get_class_routine", ctx, section=sec, day=_weekday(0))
                )

            elif plan.section or any(k in lower for k in _CLASS_ROUTINE_KEYS):
                if not sec:
                    return _SECTION_PROMPT
                day_hint = None
                if "tomorrow" in lower:
                    day_hint = _weekday(1)
                elif "today" in lower:
                    day_hint = _weekday(0)
                results.append(
                    await run_tool(
                        "get_class_routine",
                        ctx,
                        section=sec,
                        **({"day": day_hint} if day_hint else {}),
                    )
                )

            elif not wants_class_routine(lower) and (
                lower.strip() == "today" or any(k in lower for k in _DAILY_KEYS)
            ):
                results.append(await run_tool("get_daily_schedule", ctx, section=sec or None))

            elif any(k in lower for k in ("list reminder", "my reminders", "show reminders")):
                results.append(await run_tool("list_reminders", ctx))

            elif any(k in lower for k in ("list routine", "my routines", "show routines")):
                results.append(await run_tool("list_routines", ctx))

            elif any(k in lower for k in ("list hook", "automation hook", "my hooks")):
                results.append(await run_tool("list_automation_hooks", ctx))

            elif any(
                k in lower
                for k in (
                    "enable routine",
                    "daily tomorrow",
                    "hour before class",
                    "routine automation",
                    "automate routine",
                )
            ):
                results.append(await run_tool("enable_routine_automation", ctx, section=sec or None))

            elif any(k in lower for k in ("pdf", "uploaded routine", "routine document")):
                results.append(await run_tool("read_department_routine_pdf", ctx, section=sec or None))

            if not results and plan.primary == "routine" and sec and wants_class_routine(lower):
                results.append(await run_tool("get_class_routine", ctx, section=sec))

            if not results and any(k in lower for k in ("pdf", "uploaded routine", "routine document")):
                results.append(await run_tool("read_routine_pdf", ctx, section=sec or None))

            if results:
                return format_tool_results(results).summary

            if plan.primary == "routine" and plan.tools:
                return (
                    "Class routines load from data/routines (CSV/PDF) via get_class_routine — "
                    "tell me your section and day (today/tomorrow)."
                )
        except Exception as e:
            logger.warning("RoutineAgent tool path failed: %s", e)

        if wants_class_routine(lower) or plan.primary == "routine":
            return (
                "No routine in data/routines for that section/day. "
                "Add CSV to data/routines/ or set your section (e.g. 64_I) with store_note."
            )

        return (
            "I load schedules from data/routines and tools only — "
            "ask for a class routine, reminders, or automation."
        )

    async def _resolve_section(self, ctx: Dict, plan_section: Optional[str]) -> str:
        explicit = normalize_section(plan_section) or self._section_from_context(ctx)
        if explicit:
            return explicit
        uid = int(ctx.get("user_id") or 0)
        if uid:
            return await recall_user_section(uid)
        return ""

    @staticmethod
    def _section_from_context(ctx: Dict) -> str:
        raw = (ctx.get("section") or "").strip()
        if not raw:
            return ""
        return resolve_section(section=raw, department=ctx.get("department"))
