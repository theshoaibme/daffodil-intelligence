from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class EventAgent(BaseAgent):
    name = "Event Agent"
    description = "Handles campus events, workshops, seminars, clubs, and activities"
    tools = ["get_events", "register_event", "create_event", "get_calendar", "join_club"]

    SYSTEM_PROMPT = """You are the Event Agent for Daffodil Intelligence.
You help students with:
- Campus events and workshops
- Club activities and registrations
- Seminars and guest lectures
- Sports tournaments
- Cultural programs
- Event calendar

Share event details with excitement and encourage participation!"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["event", "workshop", "seminar", "program"]):
            return await self.handle_events()

        elif any(k in message_lower for k in ["register", "join", "participate", "attend"]):
            return await self.handle_register(message)

        elif any(k in message_lower for k in ["club", "team", "society"]):
            return await self.handle_clubs()

        elif any(k in message_lower for k in ["calendar", "schedule", "upcoming"]):
            return await self.handle_calendar()

        elif any(k in message_lower for k in ["create", "organize", "host"]):
            return await self.handle_create()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_events(self) -> str:
        events = [
            {"title": "AI & Machine Learning Workshop", "date": "2026-05-15", "time": "2:00 PM", "venue": "Lab 301", "type": "Workshop"},
            {"title": "Guest Lecture: Tech Industry Trends", "date": "2026-05-18", "time": "11:00 AM", "venue": "Auditorium", "type": "Seminar"},
            {"title": "Programming Contest", "date": "2026-05-20", "time": "9:00 AM", "venue": "Lab Building", "type": "Competition"},
            {"title": "Cultural Night", "date": "2026-05-25", "time": "6:00 PM", "venue": "Open Air Theater", "type": "Cultural"},
            {"title": "Sports Day", "date": "2026-05-30", "time": "8:00 AM", "venue": "Sports Complex", "type": "Sports"},
        ]

        event_list = "\n".join([
            f"- **{e['title']}**\n  📅 {e['date']} at {e['time']}\n  📍 {e['venue']} | 🏷️ {e['type']}"
            for e in events
        ])

        return f"""🎉 **Upcoming Events**

{event_list}

💡 Type "register [event name]" to sign up!"""

    async def handle_register(self, message: str) -> str:
        return """✅ **Event Registration**

**To register for an event:**

1. **Online**: Visit events portal
2. **App**: DIU Events App
3. **Offline**: Student Center

**Required:**
- Student ID
- Valid email
- Department approval (for some events)

📝 Registration is free!
🎁 Limited freebies for early registrants!"""

    async def handle_clubs(self) -> str:
        clubs = [
            {"name": "Programming Club", "members": 150, "active": True},
            {"name": "Robotics Club", "members": 80, "active": True},
            {"name": "Photography Club", "members": 120, "active": True},
            {"name": "Cultural Club", "members": 200, "active": True},
            {"name": "Sports Club", "members": 300, "active": True},
            {"name": "Debate Club", "members": 50, "active": True},
        ]

        club_list = "\n".join([
            f"- **{c['name']}**: {c['members']} members"
            for c in clubs
        ])

        return f"""🏆 **Student Clubs**

{club_list}

**Benefits of Joining:**
- 🎯 Skill development
- 🤝 Network building
- 🏆 Competition opportunities
- 🎉 Social events

📝 Type "join [club name]" to apply!"""

    async def handle_calendar(self) -> str:
        return """📅 **Event Calendar - May 2026**

| Date | Event | Type |
|------|-------|------|
| May 15 | AI Workshop | Workshop |
| May 16 | Career Fair | Fair |
| May 18 | Guest Lecture | Seminar |
| May 20 | Programming Contest | Competition |
| May 22 | Tech Talk | Seminar |
| May 25 | Cultural Night | Cultural |
| May 30 | Sports Day | Sports |

🔴 *Highlighted events are mandatory*

Check the app for daily updates!"""

    async def handle_create(self) -> str:
        return """📝 **Create an Event**

**To organize an event:**

1. **Fill the form** at Student Affairs
2. **Submit proposal** with:
   - Event name & description
   - Date & time
   - Venue requirement
   - Budget estimate
   - Expected participants

3. **Approval**: 3-5 working days

**Guidelines:**
- Follow university policies
- No political/religious events
- Safety first
- Clear venue after event

📞 Contact: studentaffairs@diu.edu.bd"""


async def get_events(category: str = None, limit: int = 10) -> List[Dict]:
    return [
        {"title": "AI Workshop", "date": "2026-05-15", "venue": "Lab 301"},
        {"title": "Career Fair", "date": "2026-05-16", "venue": "Auditorium"},
        {"title": "Programming Contest", "date": "2026-05-20", "venue": "Lab Building"},
    ]


async def register_event(event_id: str, student_id: str) -> Dict:
    return {
        "registration_id": f"REG-{event_id}-{student_id}",
        "status": "confirmed",
        "message": "See you at the event!"
    }


async def create_event(event_data: Dict) -> Dict:
    return {
        "event_id": f"EVENT-{hash(event_data.get('title', '')) % 10000}",
        "status": "pending_approval"
    }


async def get_calendar(month: str = None) -> List[Dict]:
    return [
        {"date": "2026-05-15", "event": "AI Workshop", "type": "Workshop"},
        {"date": "2026-05-16", "event": "Career Fair", "type": "Fair"},
    ]


async def join_club(club_name: str, student_id: str) -> Dict:
    return {
        "application_id": f"CLUB-{hash(club_name) % 1000}",
        "status": "submitted",
        "message": "Application submitted. We'll contact you soon!"
    }