"""Pipeline and turn-memory integration tests."""

import pytest

from app.memory import memory_service
from app.runtime import pipeline
from app.runtime.agent_factory import AgentPersona
from app.skills.resolver import RuntimeConfig


@pytest.mark.asyncio
async def test_pipeline_injects_recall_context(monkeypatch):
    captured: dict = {}

    async def fake_cfg(**_kwargs):
        return RuntimeConfig(agent_id="main", persona=AgentPersona.MAIN, extra_system="Base prompt.")

    async def fake_recall_context(user_id, agent_id, message, *, chat_id=None):
        return "## Recalled memory\n- [fact] User prefers concise answers"

    async def fake_run(message, **kwargs):
        captured.update(kwargs)
        return {"content": f"ok:{message}", "tool_calls": [], "engine": "antigravity"}

    monkeypatch.setattr("app.runtime.pipeline.resolve_runtime_config", fake_cfg)
    monkeypatch.setattr(memory_service, "build_recall_context", fake_recall_context)
    monkeypatch.setattr("app.runtime.orchestrator.run", fake_run)

    result = await pipeline.run_turn("hello", user_id=5, chat_id=42, agent_id="main")
    assert "ok:" in result["content"]
    extra = captured.get("extra_system") or ""
    assert "Recalled memory" in extra
    assert "Base prompt." in extra


@pytest.mark.asyncio
async def test_process_turn_memory_best_effort():
    await memory_service.process_turn_memory(
        user_id=99,
        agent_id="main",
        chat_id="test-chat",
        user_msg="What is my CGPA?",
        assistant_msg="Your CGPA is 3.5.",
        turn_index=1,
    )


@pytest.mark.asyncio
async def test_store_subagent_event_best_effort():
    await memory_service.store_subagent_event(
        user_id=99,
        parent_agent_id="main",
        subagent_id="sub-001",
        name="researcher",
        task="Look up exam schedule",
        result_summary="Exam is on May 20.",
        chat_id=7,
    )
