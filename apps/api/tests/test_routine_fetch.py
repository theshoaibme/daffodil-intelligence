"""Tests for data/routines-only class routine fetch (no hardcoded schedules)."""

import asyncio

from app.automation.routine_fetch import fetch_class_routine, routine_has_schedule
from app.runtime.tool_context import clear_turn_context, set_turn_context
from app.tools.automation.routine import GetClassRoutineTool


def test_fetch_from_csv():
    data = asyncio.run(
        fetch_class_routine(section="66_C", day="Saturday", department="CSE")
    )
    assert data.get("source") == "csv"
    assert routine_has_schedule(data)
    assert data.get("items")


def test_fetch_tomorrow_resolves_weekday():
    data = asyncio.run(
        fetch_class_routine(section="64_I", day="tomorrow", department="CSE")
    )
    assert data.get("day")
    assert data.get("source") in ("csv", "none", "memory", "data_folder_pdf")


def test_fetch_empty_section():
    data = asyncio.run(fetch_class_routine(section=""))
    assert data.get("error") == "section_required"


def test_tool_never_invents_subjects():
    set_turn_context(user_id=1, department="CSE", section="64_I")
    try:
        result = asyncio.run(
            GetClassRoutineTool().execute(section="64_I", day="tomorrow", department="CSE")
        )
        body = str(result.data) + str(result.summary or "") + str(result.error or "")
        assert "Mathematics" not in body
        assert "English" not in body
        assert "Lunch Break" not in body
    finally:
        clear_turn_context()
