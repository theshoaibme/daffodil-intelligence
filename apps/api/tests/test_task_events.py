"""Task graph event helpers."""

from app.runtime.task_events import emit_task, reset_turn_tasks, take_nested_events
from app.tools.automation.agents import _parse_agent_types


def test_emit_task_nested():
    reset_turn_tasks()
    root = emit_task(kind="agent", name="main", status="active", depth=0)
    child = emit_task(
        parent_id=root["task_id"],
        kind="agent",
        name="routine",
        status="active",
        agent_id="routine",
        parallel_group="g1",
        depth=1,
    )
    events = take_nested_events()
    assert len(events) >= 2
    assert child["parallel_group"] == "g1"
    assert child["agent_id"] == "routine"


def test_parse_agent_types():
    assert _parse_agent_types("routine, research") == ["routine", "research"]
    assert _parse_agent_types('["planning","exam"]') == ["planning", "exam"]
