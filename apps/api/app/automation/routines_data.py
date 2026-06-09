"""Class routine catalog (section → weekly schedule)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# time: "HH:MM" 24h, type: class | exam
ROUTINE_CATALOG: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "64_I": {
        "Monday": [
            {"time": "10:00", "course": "CSE321", "title": "Machine Learning", "room": "401", "teacher": "Prof. Rahman", "type": "class"},
            {"time": "14:00", "course": "CSE322", "title": "Computer Networks", "room": "205", "teacher": "Prof. Karim", "type": "class"},
        ],
        "Tuesday": [
            {"time": "09:00", "course": "CSE323", "title": "Software Engineering", "room": "102", "teacher": "Prof. Islam", "type": "class"},
            {"time": "11:00", "course": "CSE324", "title": "Database Systems", "room": "C-401", "teacher": "Prof. Ahmed", "type": "class"},
        ],
        "Wednesday": [
            {"time": "10:00", "course": "CSE321", "title": "Machine Learning Lab", "room": "Lab-3", "teacher": "Prof. Rahman", "type": "class"},
        ],
        "Thursday": [
            {"time": "13:00", "course": "CSE322", "title": "Networks Lab", "room": "Lab-2", "teacher": "Prof. Karim", "type": "class"},
        ],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    },
}


def get_section_routine(section: str, day: Optional[str] = None) -> Dict[str, Any]:
    key = section.strip().replace(" ", "_").upper()
    if key not in ROUTINE_CATALOG:
        key = "64_I"
    weekly = ROUTINE_CATALOG[key]
    if day:
        return {"section": key, "day": day, "items": weekly.get(day, [])}
    return {"section": key, "weekly": weekly}
