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
from typing import Optional
from ..core.config import get_settings

settings = get_settings()

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

If query is complex (multiple topics), call multiple agents in parallel.
"""

    async def detect_intent_ai(self, message: str) -> list[str]:
        system_prompt = (
            "You are the router for Daffodil Intelligence. Analyze the user query and determine which of these agents "
            "are needed. Respond with a comma-separated list of the relevant agent keys, and nothing else.\n"
            "Keys:\n"
            "- academic: CGPA, results, courses, grades, attendance, syllabus\n"
            "- library: books, journals, PDF, borrowing\n"
            "- campus: shuttle, rooms, notices, facilities, building\n"
            "- career: jobs, CV, roadmap, internships, resumes, placements\n"
            "- coding: debugging, programming, errors, bug fixing\n"
            "- research: papers, thesis, citations, literature, publications\n"
            "- wellness: stress, mental health, study tips, motivation, relax\n"
            "- finance: fees, tuition, waivers, scholarships, cost, money\n"
            "- vision: image or screenshot analysis\n"
            "- voice: voice commands or audio\n"
            "- exam: exam schedules, seating, seat plan, midterm/final exams\n"
            "- hostel: hostel rooms, bedding, mess\n"
            "- transport: shuttle buses, transport routes, tracking\n"
            "- event: workshops, seminars, university events, clubs\n"
            "- complaint: grievances, issues, feedback, escalation\n"
            "- notification: subscription settings, alerts, announcement messages\n"
            "- fee: tuition fee, installments, payment status\n"
        )
        
        try:
            res = await self.generate_response(system_prompt, message)
            detected = [a.strip().lower() for a in res.split(",")]
            valid_agents = [a for a in detected if a in AGENT_MAP]
            if not valid_agents:
                return ["academic"]
            return valid_agents
        except Exception as e:
            logger.error(f"Error in detect_intent_ai: {e}")
            return detect_intent(message)

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        lang = detect_language(message)
        
        # Fast local handling for simple greetings to save LLM calls and avoid rate-limiting
        msg_clean = message.lower().strip().strip("?.!।")
        greetings_en = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        greetings_bn = ["হ্যালো", "হাই", "আসসালামু আলাইকুম", "নমস্কার", "শুভ সকাল", "শুভ দুপুর", "শুভ সন্ধ্যা"]
        
        if any(g in msg_clean for g in greetings_en + greetings_bn):
            # Check if any other agent keyword is present
            has_other_keywords = False
            for agent, words in KEYWORDS.items():
                if any(word in msg_clean for word in words):
                    has_other_keywords = True
                    break
            if not has_other_keywords:
                if lang == "bn":
                    return "হ্যালো! আমি ড্যাফোডিল ইন্টেলিজেন্স। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"
                return "Hello! I am Daffodil Intelligence. How can I assist you today?"

        agents = await self.detect_intent_ai(message)
        results = await process_with_agents(message, agents, context)
        response = await synthesize_response(results, message, lang)
        return response


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


KEYWORDS = {
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


def detect_intent(message: str) -> list[str]:
    message_lower = message.lower()
    agents = []

    for agent, words in KEYWORDS.items():
        if any(word in message_lower for word in words):
            agents.append(agent)

    # Don't blindly fallback to academic — return empty to trigger a general clarification
    return agents


async def process_with_agents(message: str, agents: list[str], context: dict = None) -> dict:
    lang = detect_language(message)
    msg_clean = message.lower().strip().strip("?.!।")
    greetings_en = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    greetings_bn = ["হ্যালো", "হাই", "আসসালামু আলাইকুম", "নমস্কার", "শুভ সকাল", "শুভ দুপুর", "শুভ সন্ধ্যা"]
    
    if any(g in msg_clean for g in greetings_en + greetings_bn):
        # Check if any other agent keyword is present
        has_other_keywords = False
        for agent, words in KEYWORDS.items():
            if any(word in msg_clean for word in words):
                has_other_keywords = True
                break
        if not has_other_keywords:
            if lang == "bn":
                return {"general": "হ্যালো! আমি ড্যাফোডিল ইন্টেলিজেন্স। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"}
            return {"general": "Hello! I am Daffodil Intelligence. How can I assist you today?"}

    # No agents matched — ask user to clarify
    if not agents:
        if lang == "bn":
            return {"general": "আমি আপনার প্রশ্নটি সম্পূর্ণভাবে বুঝতে পারিনি। অনুগ্রহ করে আরও নির্দিষ্টভাবে জিজ্ঞাসা করুন — যেমন সিজিপিএ, লাইব্রেরি, শাটল, বা ক্যারিয়ার সম্পর্কে।"}
        return {"general": "I'm not sure what you're asking. Could you be more specific? You can ask me about CGPA, library books, shuttle schedules, career opportunities, and more."}

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
            except RuntimeError as e:
                if str(e) == "RATE_LIMITED":
                    logger.warning(f"Agent {agent_type} rate-limited, skipping")
                    if lang == "bn":
                        results[agent_type] = "দুঃখিত, এআই সার্ভিসটি এই মুহূর্তে ব্যস্ত আছে। একটু পরে আবার চেষ্টা করুন।"
                    else:
                        results[agent_type] = "I'm sorry, the AI service is busy right now. Please try again in a moment."
                else:
                    logger.error(f"Agent {agent_type} failed: {e}")
                    results[agent_type] = f"Error: {str(e)}"
            except Exception as e:
                logger.error(f"Agent {agent_type} failed: {e}")
                results[agent_type] = f"Error: {str(e)}"

    return results


async def synthesize_response(results: dict, original_message: str, language: str = None) -> str:
    if not results:
        return "I'm not sure how to help with that. Can you be more specific?"

    if language is None:
        language = detect_language(original_message)

    # Process all result values to clean/replace error messages first
    processed_results = {}
    for agent_name, result in results.items():
        if isinstance(result, str):
            if result.startswith("Error"):
                if language == "bn":
                    processed_results[agent_name] = "দুঃখিত, বিশ্ববিদ্যালয়ের সার্ভিসটির সাথে সংযোগ করতে সমস্যা হচ্ছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
                else:
                    processed_results[agent_name] = "I'm sorry, I am having trouble connecting to the university service. Please try again in a moment."
            else:
                processed_results[agent_name] = result
        else:
            processed_results[agent_name] = result

    if len(processed_results) == 1:
        result_text = list(processed_results.values())[0]
        if isinstance(result_text, str):
            return format_voice_response(result_text, language)
        return result_text

    response_parts = []
    for agent_name, result in processed_results.items():
        if isinstance(result, str):
            response_parts.append(format_voice_response(result, language))

    # Avoid returning empty string if all results failed
    if not response_parts:
        if language == "bn":
            return "দুঃখিত, বিশ্ববিদ্যালয়ের সার্ভিসটির সাথে সংযোগ করতে সমস্যা হচ্ছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
        else:
            return "I'm sorry, I am having trouble connecting to the university service. Please try again in a moment."

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