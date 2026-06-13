"""Tests for generic UI block mappers and present_ui tool."""

import asyncio

import pytest

from app.tools.base import ToolResult
from app.ui_blocks.mappers import enrich_tool_result, format_tool_results, map_tool_result
from app.ui_blocks.schemas import validate_block_payload
from app.tools.ui.present_ui import PresentUiTool


def test_map_routine_weekly_as_data_table():
    result = ToolResult(
        success=True,
        tool_name="get_class_routine",
        data={
            "section": "CSE-12",
            "weekly": {
                "Mon": [
                    {
                        "time": "09:00",
                        "course": "CSE101",
                        "title": "Intro",
                        "room": "A1",
                        "teacher": "Dr. X",
                    }
                ]
            },
        },
    )
    blocks = map_tool_result("get_class_routine", result)
    assert len(blocks) == 1
    assert blocks[0].block_type == "data_table"
    assert blocks[0].data["rows"][0]["day"] == "Mon"


def test_map_routine_day_empty():
    result = ToolResult(
        success=True,
        tool_name="get_class_routine",
        data={"section": "CSE-12", "day": "Sun", "items": []},
    )
    blocks = map_tool_result("get_class_routine", result)
    assert blocks[0].block_type == "status_card"


def test_map_routine_day_orders_columns():
    result = ToolResult(
        success=True,
        tool_name="get_class_routine",
        data={
            "section": "64_I",
            "day": "Thursday",
            "items": [
                {"teacher": "MSS", "course": "CSE431(64_I)", "room": "KT-515", "time": "10:00-11:30"},
                {"teacher": "MAR", "course": "CSE432(64_I)", "room": "KT-517", "time": "01:00-02:30"},
            ],
        },
    )
    blocks = map_tool_result("get_class_routine", result)
    assert blocks[0].block_type == "data_table"
    cols = [c["key"] for c in blocks[0].data["columns"]]
    assert cols[:4] == ["time", "course", "room", "teacher"]
    times = [r["time"] for r in blocks[0].data["rows"]]
    assert times == ["01:00-02:30", "10:00-11:30"]


def test_map_daily_schedule_as_tables():
    result = ToolResult(
        success=True,
        tool_name="get_daily_schedule",
        data={
            "section": "CSE-12",
            "day": "Wednesday",
            "classes": [
                {"time": "09:00", "course": "CSE101", "title": "Intro", "room": "A1", "teacher": "Dr. X"}
            ],
            "reminders": [{"id": "r1", "title": "Lab", "fire_at": "2026-06-10T14:00", "repeat": "once"}],
            "routines": [],
        },
    )
    blocks = map_tool_result("get_daily_schedule", result)
    assert all(b.block_type == "data_table" for b in blocks)
    assert len(blocks) == 2


def test_map_reminders():
    result = ToolResult(
        success=True,
        tool_name="list_reminders",
        data={
            "reminders": [
                {"id": "r1", "title": "Lab", "fire_at": "2026-06-10T09:00", "repeat": "once"}
            ]
        },
    )
    blocks = map_tool_result("list_reminders", result)
    assert blocks[0].block_type == "data_table"
    assert len(blocks[0].data["rows"]) == 1


def test_normalize_legacy_routine_weekly_block():
    from app.ui_blocks.schemas import UiBlock

    legacy = UiBlock(
        block_type="routine_weekly",
        title="Class routine — 64_I",
        data={
            "section": "64_I",
            "weekly": {
                "Tuesday": [
                    {"time": "08:30-10:00", "course": "CSE431(64_I)", "room": "KT-515", "teacher": "MSS"}
                ]
            },
        },
    )
    result = ToolResult(success=True, tool_name="get_class_routine", data={}, ui_blocks=[legacy])
    blocks = map_tool_result("get_class_routine", result)
    assert blocks[0].block_type == "data_table"
    assert blocks[0].data["rows"][0]["day"] == "Tuesday"


def test_map_error():
    result = ToolResult(success=False, tool_name="x", error="boom")
    blocks = map_tool_result("x", result)
    assert blocks[0].block_type == "error_alert"


def test_format_tool_results_summary():
    results = [
        ToolResult(
            success=True,
            tool_name="list_reminders",
            data={"reminders": [{"id": "1", "title": "A", "fire_at": "t", "repeat": "once"}]},
        )
    ]
    presentation = format_tool_results(results)
    assert "reminder" in presentation.summary.lower()
    assert presentation.blocks[0].block_type == "data_table"


def test_enrich_attaches_summary():
    result = ToolResult(
        success=True,
        tool_name="enable_routine_automation",
        data={"status": "ok", "section": "CSE-12"},
    )
    enriched = enrich_tool_result(result)
    assert enriched.summary
    assert enriched.ui_blocks


def test_validate_block_payload_rejects_unknown_schema():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_block_payload({"schema": "routine_weekly", "data": {}})


def test_present_ui_tool():
    async def _run():
        tool = PresentUiTool()
        bad = await tool.execute(summary="", blocks=[])
        assert not bad.success

        ok = await tool.execute(
            summary="Schedule ready.",
            blocks=[
                {
                    "schema": "status_card",
                    "data": {"tone": "success", "message": "Done"},
                }
            ],
        )
        assert ok.success
        assert ok.summary == "Schedule ready."
        assert len(ok.ui_blocks) == 1

    asyncio.run(_run())
