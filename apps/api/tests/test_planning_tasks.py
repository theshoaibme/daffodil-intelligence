"""Planning agent task SSE emissions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.runtime.task_events import reset_turn_tasks, take_nested_events


def _sample_plan():
    from app.agents.planning import ExecutionPlan, PlanStep
    steps = [
        PlanStep(
            step_id="s1",
            description="Search async Python patterns",
            agent_type="research",
            tools=[],
            depends_on=[],
            input_template="Find async Python patterns",
        ),
        PlanStep(
            step_id="s2",
            description="Summarize findings",
            agent_type="general",
            tools=[],
            depends_on=["s1"],
            input_template="Summarize {s1}",
        ),
    ]
    return ExecutionPlan(goal="Research async Python", steps=steps)


@pytest.mark.asyncio
async def test_execute_plan_emits_step_tasks():
    from app.agents.planning import PlanningAgent

    reset_turn_tasks()
    plan = _sample_plan()
    agent = PlanningAgent()

    mock_research = MagicMock()
    mock_research.process = AsyncMock(return_value="research output")
    mock_general = MagicMock()
    mock_general.process = AsyncMock(return_value="summary output")

    with patch("app.agents.registry.AGENT_MAP", {"research": mock_research, "general": mock_general}), patch.object(
        agent,
        "generate_response",
        AsyncMock(return_value="final synthesis"),
    ):
        await agent._execute_plan(plan, context={"user_id": 0})

    events = take_nested_events()
    task_events = [e for e in events if e.get("type") == "task"]

    plan_roots = [e for e in task_events if e.get("kind") == "plan" and e.get("name", "").startswith("plan-")]
    assert len(plan_roots) >= 2
    assert any(e.get("status") == "active" for e in plan_roots)
    assert any(e.get("status") == "success" for e in plan_roots)

    step_events = [e for e in task_events if e.get("name") in ("s1", "s2")]
    assert len(step_events) >= 4
    assert all(e.get("short_title") for e in step_events)

    wave_groups = {e.get("parallel_group") for e in step_events if e.get("name") == "s1"}
    assert None not in wave_groups
    assert len(wave_groups) == 1
