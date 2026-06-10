"""Routine PDF lookup — convenience wrapper over read_pdf + department paths."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.routine_memory import recall_user_section
from ...automation.routine_pdf_reader import read_routine_pdf_fast
from ...automation.routine_resolver import department_data_dir, resolve_section
from ...runtime.tool_context import get_department, get_section, get_user_id


class ReadRoutinePdfTool(BaseTool):
    name = "read_routine_pdf"
    description = (
        "Read department routine PDF from data/routines/{department}/. "
        "For arbitrary PDF paths use read_pdf instead."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="department", type="string", description="Department", required=False),
        ToolParameter(name="section", type="string", description="Section code", required=False),
        ToolParameter(name="day", type="string", description="Weekday e.g. Monday", required=False),
        ToolParameter(
            name="query",
            type="string",
            description="Keyword filter e.g. course code",
            required=False,
        ),
        ToolParameter(
            name="max_chars",
            type="integer",
            description="Max characters (default 4000)",
            required=False,
            default=4000,
        ),
    ]

    async def execute(
        self,
        department: str = None,
        section: str = None,
        day: str = None,
        query: str = None,
        max_chars: int = 4000,
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
            return self.fail("Section required — ask user or save with store_note")

        result = read_routine_pdf_fast(
            dept,
            sec,
            day=day.strip() if day else None,
            query=query.strip() if query else None,
            max_chars=int(max_chars or 4000),
        )
        if result.get("error"):
            folder = department_data_dir(dept)
            return self.fail(
                f"No routine file for {dept} section {sec}. "
                f"Place PDF at {folder}/{sec}.pdf or use read_pdf with a file path."
            )
        return self.ok(result)
