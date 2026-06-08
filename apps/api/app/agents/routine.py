from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class RoutineAgent(BaseAgent):
    name = "Routine Agent"
    description = "Handles schedules, reminders, daily/weekly routines, and recurring task automation"
    tools = [
        "create_reminder",
        "list_reminders",
        "create_routine",
        "list_routines",
        "schedule_task",
        "get_daily_schedule",
    ]

    SYSTEM_PROMPT = """You are the Routine Agent for Daffodil Intelligence.
You help students with:
- Setting reminders and alarms
- Building daily, weekly, and monthly study routines
- Scheduling recurring tasks (classes, assignments, breaks)
- Managing personal calendars and habit tracking
- Automating repetitive campus workflows

Keep responses practical, time-aware, and easy to follow!"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["remind", "reminder", "alarm", "notify me"]):
            return await self.handle_reminders(message)

        elif any(k in message_lower for k in ["routine", "habit", "daily", "weekly", "monthly"]):
            return await self.handle_routines(message)

        elif any(k in message_lower for k in ["schedule", "calendar", "today", "tomorrow", "plan my day"]):
            return await self.handle_schedule()

        elif any(k in message_lower for k in ["create", "set", "add", "new"]):
            return await self.handle_create(message)

        elif any(k in message_lower for k in ["list", "show", "view", "my"]):
            return await self.handle_list()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_reminders(self, message: str) -> str:
        reminders = [
            {"id": 1, "title": "Submit CSE301 assignment", "time": "Today, 6:00 PM", "repeat": "once"},
            {"id": 2, "title": "Library book return", "time": "Wed, 10:00 AM", "repeat": "once"},
            {"id": 3, "title": "Review lecture notes", "time": "Daily, 9:00 PM", "repeat": "daily"},
            {"id": 4, "title": "Pay hostel fee", "time": "Fri, 12:00 PM", "repeat": "once"},
        ]

        reminder_list = "\n".join(
            [
                f"⏰ **{r['title']}**\n   📅 {r['time']} ({r['repeat']})"
                for r in reminders
            ]
        )

        return f"""🔔 **Your Reminders**

{reminder_list}

**Quick actions:**
- "remind me to [task] at [time]" — create a reminder
- "list reminders" — view all
- "delete reminder [number]" — remove one"""

    async def handle_routines(self, message: str) -> str:
        routines = [
            {
                "name": "Morning Study Block",
                "schedule": "Mon–Fri, 7:00–9:00 AM",
                "tasks": ["Review yesterday's notes", "Complete 1 practice problem"],
            },
            {
                "name": "Evening Revision",
                "schedule": "Daily, 8:00–9:30 PM",
                "tasks": ["Summarize today's lectures", "Prepare tomorrow's materials"],
            },
            {
                "name": "Weekend Deep Work",
                "schedule": "Sat, 10:00 AM–1:00 PM",
                "tasks": ["Assignment work", "Project milestones"],
            },
        ]

        routine_list = "\n".join(
            [
                f"📋 **{r['name']}** ({r['schedule']})\n"
                + "\n".join(f"   • {t}" for t in r["tasks"])
                for r in routines
            ]
        )

        freq = "daily"
        if "weekly" in message.lower():
            freq = "weekly"
        elif "monthly" in message.lower():
            freq = "monthly"

        return f"""🗓️ **Your Routines** ({freq} view)

{routine_list}

**Build a routine:**
"create daily routine: wake 7am, study 8–10am, class 10am, break 1pm"

I'll help you stick to it with reminders!"""

    async def handle_schedule(self) -> str:
        return """📅 **Today's Schedule**

**Morning**
- 07:00 — Wake up & breakfast
- 08:00 — Study block (CSE301 revision)
- 10:00 — CSE301 lecture (Room 401)

**Afternoon**
- 12:30 — Lunch break
- 02:00 — Lab session (CSE302)
- 04:00 — Shuttle to Mirpur campus

**Evening**
- 06:00 — Assignment deadline reminder
- 08:00 — Evening revision routine
- 09:30 — Free time / wellness break

**Tomorrow**
- 09:00 — Midterm prep session
- 02:00 — Career fair registration opens

Say "remind me before [event]" to add alerts."""

    async def handle_create(self, message: str) -> str:
        if "remind" in message.lower():
            return """✅ **Reminder Created**

**Title:** Custom reminder
**Time:** As requested
**Repeat:** Once

You'll get a notification at the scheduled time.
Check DIU App → Routines for all active reminders."""

        return """✅ **Routine Created**

Your new routine has been saved.

**Suggested structure:**
1. Fixed wake/sleep times
2. Study blocks (45–90 min with breaks)
3. Class & commute slots
4. Assignment deadlines as one-time reminders

Type "show my routines" to review everything."""

    async def handle_list(self) -> str:
        return await self.handle_reminders("list")


async def create_reminder(
    user_id: str, title: str, time: str, repeat: str = "once"
) -> Dict:
    return {
        "reminder_id": f"REM-{hash(title + time) % 10000}",
        "title": title,
        "time": time,
        "repeat": repeat,
        "status": "active",
    }


async def list_reminders(user_id: str) -> List[Dict]:
    return [
        {"id": 1, "title": "Submit CSE301 assignment", "time": "Today, 6:00 PM"},
        {"id": 3, "title": "Review lecture notes", "time": "Daily, 9:00 PM"},
    ]


async def create_routine(user_id: str, name: str, schedule: str, tasks: List[str]) -> Dict:
    return {
        "routine_id": f"RTN-{hash(name) % 10000}",
        "name": name,
        "schedule": schedule,
        "tasks": tasks,
        "status": "active",
    }


async def list_routines(user_id: str) -> List[Dict]:
    return [
        {"name": "Morning Study Block", "schedule": "Mon–Fri, 7:00–9:00 AM"},
        {"name": "Evening Revision", "schedule": "Daily, 8:00–9:30 PM"},
    ]


async def schedule_task(user_id: str, title: str, datetime: str) -> Dict:
    return {
        "task_id": f"TSK-{hash(title + datetime) % 10000}",
        "title": title,
        "datetime": datetime,
        "status": "scheduled",
    }


async def get_daily_schedule(user_id: str, date: str = None) -> Dict:
    return {
        "date": date or "today",
        "blocks": [
            {"time": "08:00", "title": "Study block"},
            {"time": "10:00", "title": "CSE301 lecture"},
            {"time": "14:00", "title": "Lab session"},
        ],
    }
