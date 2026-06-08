"""Skill hub and ruleset API."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.security import get_current_user
from ..skills.store import skill_store, ruleset_store, global_config_store, agent_profile_store
from ..skills.models import AgentProfile

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillCreate(BaseModel):
    name: str
    description: str
    content: str
    tool_names: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tool_names: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class RulesetCreate(BaseModel):
    name: str
    description: str
    rules: List[str]
    is_public: bool = False


class RulesetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[str]] = None
    is_public: Optional[bool] = None


class GlobalConfigUpdate(BaseModel):
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None
    extra_system: Optional[str] = None
    default_agent_id: Optional[str] = None


class AgentProfileUpdate(BaseModel):
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None
    extra_system: Optional[str] = None


@router.get("/hub")
async def skill_hub(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    skills = skill_store.list_all(user_id=user_id)
    return {
        "count": len(skills),
        "public_count": sum(1 for s in skills if s.is_public),
        "copycat_count": sum(1 for s in skills if s.source == "copycat"),
        "skills": [_skill_dict(s) for s in skills],
    }


@router.get("/config/global")
async def get_global_config():
    return global_config_store.get().model_dump()


@router.patch("/config/global")
async def patch_global_config(body: GlobalConfigUpdate, user: dict = Depends(get_current_user)):
    return global_config_store.patch(**body.model_dump(exclude_unset=True)).model_dump()


@router.get("/config/agent/{agent_id}")
async def get_agent_profile(agent_id: str):
    profile = agent_profile_store.get(agent_id)
    if not profile:
        return {"agent_id": agent_id, "ruleset_ids": [], "skill_ids": [], "extra_system": ""}
    return profile.model_dump()


@router.put("/config/agent/{agent_id}")
async def upsert_agent_profile(agent_id: str, body: AgentProfileUpdate, user: dict = Depends(get_current_user)):
    existing = agent_profile_store.get(agent_id) or AgentProfile(agent_id=agent_id)
    data = existing.model_dump()
    data.update(body.model_dump(exclude_unset=True))
    data["agent_id"] = agent_id
    return agent_profile_store.upsert(AgentProfile(**data)).model_dump()


@router.get("/rulesets/list")
async def list_rulesets(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    items = ruleset_store.list_all(user_id=user_id)
    return {"rulesets": [_ruleset_dict(r) for r in items], "count": len(items)}


@router.post("/rulesets")
async def create_ruleset(body: RulesetCreate, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    rs = ruleset_store.create(
        name=body.name,
        description=body.description,
        rules=body.rules,
        created_by=user_id,
        is_public=body.is_public,
    )
    return _ruleset_dict(rs)


@router.patch("/rulesets/{ruleset_id}")
async def update_ruleset(ruleset_id: str, body: RulesetUpdate, user: dict = Depends(get_current_user)):
    rs = ruleset_store.get(ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    user_id = int(user.get("sub"))
    if rs.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    updated = ruleset_store.update(ruleset_id, **body.model_dump(exclude_unset=True))
    return _ruleset_dict(updated)


@router.delete("/rulesets/{ruleset_id}")
async def delete_ruleset(ruleset_id: str, user: dict = Depends(get_current_user)):
    rs = ruleset_store.get(ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    user_id = int(user.get("sub"))
    if rs.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    ruleset_store.delete(ruleset_id)
    return {"status": "deleted"}


@router.get("/")
async def list_skills(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    skills = skill_store.list_all(user_id=user_id)
    return {"skills": [_skill_dict(s) for s in skills], "count": len(skills)}


@router.post("/")
async def create_skill(body: SkillCreate, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    skill = skill_store.create(
        name=body.name,
        description=body.description,
        content=body.content,
        tool_names=body.tool_names,
        tags=body.tags,
        created_by=user_id,
        is_public=body.is_public,
        source="manual",
    )
    return _skill_dict(skill)


@router.get("/{skill_id}")
async def get_skill(skill_id: str, user: dict = Depends(get_current_user)):
    skill = skill_store.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    user_id = int(user.get("sub"))
    if not skill.is_public and skill.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return _skill_dict(skill)


@router.patch("/{skill_id}")
async def update_skill(skill_id: str, body: SkillUpdate, user: dict = Depends(get_current_user)):
    skill = skill_store.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    user_id = int(user.get("sub"))
    if skill.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    updated = skill_store.update(skill_id, **body.model_dump(exclude_unset=True))
    return _skill_dict(updated)


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str, user: dict = Depends(get_current_user)):
    skill = skill_store.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    user_id = int(user.get("sub"))
    if skill.created_by != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    skill_store.delete(skill_id)
    return {"status": "deleted"}


def _skill_dict(skill) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "content": skill.content,
        "tool_names": skill.tool_names,
        "source": skill.source,
        "recording_name": skill.recording_name,
        "tags": skill.tags,
        "is_public": skill.is_public,
        "usage_count": skill.usage_count,
        "created_at": skill.created_at,
    }


def _ruleset_dict(rs) -> dict:
    return {
        "id": rs.id,
        "name": rs.name,
        "description": rs.description,
        "rules": rs.rules,
        "is_public": rs.is_public,
        "created_at": rs.created_at,
    }
