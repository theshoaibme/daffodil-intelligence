from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from enum import Enum


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    ACADEMIC = "academic"
    LIBRARY = "library"
    CAMPUS = "career"
    CAREER = "career"
    CODING = "coding"
    RESEARCH = "research"
    FINANCE = "finance"
    WELLNESS = "wellness"
    VISION = "voice"
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
    tone: str  # friendly, formal, casual, technical
    expertise: List[str] = []
    response_style: str  # detailed, brief, structured


class DynamicAgent(BaseModel):
    id: str
    name: str
    description: str
    agent_type: AgentType
    personality: AgentPersonality
    capabilities: List[AgentCapability]
    system_prompt: str
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


def register_agent(agent: DynamicAgent):
    AGENT_REGISTRY[agent.id] = agent


def get_agent(agent_id: str) -> Optional[DynamicAgent]:
    return AGENT_REGISTRY.get(agent_id)


def list_agents(user_id: int = None) -> List[DynamicAgent]:
    if user_id:
        return [a for a in AGENT_REGISTRY.values() if a.created_by == user_id or a.is_public]
    return list(AGENT_REGISTRY.values())