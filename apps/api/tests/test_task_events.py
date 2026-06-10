"""Task graph event helpers."""

from app.runtime.task_events import emit_task, reset_turn_tasks, take_nested_events
from app.runtime.task_titles import short_title
from app.tools.automation.agents import _parse_agent_types


def test_short_title_strips_prefix_and_truncates():
    assert short_title("Agent: Research quantum computing trends") == "Research quantum computing trends"
    assert short_title("Tool: Google Web Search") == "Google Web Search"
    long_text = "A" * 60
    assert short_title(long_text).endswith("...")
    assert len(short_title(long_text)) == 48


def test_emit_task_includes_short_title_from_title():
    reset_turn_tasks()
    event = emit_task(
        kind="agent",
        name="main",
        title="Orchestrator (main)",
        status="active",
        depth=0,
    )
    assert event["short_title"] == "Orchestrator (main)"


def test_emit_task_includes_explicit_short_title():
    reset_turn_tasks()
    event = emit_task(
        kind="tool",
        name="deep_research",
        title="Tool: Deep research on async Python patterns",
        short_title="Deep research",
        status="active",
        depth=1,
    )
    assert event["short_title"] == "Deep research"
    assert take_nested_events()[-1]["short_title"] == "Deep research"


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


def test_emit_task_root_id_links_children():
    reset_turn_tasks()
    root = emit_task(kind="agent", name="main", status="active", depth=0)
    child = emit_task(
        kind="agent",
        name="planning",
        status="active",
        depth=1,
    )
    assert root["task_id"].startswith("root-")
    assert child["parent_id"] == root["task_id"]
    assert "parent_id" not in root or root.get("parent_id") is None


def test_emit_task_root_completion_reuses_same_id():
    reset_turn_tasks()
    root = emit_task(kind="agent", name="main", status="active", depth=0)
    done = emit_task(
        task_id=root["task_id"],
        kind="agent",
        name="main",
        status="success",
        depth=0,
    )
    assert done["task_id"] == root["task_id"]
