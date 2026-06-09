"""Tests for automation tools and store."""

import asyncio

import pytest

from app.automation.routines_data import get_section_routine
from app.automation.store import automation_store
from app.runtime.tool_context import clear_turn_context, set_turn_context
from app.tools.automation.agents import InvokeAgentTool, ListAgentsTool
from app.tools.automation.reminders import CreateReminderTool, ListRemindersTool
from app.tools.automation.routine import GetClassRoutineTool


@pytest.fixture(autouse=True)
def _tool_ctx():
    set_turn_context(user_id=42, section="64_I", selected_tools=["Planning"])
    yield
    clear_turn_context()


def test_get_section_routine():
    data = get_section_routine("64_I", "Monday")
    assert data["section"] == "64_I"
    assert len(data["items"]) >= 1


def test_list_agents_tool():
    pytest.importorskip("langchain")
    result = asyncio.run(ListAgentsTool().execute())
    assert result.success
    assert result.data["count"] >= 10
    ids = [a["id"] for a in result.data["agents"]]
    assert "routine" in ids
    assert "planning" in ids


def test_invoke_routine_agent():
    pytest.importorskip("langchain")
    result = asyncio.run(
        InvokeAgentTool().execute(agent_type="routine", message="show my reminders")
    )
    assert result.success
    assert "reminder" in result.data["response"].lower() or "Reminder" in result.data["response"]


def test_get_class_routine_tool():
    result = asyncio.run(GetClassRoutineTool().execute(section="64_I", day="Monday"))
    assert result.success
    assert result.data["day"] == "Monday"


def test_reminder_crud():
    created = asyncio.run(
        CreateReminderTool().execute(title="Test class", fire_at="2099-01-01T10:00:00")
    )
    assert created.success
    rid = created.data["reminder"]["id"]

    listed = asyncio.run(ListRemindersTool().execute())
    assert listed.success
    assert any(r["id"] == rid for r in listed.data["reminders"])

    automation_store.delete_reminder(42, rid)
