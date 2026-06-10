"""Tests for automation tools and store."""

import asyncio
import json

import pytest

from app.automation import routine_resolver
from app.automation.routine_resolver import save_routine_upload
from app.automation.routines_data import get_uploaded_routine
from app.automation.store import automation_store
from app.runtime.tool_context import clear_turn_context, set_turn_context
from app.tools.automation.agents import InvokeAgentTool, ListAgentsTool
from app.tools.automation.reminders import CreateReminderTool, ListRemindersTool
from app.tools.automation.routine import GetClassRoutineTool


@pytest.fixture(autouse=True)
def _tool_ctx():
    set_turn_context(user_id=42, department="CSE", selected_tools=["Planning"])
    yield
    clear_turn_context()


@pytest.fixture
def routine_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(routine_resolver, "ROUTINE_DATA_ROOT", tmp_path)
    yield tmp_path


@pytest.fixture
def uploaded_routine(routine_data_root):
    weekly = {
        "Monday": [
            {
                "time": "10:00",
                "course": "TST101",
                "title": "Test Course",
                "room": "101",
                "teacher": "Test Prof",
                "type": "class",
            }
        ],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    }
    section = "99_Z"
    payload = json.dumps({"section": section, "weekly": weekly}).encode()
    save_routine_upload(
        department="TEST",
        section=section,
        filename=f"{section}.json",
        content=payload,
    )
    yield section


def test_get_uploaded_routine(uploaded_routine):
    section = uploaded_routine
    data = get_uploaded_routine(section, "Monday", department="TEST")
    assert data["section"] == section
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


def test_get_class_routine_tool(uploaded_routine):
    section = uploaded_routine
    result = asyncio.run(
        GetClassRoutineTool().execute(section=section, day="Monday", department="TEST")
    )
    assert result.success
    assert result.data.get("day") == "Monday" or result.data.get("items")
