"""Per-agent tool binding: skills and custom-agent capabilities drive tool_names."""

import pytest

from app.skills.resolver import resolve_runtime_config
from app.skills.store import _memory, global_config_store, skill_store
from app.skills.models import GlobalAgentConfig


@pytest.fixture(autouse=True)
def isolated_stores(monkeypatch):
    monkeypatch.setattr("app.core.database._use_mock", True)
    _memory.reset()
    yield


@pytest.mark.asyncio
async def test_skill_tool_names_become_allowlist():
    sk = skill_store.create(
        "Notes",
        "Memory helper",
        "Use store_note for long-term facts.",
        tool_names=["store_note", "recall_notes"],
        is_public=True,
    )
    global_config_store.save(GlobalAgentConfig(skill_ids=[sk.id], default_agent_id="main"))

    cfg = await resolve_runtime_config(agent_id="main", user_id=0)
    assert cfg.tool_names is not None
    assert "store_note" in cfg.tool_names
    assert "recall_notes" in cfg.tool_names


@pytest.mark.asyncio
async def test_no_tools_means_no_allowlist():
    sk = skill_store.create("Plain", "No tools", "Just guidance.", is_public=True)
    global_config_store.save(GlobalAgentConfig(skill_ids=[sk.id], default_agent_id="main"))

    cfg = await resolve_runtime_config(agent_id="main", user_id=0)
    assert cfg.tool_names is None


@pytest.mark.asyncio
async def test_custom_agent_capability_tools(monkeypatch):
    from app.agents import builder
    from app.agents.builder import AgentCapability, register_agent

    monkeypatch.setattr(builder, "AGENT_REGISTRY", {})
    agent = builder.AgentBuilder.create_agent(
        name="Searcher",
        description="web research",
        custom_prompt="You search the web.",
        created_by=1,
    )
    agent.capabilities = [
        AgentCapability(name="search", description="web", tools=["web_search", "fetch_url"])
    ]
    register_agent(agent)

    cfg = await resolve_runtime_config(agent_id=agent.id, user_id=1)
    assert cfg.tool_names is not None
    assert "web_search" in cfg.tool_names
    assert "fetch_url" in cfg.tool_names
