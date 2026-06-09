"""Unified Agent Hub API — built-in registry + PostgreSQL custom agents."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.builder import AgentBuilder, AgentCapability, AgentType, DynamicAgent
from ..agents.registry import AGENT_MAP
from ..core.database import get_db, is_mock_database
from ..core.security import get_current_user
from ..models import hub as hub_models
from ..skills.models import AgentProfile
from ..skills.repository import HubRepository
from ..api.status import _AGENT_CATEGORIES

router = APIRouter(prefix="/agents/hub", tags=["Agent Hub"])


_HUB_CATEGORIES = frozenset(
    {"orchestration", "computer", "productivity", "university", "ai", "general"}
)


class CapabilityInput(BaseModel):
    name: str
    description: str = ""
    tools: List[str] = Field(default_factory=list)
    enabled: bool = True


class CreateHubAgentRequest(BaseModel):
    name: str
    description: str
    category: str = "general"
    template: Optional[str] = None
    custom_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[List[CapabilityInput]] = None
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None
    is_public: bool = False


class UpdateHubAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_public: Optional[bool] = None
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None
    extra_system: Optional[str] = None


class RateRequest(BaseModel):
    rating: float = Field(ge=1, le=5)


def _is_admin(user: dict) -> bool:
    return user.get("role") == "admin"


def _can_modify_agent(user: dict, created_by: Optional[int]) -> bool:
    user_id = int(user.get("sub"))
    return _is_admin(user) or created_by == user_id


def _builtin_entry(agent_id: str, agent) -> dict:
    skill_count = 0
    return {
        "id": agent_id,
        "name": agent.name,
        "description": agent.description,
        "kind": "builtin",
        "category": _AGENT_CATEGORIES.get(agent_id, "general"),
        "tools": agent.tools,
        "tool_count": len(agent.tools or []),
        "skill_count": skill_count,
        "status": "active",
        "is_public": True,
        "usage_count": 0,
        "rating": 0.0,
    }


async def _custom_entry(repo: HubRepository, row: hub_models.CustomAgent) -> dict:
    skill_count = await repo.count_agent_skills(str(row.id))
    return {
        "id": str(row.id),
        "name": row.name,
        "description": row.description,
        "kind": "custom",
        "category": row.agent_type or "custom",
        "tools": [],
        "tool_count": 0,
        "skill_count": skill_count,
        "status": "active",
        "is_public": bool(row.is_public),
        "usage_count": row.usage_count or 0,
        "rating": row.rating or 0.0,
        "created_by": row.created_by,
    }


def _dynamic_to_row(agent: DynamicAgent) -> hub_models.CustomAgent:
    return hub_models.CustomAgent(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type.value,
        personality=agent.personality.model_dump(),
        capabilities=[c.model_dump() for c in agent.capabilities],
        system_prompt=agent.system_prompt,
        created_by=agent.created_by,
        is_public=agent.is_public,
        usage_count=agent.usage_count,
        rating=agent.rating,
    )


@router.get("")
async def list_hub_agents(
    kind: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))
    agents: List[dict] = []

    if kind in (None, "builtin"):
        for aid, agent in sorted(AGENT_MAP.items()):
            entry = _builtin_entry(aid, agent)
            if category and entry["category"] != category:
                continue
            if q:
                ql = q.lower()
                if ql not in entry["name"].lower() and ql not in (entry["description"] or "").lower():
                    continue
            agents.append(entry)

    if kind in (None, "custom"):
        if is_mock_database():
            from ..agents.builder import list_agents as list_custom_memory

            for agent in list_custom_memory(user_id):
                entry = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "kind": "custom",
                    "category": agent.agent_type.value,
                    "tools": [],
                    "tool_count": 0,
                    "skill_count": len(agent.skill_ids or []),
                    "status": "active",
                    "is_public": agent.is_public,
                    "usage_count": agent.usage_count,
                    "rating": agent.rating,
                    "created_by": agent.created_by,
                }
                if category and entry["category"] != category:
                    continue
                if q:
                    ql = q.lower()
                    if ql not in entry["name"].lower() and ql not in (entry["description"] or "").lower():
                        continue
                agents.append(entry)
        else:
            rows, _ = await repo.list_custom_agents(user_id=user_id, limit=limit, offset=offset)
            for row in rows:
                entry = await _custom_entry(repo, row)
                if category and entry["category"] != category:
                    continue
                if q:
                    ql = q.lower()
                    if ql not in entry["name"].lower() and ql not in (entry["description"] or "").lower():
                        continue
                agents.append(entry)

    return {"agents": agents, "count": len(agents)}


@router.get("/{agent_id}")
async def get_hub_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    if agent_id in AGENT_MAP:
        agent = AGENT_MAP[agent_id]
        profile = await repo.get_agent_profile(agent_id)
        return {
            **_builtin_entry(agent_id, agent),
            "profile": profile.model_dump() if profile else {"agent_id": agent_id, "skill_ids": [], "ruleset_ids": [], "extra_system": ""},
        }

    row = await repo.get_custom_agent(agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    user_id = int(user.get("sub"))
    if not row.is_public and row.created_by != user_id and not _is_admin(user):
        raise HTTPException(status_code=403, detail="Not allowed")

    profile = await repo.get_agent_profile(agent_id)
    return {
        **await _custom_entry(repo, row),
        "system_prompt": row.system_prompt,
        "personality": row.personality,
        "capabilities": row.capabilities,
        "profile": profile.model_dump() if profile else {"agent_id": agent_id, "skill_ids": [], "ruleset_ids": [], "extra_system": ""},
    }


@router.post("")
async def create_hub_agent(
    body: CreateHubAgentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = HubRepository(db)
    user_id = int(user.get("sub"))

    prompt = (body.system_prompt or body.custom_prompt or "").strip() or None
    agent = AgentBuilder.create_agent(
        name=body.name,
        description=body.description,
        template=body.template,
        custom_prompt=prompt,
        created_by=user_id,
    )
    if prompt:
        agent.system_prompt = prompt
    if body.capabilities:
        agent.capabilities = [
            AgentCapability(
                name=c.name,
                description=c.description or c.name.replace("_", " ").title(),
                enabled=c.enabled,
                tools=c.tools or [],
            )
            for c in body.capabilities
        ]
    agent.is_public = body.is_public
    category = (body.category or "general").strip().lower()
    if category not in _HUB_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {body.category}")
    if body.ruleset_ids:
        missing = await repo.validate_ruleset_ids(body.ruleset_ids)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown rulesets: {missing}")
    if body.skill_ids:
        missing = await repo.validate_skill_ids(body.skill_ids)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")

    row = _dynamic_to_row(agent)
    row.agent_type = category
    row = await repo.create_custom_agent(row)
    await repo.upsert_agent_profile(AgentProfile(
        agent_id=str(row.id),
        ruleset_ids=body.ruleset_ids or [],
        skill_ids=body.skill_ids or [],
    ))

    return await _custom_entry(repo, row)


@router.patch("/{agent_id}")
async def update_hub_agent(
    agent_id: str,
    body: UpdateHubAgentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if agent_id in AGENT_MAP:
        raise HTTPException(status_code=400, detail="Built-in agents cannot be modified")

    repo = HubRepository(db)
    row = await repo.get_custom_agent(agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not _can_modify_agent(user, row.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")

    fields = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.description is not None:
        fields["description"] = body.description
    if body.system_prompt is not None:
        fields["system_prompt"] = body.system_prompt
    if body.is_public is not None:
        fields["is_public"] = body.is_public
    if fields:
        await repo.update_custom_agent(agent_id, **fields)

    profile = await repo.get_agent_profile(agent_id) or AgentProfile(agent_id=agent_id)
    if body.extra_system is not None:
        profile.extra_system = body.extra_system
    if body.ruleset_ids is not None:
        missing = await repo.validate_ruleset_ids(body.ruleset_ids)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown rulesets: {missing}")
        profile.ruleset_ids = body.ruleset_ids
    if body.skill_ids is not None:
        missing = await repo.validate_skill_ids(body.skill_ids)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")
        profile.skill_ids = body.skill_ids
    await repo.upsert_agent_profile(profile)

    row = await repo.get_custom_agent(agent_id)
    return await _custom_entry(repo, row)


@router.delete("/{agent_id}")
async def delete_hub_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if agent_id in AGENT_MAP:
        raise HTTPException(status_code=400, detail="Built-in agents cannot be deleted")

    repo = HubRepository(db)
    row = await repo.get_custom_agent(agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not _can_modify_agent(user, row.created_by):
        raise HTTPException(status_code=403, detail="Not allowed")

    await repo.delete_custom_agent(agent_id)
    return {"status": "deleted"}


@router.post("/{agent_id}/use")
async def use_hub_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    if agent_id in AGENT_MAP:
        return {"status": "ok", "usage_count": 0, "kind": "builtin"}

    repo = HubRepository(db)
    count = await repo.increment_agent_usage(agent_id)
    if count is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "ok", "usage_count": count, "kind": "custom"}


@router.post("/{agent_id}/rate")
async def rate_hub_agent(
    agent_id: str,
    body: RateRequest,
    db: AsyncSession = Depends(get_db),
):
    if agent_id in AGENT_MAP:
        raise HTTPException(status_code=400, detail="Built-in agents cannot be rated")

    repo = HubRepository(db)
    rating = await repo.rate_agent(agent_id, body.rating)
    if rating is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"rating": rating}
