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

BN_CHARS_PATTERN = re.compile(r'[\u0980-\u09FF]')

def detect_language(text: str) -> str:
    bn_chars = BN_CHARS_PATTERN.findall(text)
    bn_ratio = len(bn_chars) / len(text) if text else 0
    if bn_ratio > 0.3:
        return "bn"
    return "en"

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


async def synthesize_response(results: dict, original_message: str, language: str = None) -> str:
    if not results:
        return "I'm not sure how to help with that. Can you be more specific?"

    if language is None:
        language = detect_language(original_message)

    if len(results) == 1:
        result_text = list(results.values())[0]
        if isinstance(result_text, str):
            return format_voice_response(result_text, language)
        return result_text

    response_parts = []
    for agent_name, result in results.items():
        if isinstance(result, str) and not result.startswith("Error"):
            response_parts.append(format_voice_response(result, language))

    return "। ".join(response_parts) if language == "bn" else "\n\n".join(response_parts)


def format_voice_response(text: str, language: str = "en") -> str:
    if not text:
        return text
    
    text = text.strip()
    
    text = text.replace("**", "")
    text = text.replace("*", "")
    
    if language == "bn":
        replacements = {
            "Hello": "হ্যালো",
            "Hi": "হাই",
            "Hey": "হ্যালো",
            "Thank you": "ধন্যবাদ",
            "Thanks": "ধন্যবাদ",
            "Yes": "হ্যাঁ",
            "No": "না",
            "Sorry": "দুঃখিত",
            "Error": "ত্রুটি",
            "Success": "সফল",
            "Result": "ফলাফল",
            "Available": "উপলব্ধ",
            "Not found": "পাওয়া যায়নি",
            "CGPA": "সিজিপিএ",
            "GPA": "জিপিএ",
            "PDF": "পিডিএফ",
            "API": "এপিআই",
            "URL": "ইউআরএল",
            "ID": "আইডি",
            "OK": "ঠিক আছে",
            "Sure": "অবশ্যই",
        }
        
        for en_word, bn_word in replacements.items():
            text = text.replace(en_word, bn_word)
        
        if not text.endswith("।") and not text.endswith("?") and not text.endswith("!"):
            if "?" in text:
                pass
            else:
                text = text + "।"
    
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    
    return text