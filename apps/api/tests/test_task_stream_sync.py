"""SSE task stream contract: root/child IDs and event shape for TaskPanel sync."""

from app.runtime.task_events import emit_task, reset_turn_tasks, take_nested_events


def test_sse_task_event_shape_includes_short_title():
    reset_turn_tasks()
    event = emit_task(
        kind="tool",
        name="deep_research",
        title="Tool: Deep research on async Python patterns",
        short_title="Deep research",
        status="active",
        depth=2,
        parent_id="root-abc",
    )
    required = {
        "type",
        "task_id",
        "parent_id",
        "kind",
        "name",
        "title",
        "short_title",
        "status",
        "depth",
    }
    assert required.issubset(event.keys())
    assert event["type"] == "task"
    assert event["short_title"] == "Deep research"


def test_orchestrator_tree_start_and_complete_same_root_id():
    """Mirrors pipeline stream: root active → child → root success uses one ID."""
    reset_turn_tasks()
    root = emit_task(
        kind="agent",
        name="main",
        title="Orchestrator (main)",
        status="active",
        agent_id="main",
        depth=0,
    )
    root_id = root["task_id"]
    plan = emit_task(
        kind="plan",
        name="plan-1",
        title="Research async Python",
        status="active",
        agent_id="planning",
        depth=1,
    )
    assert plan["parent_id"] == root_id

    complete = emit_task(
        task_id=root_id,
        kind="agent",
        name="main",
        title="Orchestrator (main)",
        status="success",
        agent_id="main",
        depth=0,
    )
    assert complete["task_id"] == root_id

    events = take_nested_events()
    root_events = [e for e in events if e.get("task_id") == root_id]
    assert len(root_events) >= 2
    assert root_events[0]["status"] == "active"
    assert root_events[-1]["status"] == "success"
