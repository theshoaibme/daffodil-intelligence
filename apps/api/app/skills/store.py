"""JSON-backed persistence for skills, rulesets, and agent configuration."""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .models import AgentProfile, GlobalAgentConfig, Ruleset, Skill

_DATA_DIR = Path("data")
_DATA_DIR.mkdir(exist_ok=True)


class _JsonStore:
    def __init__(self, filename: str):
        self._path = _DATA_DIR / filename
        self._lock = threading.Lock()
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True


class SkillStore(_JsonStore):
    def __init__(self):
        super().__init__("skills.json")
        self._skills: Dict[str, Skill] = {}
        self._data_loaded = False

    def _load(self):
        if self._data_loaded:
            return
        self._data_loaded = True
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._skills = {k: Skill(**v) for k, v in raw.items()}
            except Exception:
                self._skills = {}

    def _save(self):
        self._path.write_text(
            json.dumps({k: v.model_dump() for k, v in self._skills.items()}, indent=2),
            "utf-8",
        )

    def get(self, skill_id: str) -> Optional[Skill]:
        with self._lock:
            self._load()
            return self._skills.get(skill_id)

    def list_all(self, user_id: Optional[int] = None, public_only: bool = False) -> List[Skill]:
        with self._lock:
            self._load()
            items = list(self._skills.values())
        if public_only:
            return [s for s in items if s.is_public]
        if user_id is not None:
            return [s for s in items if s.is_public or s.created_by == user_id]
        return items

    def create(
        self,
        name: str,
        description: str,
        content: str,
        *,
        tool_names: Optional[List[str]] = None,
        source: str = "manual",
        recording_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: int = 0,
        is_public: bool = True,
    ) -> Skill:
        skill = Skill(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            content=content,
            tool_names=tool_names or [],
            source=source,
            recording_name=recording_name,
            tags=tags or [],
            created_by=created_by,
            is_public=is_public,
            created_at=time.time(),
        )
        with self._lock:
            self._load()
            self._skills[skill.id] = skill
            self._save()
        return skill

    def update(self, skill_id: str, **fields) -> Optional[Skill]:
        with self._lock:
            self._load()
            skill = self._skills.get(skill_id)
            if not skill:
                return None
            data = skill.model_dump()
            data.update({k: v for k, v in fields.items() if v is not None})
            updated = Skill(**data)
            self._skills[skill_id] = updated
            self._save()
            return updated

    def delete(self, skill_id: str) -> bool:
        with self._lock:
            self._load()
            if skill_id not in self._skills:
                return False
            del self._skills[skill_id]
            self._save()
            return True

    def increment_usage(self, skill_id: str):
        with self._lock:
            self._load()
            skill = self._skills.get(skill_id)
            if skill:
                skill.usage_count += 1
                self._save()


class RulesetStore(_JsonStore):
    def __init__(self):
        super().__init__("rulesets.json")
        self._rulesets: Dict[str, Ruleset] = {}
        self._data_loaded = False

    def _load(self):
        if self._data_loaded:
            return
        self._data_loaded = True
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._rulesets = {k: Ruleset(**v) for k, v in raw.items()}
            except Exception:
                self._rulesets = {}

    def _save(self):
        self._path.write_text(
            json.dumps({k: v.model_dump() for k, v in self._rulesets.items()}, indent=2),
            "utf-8",
        )

    def get(self, ruleset_id: str) -> Optional[Ruleset]:
        with self._lock:
            self._load()
            return self._rulesets.get(ruleset_id)

    def list_all(self, user_id: Optional[int] = None) -> List[Ruleset]:
        with self._lock:
            self._load()
            items = list(self._rulesets.values())
        if user_id is not None:
            return [r for r in items if r.is_public or r.created_by == user_id]
        return items

    def create(
        self,
        name: str,
        description: str,
        rules: List[str],
        *,
        created_by: int = 0,
        is_public: bool = True,
    ) -> Ruleset:
        rs = Ruleset(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            rules=rules,
            created_by=created_by,
            is_public=is_public,
            created_at=time.time(),
        )
        with self._lock:
            self._load()
            self._rulesets[rs.id] = rs
            self._save()
        return rs

    def update(self, ruleset_id: str, **fields) -> Optional[Ruleset]:
        with self._lock:
            self._load()
            rs = self._rulesets.get(ruleset_id)
            if not rs:
                return None
            data = rs.model_dump()
            data.update({k: v for k, v in fields.items() if v is not None})
            updated = Ruleset(**data)
            self._rulesets[ruleset_id] = updated
            self._save()
            return updated

    def delete(self, ruleset_id: str) -> bool:
        with self._lock:
            self._load()
            if ruleset_id not in self._rulesets:
                return False
            del self._rulesets[ruleset_id]
            self._save()
            return True


class GlobalConfigStore(_JsonStore):
    def __init__(self):
        super().__init__("global_agent_config.json")
        self._config: Optional[GlobalAgentConfig] = None

    def get(self) -> GlobalAgentConfig:
        with self._lock:
            self._ensure_loaded()
            if self._config is not None:
                return self._config
            if self._path.exists():
                try:
                    self._config = GlobalAgentConfig(**json.loads(self._path.read_text("utf-8")))
                except Exception:
                    self._config = GlobalAgentConfig()
            else:
                self._config = GlobalAgentConfig()
            return self._config

    def save(self, config: GlobalAgentConfig) -> GlobalAgentConfig:
        with self._lock:
            self._config = config
            self._path.write_text(config.model_dump_json(indent=2), "utf-8")
            return config

    def patch(self, **fields) -> GlobalAgentConfig:
        cfg = self.get()
        data = cfg.model_dump()
        data.update({k: v for k, v in fields.items() if v is not None})
        return self.save(GlobalAgentConfig(**data))


class AgentProfileStore(_JsonStore):
    def __init__(self):
        super().__init__("agent_profiles.json")
        self._profiles: Dict[str, AgentProfile] = {}
        self._data_loaded = False

    def _load(self):
        if self._data_loaded:
            return
        self._data_loaded = True
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._profiles = {k: AgentProfile(**v) for k, v in raw.items()}
            except Exception:
                self._profiles = {}

    def _save(self):
        self._path.write_text(
            json.dumps({k: v.model_dump() for k, v in self._profiles.items()}, indent=2),
            "utf-8",
        )

    def get(self, agent_id: str) -> Optional[AgentProfile]:
        with self._lock:
            self._load()
            return self._profiles.get(agent_id)

    def upsert(self, profile: AgentProfile) -> AgentProfile:
        with self._lock:
            self._load()
            self._profiles[profile.agent_id] = profile
            self._save()
            return profile

    def list_all(self) -> List[AgentProfile]:
        with self._lock:
            self._load()
            return list(self._profiles.values())


skill_store = SkillStore()
ruleset_store = RulesetStore()
global_config_store = GlobalConfigStore()
agent_profile_store = AgentProfileStore()
