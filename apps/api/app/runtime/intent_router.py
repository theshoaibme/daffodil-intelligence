"""Root-agent intent routing — which specialist agents and tools to use."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

_SECTION_CODE = re.compile(r"\b(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\b", re.I)
_SECTION_ONLY = re.compile(r"^\s*(\d{2}_[A-Za-z0-9]+|6[Cc]\d+)\s*\.?!?\s*$", re.I)

# Order matters: first match wins for primary agent when scores tie.
AGENT_KEYWORDS: dict[str, Tuple[str, ...]] = {
    "routine": (
        "class routine",
        "class schedule",
        "my routine",
        "section routine",
        "tomorrow class",
        "today class",
        "remind",
        "reminder",
        "alarm",
        "routine",
        "daily",
        "weekly",
        "habit",
        "schedule my day",
    ),
    "academic": (
        "cgpa",
        "gpa",
        "grade",
        "result",
        "course",
        "syllabus",
        "semester",
        "attendance",
        "marks",
        "transcript",
    ),
    "exam": (
        "exam",
        "exam schedule",
        "seating",
        "seat plan",
        "midterm",
        "final exam",
    ),
    "library": (
        "book",
        "journal",
        "pdf",
        "borrow",
        "library",
        "isbn",
    ),
    "campus": (
        "notice",
        "campus",
        "building",
        "facility",
        "room booking",
    ),
    "transport": (
        "shuttle",
        "bus",
        "transport",
        "route",
        "track shuttle",
        "vehicle",
    ),
    "career": (
        "job",
        "internship",
        "cv",
        "resume",
        "interview",
        "career",
        "placement",
    ),
    "coding": (
        "code",
        "debug",
        "programming",
        "algorithm",
        "error",
        "bug",
        "function",
    ),
    "research": (
        "thesis",
        "paper",
        "research",
        "citation",
        "publication",
    ),
    "finance": (
        "fee",
        "payment",
        "waiver",
        "scholarship",
        "tuition",
        "installment",
    ),
    "wellness": (
        "stress",
        "mental",
        "anxiety",
        "motivation",
        "study tips",
    ),
    "hostel": (
        "hostel",
        "mess",
        "dorm",
    ),
    "event": (
        "event",
        "workshop",
        "seminar",
        "club",
    ),
    "complaint": (
        "complaint",
        "grievance",
        "feedback",
        "escalate",
    ),
    "notification": (
        "notification",
        "alert",
        "announcement",
        "subscribe",
    ),
    "vision": (
        "image",
        "screenshot",
        "photo",
        "analyze image",
    ),
    "planning": (
        "plan",
        "step by step",
        "workflow",
        "multiple steps",
    ),
    "computer_use": (
        "click",
        "mouse",
        "keyboard",
        "screen",
        "open app",
        "automate",
    ),
}

AGENT_TOOLS: dict[str, List[str]] = {
    "routine": [
        "get_class_routine",
        "read_pdf",
        "read_routine_pdf",
        "read_department_routine_pdf",
        "recall_notes",
        "store_note",
        "enable_routine_automation",
        "create_reminder",
        "list_reminders",
        "delete_reminder",
        "create_routine",
        "list_routines",
        "get_daily_schedule",
        "schedule_task",
        "create_automation_hook",
        "list_automation_hooks",
    ],
    "academic": ["get_cgpa", "get_courses", "get_results", "get_attendance"],
    "exam": ["get_exam_schedule"],
    "library": ["search_books", "get_book_availability", "read_pdf"],
    "transport": ["get_shuttle_schedule"],
    "career": ["search_jobs", "get_internships"],
}


@dataclass
class RoutePlan:
    agents: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    primary: str = "general"
    section: Optional[str] = None

    def hint_block(self) -> str:
        if self.primary == "general" and not self.tools:
            return ""
        tools = ", ".join(f"`{t}`" for t in self.tools[:6]) if self.tools else "none"
        agents = ", ".join(self.agents) if self.agents else "general"
        lines = [
            "## Routing (this turn)",
            f"- Primary agent: **{self.primary}**",
            f"- Also consider: {agents}",
            f"- Prefer tools: {tools}",
        ]
        if self.section:
            lines.append(f"- Section detected: `{self.section}` — call get_class_routine(section=\"{self.section}\")")
        elif self.primary == "routine":
            lines.append(
                "- If section is missing, ask once for the user's section code. "
                "When user gives a section code, call get_class_routine immediately."
            )
        lines.append("- Do NOT greet again; continue the conversation.")
        return "\n".join(lines)


def _score_agents(message_lower: str) -> List[Tuple[str, int]]:
    scores: List[Tuple[str, int]] = []
    for agent, words in AGENT_KEYWORDS.items():
        hits = sum(1 for w in words if w in message_lower)
        if hits:
            scores.append((agent, hits))
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores


def route_message(message: str) -> RoutePlan:
    """Decide which agents/tools the root agent should use for this user message."""
    text = (message or "").strip()
    lower = text.lower()

    plan = RoutePlan()

    sec_only = _SECTION_ONLY.match(text)
    if sec_only:
        plan.section = sec_only.group(1).upper()
        plan.agents = ["routine"]
        plan.primary = "routine"
        plan.tools = ["get_class_routine"]
        return plan

    sec_match = _SECTION_CODE.search(text)
    if sec_match:
        plan.section = sec_match.group(1).upper()

    scores = _score_agents(lower)
    if scores:
        plan.primary = scores[0][0]
        plan.agents = [a for a, _ in scores[:3]]
    else:
        plan.agents = ["general"]
        plan.primary = "general"

    tool_set: List[str] = []
    for agent in plan.agents:
        for tool in AGENT_TOOLS.get(agent, []):
            if tool not in tool_set:
                tool_set.append(tool)
    if plan.section and "get_class_routine" not in tool_set:
        tool_set.insert(0, "get_class_routine")
    plan.tools = tool_set
    return plan


def detect_intent(message: str) -> List[str]:
    """Keyword router used by legacy supervisor fallback."""
    plan = route_message(message)
    if plan.primary == "general" and plan.agents == ["general"]:
        return ["general"]
    return plan.agents or ["general"]
