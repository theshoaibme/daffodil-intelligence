"""Master agent tool dispatch tests."""

import pytest

from app.master_agent import MasterAgent, TaskContext
from app.tools.registry import get_registry


@pytest.mark.asyncio
async def test_execute_tool_passes_inferred_kwargs(monkeypatch):
    agent = MasterAgent()
    registry = get_registry()
    tool = registry.get("get_cgpa")
    assert tool is not None

    captured = {}

    async def fake_execute(name, **kwargs):
        captured["name"] = name
        captured["kwargs"] = kwargs
        from app.tools.base import ToolResult
        return ToolResult(success=True, data={"cgpa": 3.5}, tool_name=name)

    monkeypatch.setattr(registry, "execute", fake_execute)

    session_id = "sess1"
    agent._sessions[session_id] = {
        "session_id": session_id,
        "prompt": "what is my cgpa for 221-15-1234",
        "student_id": None,
        "user_id": 1,
        "tasks": [],
    }

    task = TaskContext(
        task_id="t1",
        session_id=session_id,
        task_type="tool",
        name="get_cgpa",
    )
    await agent._execute_tool(task, "what is my cgpa for 221-15-1234")

    assert captured["name"] == "get_cgpa"
    assert captured["kwargs"]["student_id"] == "221-15-1234"
    assert task.result["status"] == "executed"


@pytest.mark.asyncio
async def test_execute_tool_reports_missing_required_args():
    agent = MasterAgent()
    session_id = "sess2"
    agent._sessions[session_id] = {"session_id": session_id, "user_id": 1, "tasks": []}

    task = TaskContext(
        task_id="t2",
        session_id=session_id,
        task_type="tool",
        name="get_cgpa",
    )
    await agent._execute_tool(task, "what is my cgpa")

    assert task.result["status"] == "failed"
    assert "student_id" in task.result["error"]
