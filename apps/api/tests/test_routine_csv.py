"""Tests for bundled CSV class routines."""

import asyncio

from app.automation.routine_csv import get_csv_routine, list_csv_routine_catalog, load_parsed_csv
from app.automation.routine_resolver import resolve_routine_day
from app.automation.routines_data import get_uploaded_routine
from app.runtime.tool_context import clear_turn_context, set_turn_context
from app.tools.automation.routine import GetClassRoutineTool


def test_list_csv_routine_files():
    catalog = list_csv_routine_catalog()
    assert catalog["files"]
    names = {f["file"] for f in catalog["files"]}
    assert "cse-class-routine-v31-summer-2026.csv" in names
    assert "swe-routine-summer-2026-1.csv" in names


def test_cse_csv_section_saturday():
    data = get_csv_routine("66_C", "Saturday", department="CSE")
    assert data["source"] == "csv"
    assert data["day"] == "Saturday"
    assert data["items"]
    courses = " ".join(i["course"] for i in data["items"])
    assert "66_C" in courses or "CSE321" in courses


def test_swe_csv_section():
    data = get_csv_routine("42_E", "Saturday", department="SWE")
    assert data["source"] == "csv"
    assert data["items"]
    assert any("42" in i["course"] for i in data["items"])


def test_get_uploaded_routine_uses_csv():
    data = get_uploaded_routine("66_C", "Saturday", department="CSE")
    assert data["source"] == "csv"
    assert len(data["items"]) >= 1


def test_get_uploaded_routine_empty_csv_day():
    data = get_uploaded_routine("66_C", "Wednesday", department="CSE")
    assert data["source"] == "csv"
    assert data["day"] == "Wednesday"
    assert data["items"] == []


def test_cse_parsed_section_count():
    from pathlib import Path

    from app.automation.routine_resolver import ROUTINE_DATA_ROOT

    path = ROUTINE_DATA_ROOT / "cse-class-routine-v31-summer-2026.csv"
    parsed = load_parsed_csv(str(path.resolve()))
    assert parsed.format == "cse_grid"
    assert len(parsed.sections) > 50
    assert "66_C" in parsed.sections


def test_resolve_routine_day_relative():
    thursday = resolve_routine_day("Thursday")
    assert thursday == "Thursday"
    tomorrow = resolve_routine_day("tomorrow")
    assert tomorrow in (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )


def test_get_uploaded_routine_tomorrow_resolves_weekday():
    """tomorrow must map to a real weekday, not the literal string 'Tomorrow'."""
    tomorrow_day = resolve_routine_day("tomorrow")
    data = get_uploaded_routine("64_I", "tomorrow", department="CSE")
    assert data["day"] == tomorrow_day
    thursday_data = get_uploaded_routine("64_I", "Thursday", department="CSE")
    if tomorrow_day == "Thursday":
        assert len(data["items"]) == len(thursday_data["items"])


def test_get_class_routine_tool_tomorrow():
    set_turn_context(user_id=1, department="CSE")
    try:
        result = asyncio.run(
            GetClassRoutineTool().execute(section="64_I", day="tomorrow", department="CSE")
        )
        assert result.success
        assert result.data.get("day") == resolve_routine_day("tomorrow")
        tomorrow_day = resolve_routine_day("tomorrow")
        if tomorrow_day == "Thursday":
            assert len(result.data.get("items") or []) == 3
    finally:
        clear_turn_context()


def test_get_class_routine_tool_csv():
    set_turn_context(user_id=1, department="CSE")
    try:
        result = asyncio.run(
            GetClassRoutineTool().execute(section="66_C", day="Saturday", department="CSE")
        )
        assert result.success
        assert result.data.get("source") == "csv"
        assert result.data.get("items")
    finally:
        clear_turn_context()
