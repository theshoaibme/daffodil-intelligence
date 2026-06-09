"""Hub persistence tests using in-memory mock store backend."""

import pytest

from app.skills.models import AgentProfile, GlobalAgentConfig
from app.skills.store import skill_store, ruleset_store, global_config_store, agent_profile_store, _memory


@pytest.fixture(autouse=True)
def reset_memory(monkeypatch):
    monkeypatch.setattr("app.core.database._use_mock", True)
    _memory.reset()
    yield


def test_skill_crud_and_acl():
    pub = skill_store.create("A", "desc", "content", created_by=1, is_public=True)
    priv = skill_store.create("B", "desc", "content", created_by=2, is_public=False)

    items = skill_store.list_all(user_id=1)
    assert len(items) == 1
    assert items[0].id == pub.id

    items_u2 = skill_store.list_all(user_id=2)
    assert len(items_u2) == 2

    public_items = skill_store.list_all(public_only=True)
    assert len(public_items) == 1

    updated = skill_store.update(pub.id, name="A2")
    assert updated.name == "A2"

    assert skill_store.delete(priv.id)
    assert skill_store.get(priv.id) is None


def test_junction_ordering_via_profile():
    s1 = skill_store.create("S1", "", "c1", is_public=True)
    s2 = skill_store.create("S2", "", "c2", is_public=True)
    agent_profile_store.upsert(AgentProfile(
        agent_id="coding",
        skill_ids=[s2.id, s1.id],
        ruleset_ids=[],
    ))
    profile = agent_profile_store.get("coding")
    assert profile.skill_ids == [s2.id, s1.id]


def test_global_config_links():
    sk = skill_store.create("G", "", "content", is_public=True)
    global_config_store.save(GlobalAgentConfig(skill_ids=[sk.id], default_agent_id="main"))
    cfg = global_config_store.get()
    assert cfg.skill_ids == [sk.id]
    assert cfg.default_agent_id == "main"


def test_ruleset_crud():
    rs = ruleset_store.create("R", "rules", ["be nice"], created_by=1, is_public=True)
    assert ruleset_store.get(rs.id) is not None
    assert ruleset_store.delete(rs.id)
