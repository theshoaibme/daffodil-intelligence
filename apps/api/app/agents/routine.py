from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool
from ..runtime.intent_router import route_message

logger = logging.getLogger(__name__)

_SECTION_CODE = re.compile(r"\b(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\b", re.I)

ROUTINE_TOOLS = [
    "get_class_routine",
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


class RoutineAgent(BaseAgent):
    name = "Routine Agent"
    description = "Schedules, class routines, reminders, habits, and automation hooks"
    tools = ROUTINE_TOOLS

    SYSTEM_PROMPT = """You are the Routine Agent for Daffodil Intelligence.
Always use tools for real data — never invent schedules or reminders.
Tools: get_class_routine, enable_routine_automation, create/list/delete reminders,
create/list personal routines, get_daily_schedule, schedule_task, automation hooks.
If section is missing for class routine, ask once for section (e.g. 64_I).
Do not repeat the generic greeting."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = context or {}
        plan = route_message(message)
        lower = (message or "").lower()
        results = []

        try:
            if plan.section:
                results.append(
                    await run_tool("get_class_routine", ctx, section=plan.section)
                )
            elif any(k in lower for k in ("class routine", "class schedule", "my routine")):
                sec = self._section_from_context(ctx)
                if sec:
                    results.append(await run_tool("get_class_routine", ctx, section=sec))
                else:
                    return (
                        "Which section's class routine do you need? "
                        "For example: `64_I` or `6C1`."
                    )

            elif any(k in lower for k in ("list reminder", "my reminders", "show reminders")):
                results.append(await run_tool("list_reminders", ctx))

            elif any(k in lower for k in ("list routine", "my routines", "show routines")):
                results.append(await run_tool("list_routines", ctx))

            elif any(k in lower for k in ("list hook", "automation hook", "my hooks")):
                results.append(await run_tool("list_automation_hooks", ctx))

            elif any(k in lower for k in ("today", "daily schedule", "plan my day")):
                sec = self._section_from_context(ctx)
                results.append(await run_tool("get_daily_schedule", ctx, section=sec))

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
                sec = self._section_from_context(ctx)
                results.append(
                    await run_tool(
                        "enable_routine_automation",
                        ctx,
                        section=sec,
                    )
                )

            if results and any(r.success for r in results):
                return format_tool_results(results)

            if plan.primary == "routine" and plan.tools:
                return (
                    f"I can help with: {', '.join(plan.tools)}. "
                    "Tell me what you need — e.g. class routine for 64_I, list reminders, "
                    "or enable daily class alerts."
                )
        except Exception as e:
            logger.warning("RoutineAgent tool path failed: %s", e)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    @staticmethod
    def _section_from_context(ctx: Dict) -> str:
        raw = (ctx.get("section") or "64_I").strip().upper()
        if raw == "CSE":
            return "64_I"
        m = _SECTION_CODE.search(raw)
        return m.group(1).upper() if m else raw
