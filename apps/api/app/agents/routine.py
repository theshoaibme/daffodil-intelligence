from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool
from ..automation.routine_memory import recall_user_section
from ..automation.routine_resolver import normalize_section, resolve_section
from ..runtime.intent_router import route_message

logger = logging.getLogger(__name__)

ROUTINE_TOOLS = [
    "get_class_routine",
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


class RoutineAgent(BaseAgent):
    name = "Routine Agent"
    description = "Schedules, class routines, reminders, habits, and automation hooks"
    tools = ROUTINE_TOOLS

    SYSTEM_PROMPT = """You are the Routine Agent for Daffodil Intelligence.
Use tools for real data — never invent schedules.
Class routines come from MCP tools, agent memory, skills, or department PDF uploads.
Call get_class_routine, read_department_routine_pdf, and recall_notes before answering.
Use store_note to save section or schedule facts. Use MCP integrations for external PDF/files.
If section is missing, ask once. Do not repeat the generic greeting."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = context or {}
        plan = route_message(message)
        lower = (message or "").lower()
        results: List = []

        try:
            sec = await self._resolve_section(ctx, plan.section)

            if plan.section or any(k in lower for k in ("class routine", "class schedule", "my routine")):
                if not sec:
                    return (
                        "Which section's class routine do you need? "
                        "I can also look it up from your saved memory or routine skills."
                    )
                results.append(await run_tool("get_class_routine", ctx, section=sec))

            elif any(k in lower for k in ("list reminder", "my reminders", "show reminders")):
                results.append(await run_tool("list_reminders", ctx))

            elif any(k in lower for k in ("list routine", "my routines", "show routines")):
                results.append(await run_tool("list_routines", ctx))

            elif any(k in lower for k in ("list hook", "automation hook", "my hooks")):
                results.append(await run_tool("list_automation_hooks", ctx))

            elif any(k in lower for k in ("today", "daily schedule", "plan my day")):
                results.append(await run_tool("get_daily_schedule", ctx, section=sec or None))

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

            if results and any(r.success for r in results):
                return format_tool_results(results)

            if plan.primary == "routine" and plan.tools:
                return (
                    f"I can help with: {', '.join(plan.tools)}. "
                    "Tell me what you need — class routine, reminders, or automation."
                )
        except Exception as e:
            logger.warning("RoutineAgent tool path failed: %s", e)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

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
