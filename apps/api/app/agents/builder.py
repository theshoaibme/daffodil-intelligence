import asyncio
import logging
from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    ACADEMIC = "academic"
    LIBRARY = "library"
    CAMPUS = "campus"
    CAREER = "career"
    CODING = "coding"
    RESEARCH = "research"
    FINANCE = "finance"
    WELLNESS = "wellness"
    VISION = "vision"
    VOICE = "voice"
    AUTOMATION = "automation"
    CUSTOM = "custom"


class AgentCapability(BaseModel):
    name: str
    description: str
    enabled: bool = True
    tools: List[str] = []


class AgentPersonality(BaseModel):
    name: str
    tone: str
    expertise: List[str] = []
    response_style: str


class DynamicAgent(BaseModel):
    id: str
    name: str
    description: str
    agent_type: AgentType
    personality: AgentPersonality
    capabilities: List[AgentCapability]
    system_prompt: str
    ruleset_ids: List[str] = []
    skill_ids: List[str] = []
    is_public: bool = False
    created_by: int
    usage_count: int = 0
    rating: float = 0.0


class AgentBuilder:
    TEMPLATES = {
        "study_buddy": {
            "name": "Study Buddy",
            "tone": "friendly",
            "expertise": ["subject_explanations", "practice_problems", "motivation"],
            "capabilities": ["explain_concepts", "quiz_mode", "track_progress"]
        },
        "teaching_assistant": {
            "name": "Teaching Assistant",
            "tone": "formal",
            "expertise": ["course_content", "grading", "office_hours"],
            "capabilities": ["answer_questions", "review_work", "provide_feedback"]
        },
        "career_counselor": {
            "name": "Career Counselor",
            "tone": "supportive",
            "expertise": ["career_paths", "job_search", "interview_prep"],
            "capabilities": ["resume_review", "mock_interview", "roadmap"]
        },
        "research_advisor": {
            "name": "Research Advisor",
            "tone": "technical",
            "expertise": ["literature_review", "methodology", "writing"],
            "capabilities": ["paper_search", "citation_help", "thesis_review"]
        },
        "code_mentor": {
            "name": "Code Mentor",
            "tone": "technical",
            "expertise": ["programming", "debugging", "best_practices"],
            "capabilities": ["code_review", "explain_code", "generate_tests"]
        },
        "wellness_coach": {
            "name": "Wellness Coach",
            "tone": "supportive",
            "expertise": ["stress_management", "study_tips", "motivation"],
            "capabilities": ["check_in", "provide_resources", "goal_tracking"]
        }
    }

    @staticmethod
    def create_agent(
        name: str,
        description: str,
        template: str = None,
        custom_prompt: str = None,
        created_by: int = 1
    ) -> DynamicAgent:
        import uuid

        if template and template in AgentBuilder.TEMPLATES:
            t = AgentBuilder.TEMPLATES[template]
            personality = AgentPersonality(
                name=name,
                tone=t["tone"],
                expertise=t["expertise"],
                response_style="structured"
            )
            capabilities = [
                AgentCapability(name=c, description=c.replace("_", " ").title(), tools=[])
                for c in t["capabilities"]
            ]
            system_prompt = f"""You are {name}.
Tone: {t['tone']}
Expertise: {', '.join(t['expertise'])}

You help users with: {', '.join(t['capabilities'])}

Be helpful, accurate, and adapt to user needs."""
        else:
            personality = AgentPersonality(
                name=name,
                tone="friendly",
                expertise=["general_assistance"],
                response_style="structured"
            )
            capabilities = [
                AgentCapability(name="general", description="General assistance", tools=[])
            ]
            system_prompt = custom_prompt or f"""You are {name}.
{description}

Be helpful and accurate."""

        return DynamicAgent(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            agent_type=AgentType.CUSTOM,
            personality=personality,
            capabilities=capabilities,
            system_prompt=system_prompt,
            created_by=created_by
        )

    @staticmethod
    def get_templates() -> Dict[str, Dict]:
        return AgentBuilder.TEMPLATES


