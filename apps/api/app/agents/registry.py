"""Central agent instance registry (avoids supervisor ↔ planning import cycles)."""

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
from .general import GeneralAgent
from .computer_use import ComputerUseAgent
from .copycat import CopyCatAgent
from .planning import PlanningAgent

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
    "general": GeneralAgent(),
    "computer_use": ComputerUseAgent(),
    "copycat": CopyCatAgent(),
    "planning": PlanningAgent(),
}
