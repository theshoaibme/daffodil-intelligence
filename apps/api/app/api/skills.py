"""Skill hub and ruleset API."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..skills.models import AgentProfile, GlobalAgentConfig
from ..skills.repository import HubRepository

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


def _is_admin(user: dict) -> bool:
    return user.get("role") == "admin"


def _can_modify_skill(user: dict, created_by: int) -> bool:
    user_id = int(user.get("sub"))
    return _is_admin(user) or created_by == user_id


@router.get("/hub")
async def skill_hub(
    tag: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    skills, total = await repo.list_skills(
        user_id=user_id, tag=tag, source=source, q=q, limit=limit, offset=offset
    )
    stats = await repo.skill_stats(user_id=user_id)
    return {
        **stats,
        "total": total,
        "limit": limit,
        "offset": offset,
        "skills": [_skill_dict(s) for s in skills],
    }


@router.get("/config/global")
async def get_global_config(db: AsyncSession = Depends(get_db)):
    repo = HubRepository(db)
    return (await repo.get_global_config()).model_dump()


@router.patch("/config/global")
async def patch_global_config(
    body: GlobalConfigUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    data = body.model_dump(exclude_unset=True)
    if "skill_ids" in data:
        missing = await repo.validate_skill_ids(data["skill_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")
    if "ruleset_ids" in data:
        missing = await repo.validate_ruleset_ids(data["ruleset_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown rulesets: {missing}")
    cfg = await repo.patch_global_config(**data)
    return cfg.model_dump()


@router.put("/config/global")
async def replace_global_config(
    body: GlobalConfigUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    existing = await repo.get_global_config()
    data = existing.model_dump()
    data.update(body.model_dump(exclude_unset=True))
    if data.get("skill_ids"):
        missing = await repo.validate_skill_ids(data["skill_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")
    if data.get("ruleset_ids"):
        missing = await repo.validate_ruleset_ids(data["ruleset_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown rulesets: {missing}")
    cfg = await repo.save_global_config(GlobalAgentConfig(**data))
    return cfg.model_dump()


@router.get("/config/agent/{agent_id}")
async def get_agent_profile(agent_id: str, db: AsyncSession = Depends(get_db)):
    repo = HubRepository(db)
    profile = await repo.get_agent_profile(agent_id)
    if not profile:
        return {"agent_id": agent_id, "ruleset_ids": [], "skill_ids": [], "extra_system": ""}
    return profile.model_dump()


@router.put("/config/agent/{agent_id}")
async def upsert_agent_profile(
    agent_id: str,
    body: AgentProfileUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    existing = await repo.get_agent_profile(agent_id) or AgentProfile(agent_id=agent_id)
    data = existing.model_dump()
    data.update(body.model_dump(exclude_unset=True))
    data["agent_id"] = agent_id
    if data.get("skill_ids"):
        missing = await repo.validate_skill_ids(data["skill_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")
    if data.get("ruleset_ids"):
        missing = await repo.validate_ruleset_ids(data["ruleset_ids"])
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown rulesets: {missing}")
    profile = await repo.upsert_agent_profile(AgentProfile(**data))
    return profile.model_dump()


@router.get("/rulesets/list")
async def list_rulesets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    items, total = await repo.list_rulesets(user_id=user_id, limit=limit, offset=offset)
    return {
        "rulesets": [_ruleset_dict(r) for r in items],
        "count": len(items),
        "total": total,
    }


@router.post("/rulesets")
async def create_ruleset(
    body: RulesetCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    rs = await repo.create_ruleset(
        name=body.name,
        description=body.description,
        rules=body.rules,
        created_by=user_id,
        is_public=body.is_public,
    )
    return _ruleset_dict(rs)


@router.patch("/rulesets/{ruleset_id}")
async def update_ruleset(
    ruleset_id: str,
    body: RulesetUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    rs = await repo.get_ruleset(ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    if not _can_modify_skill(user, rs.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")
    updated = await repo.update_ruleset(ruleset_id, **body.model_dump(exclude_unset=True))
    return _ruleset_dict(updated)


@router.delete("/rulesets/{ruleset_id}")
async def delete_ruleset(
    ruleset_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    rs = await repo.get_ruleset(ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    if not _can_modify_skill(user, rs.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")
    await repo.delete_ruleset(ruleset_id)
    return {"status": "deleted"}


@router.get("/")
async def list_skills(
    tag: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    skills, total = await repo.list_skills(
        user_id=user_id, tag=tag, source=source, q=q, limit=limit, offset=offset
    )
    return {
        "skills": [_skill_dict(s) for s in skills],
        "count": len(skills),
        "total": total,
    }


@router.post("/")
async def create_skill(
    body: SkillCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    skill = await repo.create_skill(
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
async def get_skill(
    skill_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    skill = await repo.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    user_id = int(user.get("sub"))
    if not skill.is_public and skill.created_by != user_id and not _is_admin(user):
        raise HTTPException(status_code=403, detail="Not allowed")
    return _skill_dict(skill)


@router.patch("/{skill_id}")
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    skill = await repo.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if not _can_modify_skill(user, skill.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")
    updated = await repo.update_skill(skill_id, **body.model_dump(exclude_unset=True))
    return _skill_dict(updated)


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    skill = await repo.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if not _can_modify_skill(user, skill.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")
    await repo.delete_skill(skill_id)
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
