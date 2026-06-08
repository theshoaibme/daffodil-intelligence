"""Deprecated store — PostgreSQL repository with in-memory fallback for mock DB tests."""

from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from typing import Dict, List, Optional

from ..core.database import get_session_maker, is_mock_database
from .models import AgentProfile, GlobalAgentConfig, Ruleset, Skill
from .repository import HubRepository


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def _with_repo(fn):
    session_maker = get_session_maker()
    if session_maker is None:
        raise RuntimeError("Database unavailable")
    async with session_maker() as session:
        repo = HubRepository(session)
        return await fn(repo)


class _MemoryBackend:
    """In-memory persistence used when mock DB is active (tests)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._skills: Dict[str, Skill] = {}
        self._rulesets: Dict[str, Ruleset] = {}
        self._profiles: Dict[str, AgentProfile] = {}
        self._global = GlobalAgentConfig()

    def reset(self):
        with self._lock:
            self._skills = {}
            self._rulesets = {}
            self._profiles = {}
            self._global = GlobalAgentConfig()


_memory = _MemoryBackend()


class SkillStore:
    def get(self, skill_id: str) -> Optional[Skill]:
        if is_mock_database():
            return _memory._skills.get(skill_id)
        return _run(_with_repo(lambda repo: repo.get_skill(skill_id)))

    def list_all(
        self,
        user_id: Optional[int] = None,
        public_only: bool = False,
        limit: int = 100,
        offset: int = 0,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Skill]:
        if is_mock_database():
            items = list(_memory._skills.values())
            if public_only:
                items = [s for s in items if s.is_public]
            elif user_id is not None:
                items = [s for s in items if s.is_public or s.created_by == user_id]
            if tag:
                items = [s for s in items if tag in (s.tags or [])]
            if source:
                items = [s for s in items if s.source == source]
            if q:
                ql = q.lower()
                items = [
                    s for s in items
                    if ql in s.name.lower() or ql in s.description.lower()
                ]
            return items[offset : offset + limit]

        async def _list(repo):
            items, _ = await repo.list_skills(
                user_id=user_id,
                public_only=public_only,
                limit=limit,
                offset=offset,
                tag=tag,
                source=source,
                q=q,
            )
            return items

        return _run(_with_repo(_list))

    def create(self, name: str, description: str, content: str, **kwargs) -> Skill:
        if is_mock_database():
            skill = Skill(
                id=kwargs.get("skill_id") or str(uuid.uuid4()),
                name=name,
                description=description,
                content=content,
                tool_names=kwargs.get("tool_names") or [],
                source=kwargs.get("source", "manual"),
                recording_name=kwargs.get("recording_name"),
                tags=kwargs.get("tags") or [],
                created_by=kwargs.get("created_by", 0),
                is_public=kwargs.get("is_public", True),
                created_at=time.time(),
            )
            with _memory._lock:
                _memory._skills[skill.id] = skill
            return skill
        return _run(
            _with_repo(
                lambda repo: repo.create_skill(name, description, content, **kwargs)
            )
        )

    def update(self, skill_id: str, **fields) -> Optional[Skill]:
        if is_mock_database():
            with _memory._lock:
                skill = _memory._skills.get(skill_id)
                if not skill:
                    return None
                data = skill.model_dump()
                data.update({k: v for k, v in fields.items() if v is not None})
                updated = Skill(**data)
                _memory._skills[skill_id] = updated
                return updated
        return _run(_with_repo(lambda repo: repo.update_skill(skill_id, **fields)))

    def delete(self, skill_id: str) -> bool:
        if is_mock_database():
            with _memory._lock:
                if skill_id not in _memory._skills:
                    return False
                del _memory._skills[skill_id]
                return True
        return _run(_with_repo(lambda repo: repo.delete_skill(skill_id)))

    def increment_usage(self, skill_id: str):
        if is_mock_database():
            with _memory._lock:
                skill = _memory._skills.get(skill_id)
                if skill:
                    skill.usage_count += 1
            return
        _run(_with_repo(lambda repo: repo.increment_skill_usage(skill_id)))


class RulesetStore:
    def get(self, ruleset_id: str) -> Optional[Ruleset]:
        if is_mock_database():
            return _memory._rulesets.get(ruleset_id)
        return _run(_with_repo(lambda repo: repo.get_ruleset(ruleset_id)))

    def list_all(self, user_id: Optional[int] = None) -> List[Ruleset]:
        if is_mock_database():
            items = list(_memory._rulesets.values())
            if user_id is not None:
                items = [r for r in items if r.is_public or r.created_by == user_id]
            return items

        async def _list(repo):
            items, _ = await repo.list_rulesets(user_id=user_id, limit=1000)
            return items

        return _run(_with_repo(_list))

    def create(self, name: str, description: str, rules: List[str], **kwargs) -> Ruleset:
        if is_mock_database():
            rs = Ruleset(
                id=kwargs.get("ruleset_id") or str(uuid.uuid4()),
                name=name,
                description=description,
                rules=rules,
                created_by=kwargs.get("created_by", 0),
                is_public=kwargs.get("is_public", True),
                created_at=time.time(),
            )
            with _memory._lock:
                _memory._rulesets[rs.id] = rs
            return rs
        return _run(
            _with_repo(
                lambda repo: repo.create_ruleset(name, description, rules, **kwargs)
            )
        )

    def update(self, ruleset_id: str, **fields) -> Optional[Ruleset]:
        if is_mock_database():
            with _memory._lock:
                rs = _memory._rulesets.get(ruleset_id)
                if not rs:
                    return None
                data = rs.model_dump()
                data.update({k: v for k, v in fields.items() if v is not None})
                updated = Ruleset(**data)
                _memory._rulesets[ruleset_id] = updated
                return updated
        return _run(_with_repo(lambda repo: repo.update_ruleset(ruleset_id, **fields)))

    def delete(self, ruleset_id: str) -> bool:
        if is_mock_database():
            with _memory._lock:
                if ruleset_id not in _memory._rulesets:
                    return False
                del _memory._rulesets[ruleset_id]
                return True
        return _run(_with_repo(lambda repo: repo.delete_ruleset(ruleset_id)))


class GlobalConfigStore:
    def get(self) -> GlobalAgentConfig:
        if is_mock_database():
            return _memory._global
        return _run(_with_repo(lambda repo: repo.get_global_config()))

    def save(self, config: GlobalAgentConfig) -> GlobalAgentConfig:
        if is_mock_database():
            with _memory._lock:
                _memory._global = config
            return config
        return _run(_with_repo(lambda repo: repo.save_global_config(config)))

    def patch(self, **fields) -> GlobalAgentConfig:
        if is_mock_database():
            cfg = self.get()
            data = cfg.model_dump()
            data.update({k: v for k, v in fields.items() if v is not None})
            return self.save(GlobalAgentConfig(**data))
        return _run(_with_repo(lambda repo: repo.patch_global_config(**fields)))


class AgentProfileStore:
    def get(self, agent_id: str) -> Optional[AgentProfile]:
        if is_mock_database():
            return _memory._profiles.get(agent_id)
        return _run(_with_repo(lambda repo: repo.get_agent_profile(agent_id)))

    def upsert(self, profile: AgentProfile) -> AgentProfile:
        if is_mock_database():
            with _memory._lock:
                _memory._profiles[profile.agent_id] = profile
            return profile
        return _run(_with_repo(lambda repo: repo.upsert_agent_profile(profile)))

    def list_all(self) -> List[AgentProfile]:
        if is_mock_database():
            return list(_memory._profiles.values())
        return []


skill_store = SkillStore()
ruleset_store = RulesetStore()
global_config_store = GlobalConfigStore()
agent_profile_store = AgentProfileStore()
