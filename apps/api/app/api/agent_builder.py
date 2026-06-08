from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..core.security import get_current_user
from ..agents.builder import AgentBuilder, DynamicAgent, register_agent, get_agent, list_agents, delete_agent
from ..skills.store import agent_profile_store
from ..skills.models import AgentProfile

router = APIRouter(prefix="/agents", tags=["Agent Builder"])


class CreateAgentRequest(BaseModel):
    name: str
    description: str
    template: Optional[str] = None
    custom_prompt: Optional[str] = None
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_public: Optional[bool] = None
    ruleset_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    agent_type: str
    personality: dict
    capabilities: List[dict]
    is_public: bool
    usage_count: int
    rating: float


@router.get("/templates")
async def get_templates():
    return {"templates": AgentBuilder.get_templates()}


@router.post("/create", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))

    agent = AgentBuilder.create_agent(
        name=request.name,
        description=request.description,
        template=request.template,
        custom_prompt=request.custom_prompt,
        created_by=user_id
    )

    if request.ruleset_ids:
        agent.ruleset_ids = request.ruleset_ids
    if request.skill_ids:
        agent.skill_ids = request.skill_ids
    register_agent(agent)
    agent_profile_store.upsert(AgentProfile(
        agent_id=agent.id,
        ruleset_ids=agent.ruleset_ids,
        skill_ids=agent.skill_ids,
    ))

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type.value,
        personality=agent.personality.model_dump(),
        capabilities=[c.model_dump() for c in agent.capabilities],
        is_public=agent.is_public,
        usage_count=agent.usage_count,
        rating=agent.rating
    )


@router.get("/custom/list")
async def list_user_agents(user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    agents = list_agents(user_id)
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "agent_type": a.agent_type.value,
                "is_public": a.is_public,
                "usage_count": a.usage_count
            }
            for a in agents
        ]
    }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_details(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type.value,
        personality=agent.personality.model_dump(),
        capabilities=[c.model_dump() for c in agent.capabilities],
        is_public=agent.is_public,
        usage_count=agent.usage_count,
        rating=agent.rating
    )


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    user: dict = Depends(get_current_user)
):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if request.name:
        agent.name = request.name
    if request.description:
        agent.description = request.description
    if request.system_prompt:
        agent.system_prompt = request.system_prompt
    if request.is_public is not None:
        agent.is_public = request.is_public
    if request.ruleset_ids is not None:
        agent.ruleset_ids = request.ruleset_ids
    if request.skill_ids is not None:
        agent.skill_ids = request.skill_ids
    register_agent(agent)
    agent_profile_store.upsert(AgentProfile(
        agent_id=agent.id,
        ruleset_ids=agent.ruleset_ids,
        skill_ids=agent.skill_ids,
    ))

    return {"status": "updated", "agent_id": agent_id}


@router.delete("/{agent_id}")
async def remove_agent(agent_id: str, user: dict = Depends(get_current_user)):
    if not delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "deleted"}


@router.post("/{agent_id}/use")
async def use_agent(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.usage_count += 1
    return {"status": "ok", "usage_count": agent.usage_count}


@router.post("/{agent_id}/rate")
async def rate_agent(agent_id: str, rating: float):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    agent.rating = (agent.rating * agent.usage_count + rating) / (agent.usage_count + 1)
    return {"rating": round(agent.rating, 2)}