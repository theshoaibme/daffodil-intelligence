"""Personal tasks, schedules, and habit productivity agent."""

from __future__ import annotations

from typing import Dict, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool


class TasksAgent(BaseAgent):
    name = "Tasks Agent"
    description = "Personal schedules, daily tasks, habits, and reminders"
    tools = [
        "schedule_task",
        "get_daily_schedule",
        "create_routine",
        "list_routines",
        "delete_routine",
        "create_reminder",
        "list_reminders",
        "delete_reminder",
    ]

    SYSTEM_PROMPT = """You are the Tasks Agent for Daffodil Intelligence.
You manage personal productivity: daily schedules, task lists, habits, and reminders."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        lower = message.lower()
        ctx = context or {}
        results = []

        if any(k in lower for k in ("daily", "today", "schedule")):
            results.append(await run_tool("get_daily_schedule", ctx))
        elif any(k in lower for k in ("remind", "reminder", "alert me")):
            results.append(await run_tool("list_reminders", ctx))
        elif any(k in lower for k in ("habit", "routine", "recurring")):
            results.append(await run_tool("list_routines", ctx))
        elif any(k in lower for k in ("task", "todo", "plan my day")):
            results.append(await run_tool("schedule_task", ctx, title=message))

        if results:
            return format_tool_results(results)
        return await self.generate_response(self.SYSTEM_PROMPT, message)
