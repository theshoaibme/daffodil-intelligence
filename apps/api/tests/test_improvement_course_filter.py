"""Filter improvement exam routines by course name or code."""

import asyncio

from app.automation.routine_csv import get_improvement_exam_routine
from app.automation.routine_intent import extract_course_search_query
from app.runtime.routine_turn import run_routine_fast_path
from app.runtime.tool_context import clear_turn_context, set_turn_context


def test_extract_course_query_computer_graphics():
    q = extract_course_search_query(
        "Weekly class routine for improvement exam date computer graphics"
    )
    assert q == "computer graphics"


def test_improvement_exam_filter_single_course():
    data = get_improvement_exam_routine(course_query="computer graphics")
    assert data["source"] == "csv"
    assert len(data["items"]) == 1
    assert "CSE421" in data["items"][0]["course"]
    assert data["items"][0]["day"] == "Sunday"
    assert data["items"][0]["date"] == "14-06-2026"


def test_improvement_exam_filter_by_code():
    data = get_improvement_exam_routine(course_query="CSE421")
    assert len(data["items"]) == 1
    assert "Computer Graphics" in data["items"][0]["course"]


def test_fast_path_single_course_not_full_schedule():
    set_turn_context(user_id=1, department="CSE")
    try:
        result = asyncio.run(
            run_routine_fast_path(
                "Weekly class routine for improvement exam date computer graphics",
                user_id=1,
                metadata={"department": "CSE"},
            )
        )
        blocks = result.get("ui_blocks") or []
        assert len(blocks) == 1
        rows = (blocks[0].get("data") or {}).get("rows") or []
        assert len(rows) == 1
        assert "CSE421" in rows[0].get("course", "")
    finally:
        clear_turn_context()