AGENT_REGISTRY: Dict[str, DynamicAgent] = {}


def _row_to_dynamic(row) -> DynamicAgent:
    try:
        agent_type = AgentType(row.agent_type)
    except ValueError:
        agent_type = AgentType.CUSTOM
    personality_data = row.personality or {
        "name": row.name,
        "tone": "friendly",
        "expertise": [],
        "response_style": "structured",
    }
    caps = []
    for c in row.capabilities or []:
        try:
            caps.append(AgentCapability(**c))
        except Exception:
            pass
    return DynamicAgent(
        id=str(row.id),
        name=row.name,
        description=row.description or "",
        agent_type=agent_type,
        personality=AgentPersonality(**personality_data),
        capabilities=caps or [AgentCapability(name="general", description="General assistance", tools=[])],
        system_prompt=row.system_prompt or "",
        is_public=bool(row.is_public),
        created_by=row.created_by or 0,
        usage_count=row.usage_count or 0,
        rating=row.rating or 0.0,
    )


def register_agent(agent: DynamicAgent):
    AGENT_REGISTRY[agent.id] = agent
    _persist_registry_async(agent)


def get_agent(agent_id: str) -> Optional[DynamicAgent]:
    return AGENT_REGISTRY.get(agent_id)


def list_agents(user_id: int = None) -> List[DynamicAgent]:
    if user_id:
        return [a for a in AGENT_REGISTRY.values() if a.created_by == user_id or a.is_public]
    return list(AGENT_REGISTRY.values())


def delete_agent(agent_id: str) -> bool:
    if agent_id not in AGENT_REGISTRY:
        return False
    del AGENT_REGISTRY[agent_id]
    _delete_registry_async(agent_id)
    return True


def _persist_registry_async(agent: DynamicAgent):
    try:
        from ..core.database import get_session_maker, is_mock_database
        from ..models.hub import CustomAgent

        if is_mock_database() or get_session_maker() is None:
            return

        async def _save():
            from ..skills.repository import HubRepository

            session_maker = get_session_maker()
            async with session_maker() as session:
                repo = HubRepository(session)
                existing = await repo.get_custom_agent(agent.id)
                row = CustomAgent(
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
                if existing:
                    await repo.update_custom_agent(
                        agent.id,
                        name=row.name,
                        description=row.description,
                        agent_type=row.agent_type,
                        personality=row.personality,
                        capabilities=row.capabilities,
                        system_prompt=row.system_prompt,
                        is_public=row.is_public,
                        usage_count=row.usage_count,
                        rating=row.rating,
                    )
                else:
                    await repo.create_custom_agent(row)

        asyncio.get_event_loop().create_task(_save()) if asyncio.get_event_loop().is_running() else asyncio.run(_save())
    except Exception as e:
        logger.warning(f"Could not persist custom agent to DB: {e}")


def _delete_registry_async(agent_id: str):
    try:
        from ..core.database import get_session_maker, is_mock_database

        if is_mock_database() or get_session_maker() is None:
            return

        async def _delete():
            from ..skills.repository import HubRepository

            session_maker = get_session_maker()
            async with session_maker() as session:
                repo = HubRepository(session)
                await repo.delete_custom_agent(agent_id)

        asyncio.get_event_loop().create_task(_delete()) if asyncio.get_event_loop().is_running() else asyncio.run(_delete())
    except Exception as e:
        logger.warning(f"Could not delete custom agent from DB: {e}")


async def load_registry_from_db():
    from ..core.database import get_session_maker, is_mock_database
    from ..skills.repository import HubRepository

    if is_mock_database() or get_session_maker() is None:
        return

    session_maker = get_session_maker()
    async with session_maker() as session:
        repo = HubRepository(session)
        rows, _ = await repo.list_custom_agents(limit=1000)
        for row in rows:
            AGENT_REGISTRY[str(row.id)] = _row_to_dynamic(row)
    logger.info(f"Loaded {len(AGENT_REGISTRY)} custom agents from PostgreSQL")
