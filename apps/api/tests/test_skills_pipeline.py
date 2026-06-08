"""Skills hub, resolver, copycat auto-skill, and unified pipeline tests."""

import pytest

from app.skills.copycat import create_skill_from_recording
from app.skills.resolver import resolve_runtime_config
from app.skills.store import skill_store, ruleset_store, global_config_store, agent_profile_store, _memory
from app.skills.models import AgentProfile, GlobalAgentConfig
from app.runtime import pipeline


@pytest.fixture(autouse=True)
def isolated_stores(monkeypatch):
    monkeypatch.setattr("app.core.database._use_mock", True)
    _memory.reset()
    yield


def test_copycat_creates_skill():
    skill = create_skill_from_recording("login_flow", action_count=12, duration=4.5, created_by=1)
    assert skill is not None
    assert skill["source"] == "copycat"
    assert skill["recording_name"] == "login_flow"
    assert "replay_recording" in skill["tool_names"]


@pytest.mark.asyncio
async def test_resolver_merges_global_rules_and_skills():
    rs = ruleset_store.create("Safety", "Global rules", ["Never share passwords"], is_public=True)
    sk = skill_store.create(
        "Notes",
        "Memory helper",
        "Use store_note for long-term facts.",
        tool_names=["store_note"],
        is_public=True,
    )
    global_config_store.save(GlobalAgentConfig(
        ruleset_ids=[rs.id],
        skill_ids=[sk.id],
        extra_system="Always be concise.",
        default_agent_id="academic",
    ))
    agent_profile_store.upsert(AgentProfile(
        agent_id="academic",
        extra_system="Focus on DIU academic policies.",
    ))

    cfg = await resolve_runtime_config(agent_id="academic", user_id=1)
    assert cfg.agent_id == "academic"
    assert "Always be concise." in cfg.extra_system
    assert "Safety" in cfg.extra_system
    assert "Skill: Notes" in cfg.extra_system
    assert "Academic Agent" in cfg.extra_system or "specialist" in cfg.extra_system


@pytest.mark.asyncio
async def test_pipeline_delegates_to_orchestrator(monkeypatch):
    captured = {}

    async def fake_run(message, **kwargs):
        captured.update(kwargs)
        return {"content": f"ok:{message}", "tool_calls": [], "engine": "antigravity"}

    monkeypatch.setattr("app.runtime.orchestrator.run", fake_run)

    result = await pipeline.run_turn(
        "hello",
        user_id=5,
        chat_id="c1",
        agent_id="coding",
        context_prefix="User profile: role=student",
    )
    assert result["content"] == "ok:User profile: role=student\n\nhello"
    assert captured["agent_id"] == "coding"
    assert captured.get("extra_system") is not None or captured.get("extra_system") == ""
