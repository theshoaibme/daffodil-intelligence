"""Improvement exam routine — data/routines CSV, no section required."""

import asyncio

from app.automation.routine_csv import get_improvement_exam_routine
from app.runtime.pipeline import run_turn
from app.runtime.routine_turn import run_routine_fast_path, should_use_routine_fast_path
from app.runtime.tool_context import clear_turn_context, set_turn_context


def test_improvement_exam_csv_parsed():
    data = get_improvement_exam_routine()
    assert data["source"] == "csv"
    assert data["routine_type"] == "improvement_exam"
    assert data.get("weekly")
    assert sum(len(v) for v in data["weekly"].values()) == 36
    courses = " ".join(i["course"] for i in data["items"])
    assert "CSE421" in courses
    assert "Computer Graphics" in courses
    assert "CSE121/CSE132" in courses
    assert "CSE115 Introduction to Biology" in courses
    sunday = data["weekly"]["Sunday"]
    assert all(i.get("room") == "320 Knowledge Tower" for i in sunday)


def test_improvement_exam_by_day():
    data = get_improvement_exam_routine(day="Sunday")
    assert data.get("day") == "Sunday"
    assert data.get("items")
    assert any("CSE421" in i["course"] for i in data["items"])


def test_fast_path_improvement_exam_no_section():
    assert should_use_routine_fast_path(
        "Weekly class routine for improvement exam", "main"
    )
    set_turn_context(user_id=1, department="CSE")
    try:
        result = asyncio.run(
            run_routine_fast_path(
                "Weekly class routine for improvement exam",
                user_id=1,
                metadata={"department": "CSE"},
            )
        )
        assert result["engine"] == "routine"
        assert "Which section" not in (result.get("content") or "")
        assert result.get("ui_blocks")
        block = result["ui_blocks"][0]
        assert block.get("schema") in ("tabs", "data_table")
        if block.get("schema") == "tabs":
            tabs = (block.get("data") or {}).get("tabs") or []
            assert len(tabs) == 3
        else:
            rows = (block.get("data") or {}).get("rows") or []
            assert rows
            assert any("CSE421" in str(r.get("course", "")) for r in rows)
    finally:
        clear_turn_context()


def test_pipeline_improvement_exam():
    set_turn_context(user_id=1, department="CSE")
    try:
        result = asyncio.run(
            run_turn(
                "Weekly class routine for improvement exam",
                user_id=1,
                metadata={"department": "CSE"},
            )
        )
        assert result.get("engine") == "routine"
        assert "Which section" not in (result.get("content") or "")
        assert result.get("ui_blocks")
    finally:
        clear_turn_context()
