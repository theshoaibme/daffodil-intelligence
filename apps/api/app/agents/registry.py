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
from .event import CampusEventsAgent
from .automation import AutomationAgent
from .complaint import ComplaintAgent
from .event_manager import EventAgent
from .fee_agent import FeeAgent
from .general import GeneralAgent
from .computer_use import ComputerUseAgent
from .copycat import CopyCatAgent
from .planning import PlanningAgent
from .routine import RoutineAgent
from .writing import WritingAgent
from .tasks import TasksAgent

AGENT_MAP = {
    "academic": AcademicAgent(),
    "library": LibraryAgent(),
    "campus": CampusAgent(),
    "career": CareerAgent(),
    "coding": CodingAgent(),
    "research": ResearchAgent(),
    "writing": WritingAgent(),
    "tasks": TasksAgent(),
    "wellness": WellnessAgent(),
    "finance": FinanceAgent(),
    "vision": VisionAgent(),
    "voice": VoiceAgent(),
    "exam": ExamAgent(),
    "hostel": HostelAgent(),
    "transport": TransportAgent(),
    "campus_events": CampusEventsAgent(),
    "complaint": ComplaintAgent(),
    "event": EventAgent(),
    "automation": AutomationAgent(),
    "fee": FeeAgent(),
    "general": GeneralAgent(),
    "computer_use": ComputerUseAgent(),
    "copycat": CopyCatAgent(),
    "planning": PlanningAgent(),
    "routine": RoutineAgent(),
}
