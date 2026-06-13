"""Agent simulation tool → agent mapping."""

from app.runtime.agent_simulation import (
    PRODUCTIVITY_AGENT_IDS,
    GENERAL_AGENT_IDS,
    agents_for_tool,
)


def test_productivity_agents():
    assert "writing" in PRODUCTIVITY_AGENT_IDS
    assert "tasks" in PRODUCTIVITY_AGENT_IDS
    assert len(PRODUCTIVITY_AGENT_IDS) >= 4


def test_event_is_general_agent():
    assert "event" in GENERAL_AGENT_IDS


def test_hooks_map_to_event_agent():
    assert "event" in agents_for_tool("create_automation_hook")


def test_read_pdf_maps_writing_and_routine():
    agents = agents_for_tool("read_pdf")
    assert "writing" in agents
    assert "routine" in agents


def test_deep_research_maps_research():
    assert "research" in agents_for_tool("deep_research")


def test_schedule_task_maps_tasks():
    assert "tasks" in agents_for_tool("schedule_task")
