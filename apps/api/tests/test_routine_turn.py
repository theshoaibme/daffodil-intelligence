"""Tests for routine fast-path routing (data/routines, no LLM invention)."""

import asyncio

from app.runtime.pipeline import run_turn
from app.runtime.routine_turn import (
    run_routine_fast_path,
    should_use_routine_fast_path,
    stream_routine_fast_path,
)
from app.runtime.tool_context import clear_turn_context, set_turn_context


def test_should_use_routine_fast_path():
    assert should_use_routine_fast_path("show my class routine", "main")
    assert should_use_routine_fast_path("tomorrow class routine for 64_I", "main")
    assert should_use_routine_fast_path("64_I", "main")
    assert not should_use_routine_fast_path("what is cgpa", "main")
    assert not should_use_routine_fast_path("class routine", "academic")


def test_routine_fast_path_uses_csv_not_llm():
    set_turn_context(user_id=1, section="64_I", department="CSE")
    try:
        result = asyncio.run(
            run_routine_fast_path(
                "Show tomorrow's class routine",
                user_id=1,
                metadata={"section": "64_I", "department": "CSE"},
            )
        )
        assert result["engine"] == "routine"
        assert "Mathematics" not in result["content"]
        assert "English" not in result["content"]
        assert result.get("ui_blocks")
    finally:
        clear_turn_context()


def test_stream_routine_fast_path_emits_tasks():
    set_turn_context(user_id=1, section="64_I", department="CSE")
    try:

        async def _collect():
            events = []
            async for event in stream_routine_fast_path(
                "tomorrow class routine",
                user_id=1,
                metadata={"section": "64_I", "department": "CSE"},
            ):
                events.append(event)
            return events

        events = asyncio.run(_collect())
        task_events = [e for e in events if e.get("type") == "task"]
        assert len(task_events) >= 3
        depths = sorted(t.get("depth") for t in task_events if "depth" in t)
        assert 0 in depths and 1 in depths and 2 in depths
    finally:
        clear_turn_context()


def test_stream_routine_fast_path_emits_ui():
    set_turn_context(user_id=1, section="64_I", department="CSE")
    try:

        async def _collect():
            events = []
            async for event in stream_routine_fast_path(
                "tomorrow class routine",
                user_id=1,
                metadata={"section": "64_I", "department": "CSE"},
            ):
                events.append(event)
            return events

        events = asyncio.run(_collect())
        types = [e.get("type") for e in events]
        assert "task" in types
        assert any(e.get("type") == "ui" for e in events)
        assert any(e.get("type") == "content" for e in events)
        assert any(e.get("type") == "content" for e in events)
    finally:
        clear_turn_context()


def test_pipeline_run_turn_routine_fast_path():
    set_turn_context(user_id=1, section="64_I", department="CSE")
    try:
        result = asyncio.run(
            run_turn(
                "Show tomorrow's class routine",
                user_id=1,
                metadata={"section": "64_I", "department": "CSE"},
            )
        )
        assert result.get("engine") == "routine"
        assert "Mathematics" not in (result.get("content") or "")
    finally:
        clear_turn_context()
