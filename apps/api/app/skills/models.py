"""Pydantic models for skills, rulesets, and agent configuration."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Skill(BaseModel):
    id: str
    name: str
    description: str
    content: str
    tool_names: List[str] = Field(default_factory=list)
    source: str = "manual"  # manual | copycat | hub
    recording_name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_by: int = 0
    is_public: bool = True
    usage_count: int = 0
    created_at: float = 0.0


class Ruleset(BaseModel):
    id: str
    name: str
    description: str
    rules: List[str] = Field(default_factory=list)
    created_by: int = 0
    is_public: bool = True
    created_at: float = 0.0


class GlobalAgentConfig(BaseModel):
    """Applied to every turn before per-agent overrides."""

    ruleset_ids: List[str] = Field(default_factory=list)
    skill_ids: List[str] = Field(default_factory=list)
    extra_system: str = ""
    default_agent_id: str = "main"


class AgentProfile(BaseModel):
    """Per-agent rules/skills overlay (builtin id or custom agent uuid)."""

    agent_id: str
    ruleset_ids: List[str] = Field(default_factory=list)
    skill_ids: List[str] = Field(default_factory=list)
    extra_system: str = ""
