from .base import BaseAgent
from .academic import AcademicAgent
from .library import LibraryAgent
from .campus import CampusAgent
from .career import CareerAgent
from .coding import CodingAgent
from .research import ResearchAgent
from .wellness import WellnessAgent
from .finance import FinanceAgent
from .vision import VisionAgent
from .voice import VoiceAgent
from .exam import ExamAgent
from .hostel import HostelAgent
from .transport import TransportAgent
from .event import EventAgent
from .complaint import ComplaintAgent
from .notification import NotificationAgent
from .fee_agent import FeeAgent
import logging
import re

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    name = "Supervisor Agent"
    description = "The main orchestrator that routes requests to appropriate agents"

    SYSTEM_PROMPT = """You are the Supervisor of DAFFODIL INTELLIGENCE.
Your job is to:
1. Understand the user's intent
2. Route to correct agents
3. Coordinate multiple agents if needed
4. Merge responses into one coherent answer

Available agents (18 total):
- academic: CGPA, results, courses, grades
- library: books, journals, PDF
- campus: shuttle, rooms, notices, facilities
- career: jobs, CV, roadmap, internships
- coding: debugging, code generation, programming
- research: papers, thesis, citations
- wellness: stress, mental health, study tips
- finance: fees, payments, waivers, scholarships
- vision: image/PDF analysis
- voice: speech conversion, voice chat
- exam: exam schedules, attendance, results
- hostel: room booking, complaints, facilities
- transport: shuttle tracking, routes, vehicle booking
- events: workshops, clubs, seminars
- complaint: grievances, feedback, escalations
- notification: alerts, announcements, preferences
- fee: tuition, installments, payment status

If query is complex (multiple topics), call multiple agents in parallel."""


AGENT_MAP = {
    "academic": AcademicAgent(),
    "library": LibraryAgent(),
    "campus": CampusAgent(),
    "career": CareerAgent(),
    "coding": CodingAgent(),
    "research": ResearchAgent(),
    "wellness": WellnessAgent(),
    "finance": FinanceAgent(),
    "vision": VisionAgent(),
    "voice": VoiceAgent(),
    "exam": ExamAgent(),
    "hostel": HostelAgent(),
    "transport": TransportAgent(),
    "event": EventAgent(),
    "complaint": ComplaintAgent(),
    "notification": NotificationAgent(),
    "fee": FeeAgent(),
}


def detect_intent(message: str) -> list[str]:
    message_lower = message.lower()
    agents = []

    keywords = {
        "academic": ["cgpa", "gpa", "grade", "result", "course", "syllabus", "semester", "attendance", "marks"],
        "library": ["book", "journal", "pdf", "borrow", "library", "research paper", "isbn"],
        "campus": ["shuttle", "room", "notice", "campus", "building", "facility"],
        "career": ["job", "internship", "cv", "resume", "interview", "career", "roadmap", "placement"],
        "coding": ["code", "debug", "programming", "algorithm", "error", "bug", "develop", "function"],
        "research": ["thesis", "paper", "research", "citation", "literature", "abstract", "publication"],
        "wellness": ["stress", "mental", "study tips", "motivation", "relax", "anxiety", "health"],
        "finance": ["fee", "payment", "waiver", "scholarship", "tuition", "money", "cost"],
        "vision": ["image", "screenshot", "photo", "pdf", "analyze", "read"],
        "voice": ["speak", "voice", "speech", "audio", "talk", "voice chat"],
        "exam": ["exam", "exam schedule", "seating", "seat plan", "midterm", "final exam"],
        "hostel": ["hostel", "hostel room", "bed", "mess", "check in", "check out", "ac room"],
        "transport": ["shuttle", "bus", "transport", "route", "track shuttle", "vehicle", "van"],
        "event": ["event", "workshop", "seminar", "club", "activity", "register event"],
        "complaint": ["complaint", "complain", "issue", "problem", "feedback", "escalate", "grievance"],
        "notification": ["notification", "notifications", "alert", "announcement", "message", "subscribe"],
        "fee": ["tuition fee", "installment", "due", "pay fee", "emi", "semester fee"],
    }

    for agent, words in keywords.items():
        if any(word in message_lower for word in words):
            agents.append(agent)

    if not agents:
        agents = ["academic"]

    return agents


async def process_with_agents(message: str, agents: list[str], context: dict = None) -> dict:
    results = {}
    tools_used = []

    for agent_type in agents:
        if agent_type in AGENT_MAP:
            try:
                agent = AGENT_MAP[agent_type]
                response = await agent.process(message, context)
                results[agent_type] = response
                tools_used.extend(agent.tools)
                logger.info(f"Agent {agent_type} processed successfully")
            except Exception as e:
                logger.error(f"Agent {agent_type} failed: {e}")
                results[agent_type] = f"Error: {str(e)}"

    return results


async def synthesize_response(results: dict, original_message: str) -> str:
    if not results:
        return "I'm not sure how to help with that. Can you be more specific?"

    if len(results) == 1:
        return list(results.values())[0]

    response_parts = []
    for agent_name, result in results.items():
        if isinstance(result, str) and not result.startswith("Error"):
            response_parts.append(f"**{agent_name.title()}**: {result}")

    return "\n\n".join(response_parts) if response_parts else "Here are the results from multiple agents:"