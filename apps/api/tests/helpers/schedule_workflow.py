"""Dynamic workflow case builders for Telegram schedule automation tests.

No hardcoded routines or JSON fixtures — scenarios are generated at runtime from
user workflow requirements (offsets, evening summary hour, class density) plus a
reproducible seed.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence

WEEKDAYS: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

_DEPARTMENTS = ("CSE", "EEE", "BBA", "ENG", "PHR")
_COURSE_PREFIXES = ("CSE", "MAT", "PHY", "ENG", "ECO", "BUS")
_TEACHER_TITLES = ("Dr.", "Prof.", "Ms.", "Mr.")
_TEACHER_NAMES = ("Ahmed", "Karim", "Sultana", "Hossain", "Rahman", "Chowdhury")


@dataclass(frozen=True)
class ClassSlot:
    time: str
    course: str
    title: str = ""
    room: str = ""
    teacher: str = ""
    type: str = "class"

    def to_routine_item(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "course": self.course,
            "title": self.title,
            "room": self.room,
            "teacher": self.teacher,
            "type": self.type,
        }


@dataclass(frozen=True)
class WorkflowRequirements:
    """User-specified automation workflow — drives scenario generation."""

    reminder_offsets_min: Sequence[int] = (30, 10)
    evening_summary_hour: int = 22
    min_classes_per_active_day: int = 1
    max_classes_per_active_day: int = 2
    active_day_count: int = 5
    dense_week: bool = False

    @classmethod
    def from_user_spec(
        cls,
        *,
        offsets: Sequence[int] | None = None,
        evening_hour: int | None = None,
        dense_week: bool = False,
    ) -> WorkflowRequirements:
        return cls(
            reminder_offsets_min=tuple(sorted(set(offsets or (30, 10)), reverse=True)),
            evening_summary_hour=evening_hour if evening_hour is not None else 22,
            dense_week=dense_week,
            active_day_count=7 if dense_week else 5,
            max_classes_per_active_day=3 if dense_week else 2,
        )


@dataclass
class WorkflowScenario:
    case_id: str
    section: str
    department: str
    prompt: str
    requirements: WorkflowRequirements
    weekly: Dict[str, List[ClassSlot]]
    user_id: int
    telegram_chat_id: int
    seed: int

    @property
    def reminder_offsets_min(self) -> Sequence[int]:
        return self.requirements.reminder_offsets_min

    @property
    def evening_summary_hour(self) -> int:
        return self.requirements.evening_summary_hour

    def weekly_items(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            day: [slot.to_routine_item() for slot in slots]
            for day, slots in self.weekly.items()
        }

    def class_count(self) -> int:
        return sum(len(slots) for slots in self.weekly.values())

    def expected_reminder_count(self) -> int:
        return self.class_count() * len(self.reminder_offsets_min)

    def first_class_on(self, day: str) -> ClassSlot | None:
        slots = self.weekly.get(day) or []
        return slots[0] if slots else None

    def first_nonempty_day(self) -> str:
        for day in WEEKDAYS:
            if self.weekly.get(day):
                return day
        raise ValueError("scenario has no classes")


def _format_offsets_phrase(offsets: Sequence[int]) -> str:
    parts = [f"{o} minute{'s' if o != 1 else ''}" for o in sorted(offsets, reverse=True)]
    if len(parts) == 1:
        return parts[0]
    return " and ".join(parts)


def build_workflow_prompt(requirements: WorkflowRequirements) -> str:
    """Natural-language prompt derived from requirements — not a static template string."""
    offsets = _format_offsets_phrase(requirements.reminder_offsets_min)
    return (
        "Set up daily Telegram notifications without hardcoding: "
        f"send a summary of tomorrow's schedule the previous night at "
        f"{requirements.evening_summary_hour}:00, and reminder messages "
        f"{offsets} before each class with full course name, room number, time, "
        "and teacher information if available."
    )


def parse_offsets_from_prompt(prompt: str) -> tuple[int, ...]:
    """Extract minute offsets from a user workflow prompt."""
    found = {int(m) for m in re.findall(r"(\d+)\s*minutes?", prompt.lower())}
    return tuple(sorted(found, reverse=True))


def parse_evening_hour_from_prompt(prompt: str) -> int | None:
    match = re.search(r"previous night at (\d{1,2}):00", prompt.lower())
    return int(match.group(1)) if match else None


def _generate_section(rng: random.Random) -> str:
    return f"{rng.randint(10, 99)}_{rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"


def _generate_class_slot(rng: random.Random, *, seq: int) -> ClassSlot:
    hour = rng.randint(8, 16)
    minute = rng.choice((0, 30))
    prefix = rng.choice(_COURSE_PREFIXES)
    course = f"{prefix}{rng.randint(100, 499)}"
    title = f"{prefix} Topic {seq}"
    room = str(rng.randint(101, 599))
    teacher = f"{rng.choice(_TEACHER_TITLES)} {rng.choice(_TEACHER_NAMES)}"
    return ClassSlot(
        time=f"{hour:02d}:{minute:02d}",
        course=course,
        title=title,
        room=room,
        teacher=teacher,
    )


def generate_weekly_schedule(
    rng: random.Random,
    requirements: WorkflowRequirements,
) -> Dict[str, List[ClassSlot]]:
    weekly: Dict[str, List[ClassSlot]] = {day: [] for day in WEEKDAYS}
    active_days = rng.sample(WEEKDAYS, k=min(requirements.active_day_count, len(WEEKDAYS)))
    seq = 0
    for day in active_days:
        count = rng.randint(
            requirements.min_classes_per_active_day,
            requirements.max_classes_per_active_day,
        )
        slots = []
        used_times: set[str] = set()
        for _ in range(count):
            seq += 1
            slot = _generate_class_slot(rng, seq=seq)
            while slot.time in used_times:
                slot = _generate_class_slot(rng, seq=seq)
            used_times.add(slot.time)
            slots.append(slot)
        weekly[day] = sorted(slots, key=lambda s: s.time)
    return weekly


def generate_workflow_scenario(
    *,
    seed: int,
    requirements: WorkflowRequirements | None = None,
) -> WorkflowScenario:
    """Build a fully dynamic scenario from requirements + seed."""
    rng = random.Random(seed)
    req = requirements or WorkflowRequirements.from_user_spec()
    section = _generate_section(rng)
    department = rng.choice(_DEPARTMENTS)
    weekly = generate_weekly_schedule(rng, req)
    prompt = build_workflow_prompt(req)
    return WorkflowScenario(
        case_id=f"seed{seed}-{'dense' if req.dense_week else 'std'}-"
        f"h{req.evening_summary_hour}-o{'-'.join(map(str, req.reminder_offsets_min))}",
        section=section,
        department=department,
        prompt=prompt,
        requirements=req,
        weekly=weekly,
        user_id=50_000 + (seed % 10_000),
        telegram_chat_id=900_000 + (seed % 100_000),
        seed=seed,
    )


def requirement_profiles() -> List[tuple[str, WorkflowRequirements]]:
    """Requirement profiles only — no embedded schedule data."""
    return [
        (
            "dual_offset_standard",
            WorkflowRequirements.from_user_spec(offsets=(30, 10), evening_hour=22),
        ),
        (
            "single_offset",
            WorkflowRequirements.from_user_spec(offsets=(15,), evening_hour=21),
        ),
        (
            "dense_week",
            WorkflowRequirements.from_user_spec(
                offsets=(30, 10), evening_hour=23, dense_week=True
            ),
        ),
    ]


def generate_scenario_matrix() -> List[WorkflowScenario]:
    """One dynamic scenario per requirement profile, unique seed per profile."""
    return [
        generate_workflow_scenario(seed=10_000 + idx, requirements=req)
        for idx, (_name, req) in enumerate(requirement_profiles())
    ]


def parse_hm(value: str) -> tuple[int, int]:
    hour, minute = value.strip().split(":")
    return int(hour), int(minute)


def class_start_on(day_name: str, slot: ClassSlot, *, ref: datetime) -> datetime:
    target_idx = WEEKDAYS.index(day_name)
    ref_idx = ref.weekday()
    delta_days = target_idx - ref_idx
    base = ref.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=delta_days)
    hour, minute = parse_hm(slot.time)
    return base.replace(hour=hour, minute=minute)


def build_reminder_plan(
    weekly: Dict[str, List[ClassSlot]],
    *,
    offsets_min: Sequence[int],
    ref: datetime,
) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    for day_name, slots in weekly.items():
        for slot in slots:
            start = class_start_on(day_name, slot, ref=ref)
            for offset in offsets_min:
                fire_at = start - timedelta(minutes=offset)
                body = (
                    f"Class in {offset} min\n"
                    f"{slot.course} — {slot.title}\n"
                    f"Time: {slot.time}\n"
                    f"Room: {slot.room or 'TBA'}\n"
                    f"Teacher: {slot.teacher or 'TBA'}"
                )
                plan.append(
                    {
                        "day": day_name,
                        "offset_min": offset,
                        "fire_at": fire_at,
                        "class_time": slot.time,
                        "course": slot.course,
                        "body": body,
                        "slot": slot,
                    }
                )
    return sorted(plan, key=lambda r: r["fire_at"])


def message_has_class_details(text: str, slot: ClassSlot) -> bool:
    required = [slot.course, slot.time]
    optional_present = any(
        part and part in text for part in (slot.title, slot.room, slot.teacher)
    )
    return all(part in text for part in required) and optional_present


def persist_routine_upload(scenario: WorkflowScenario) -> None:
    """Write generated routine to the upload store (no static JSON files)."""
    from app.automation.routine_resolver import save_routine_upload

    save_routine_upload(
        department=scenario.department,
        section=scenario.section,
        filename=f"{scenario.section}.json",
        content=__import__("json").dumps(
            {"section": scenario.section, "weekly": scenario.weekly_items()}
        ).encode(),
    )
