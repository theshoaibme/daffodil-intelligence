from .base import BaseAgent
from typing import Optional, Dict
from ..core.university_data import university_data


class CampusAgent(BaseAgent):
    name = "Campus Agent"
    description = "Handles shuttle schedules, room bookings, notices, events, and campus facilities"
    tools = ["get_shuttle_schedule", "get_shuttle_location", "book_room", "get_notices", "get_events"]

    SYSTEM_PROMPT = """You are the Campus Agent for DI.
You help with:
- Shuttle schedules and live locations
- Room/classroom bookings
- Campus notices and announcements
- Events and activities
- Campus facilities information"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["shuttle", "bus", "transport"]):
            return await self.handle_shuttle(message)

        elif any(k in message_lower for k in ["room", "booking", "reserve"]):
            return await self.handle_room(message)

        elif any(k in message_lower for k in ["notice", "notice", "announcement"]):
            return await self.handle_notices()

        elif any(k in message_lower for k in ["event", "activity"]):
            return await self.handle_events()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_shuttle(self, message: str) -> str:
        schedules = await get_shuttle_schedule()
        schedule_list = "\n".join([
            f"- **{s['route']}**: {s['time']} from {s['stop']} ({s['status']})"
            for s in schedules
        ])

        return f"""🚌 **Shuttle Schedule**

{schedule_list}

For live tracking, use: 'track shuttle [route]'"""

    async def handle_room(self, message: str) -> str:
        return """🏫 **Room Booking**

To book a room:
1. Go to the Admin Office
2. Submit a booking request with:
   - Room number needed
   - Date and time
   - Purpose

Or contact your department admin."""

    async def handle_notices(self) -> str:
        notices = await get_notices()
        notice_list = "\n".join([
            f"- **{n['title']}** ({n['priority'].upper()}) - {n['date']}"
            for n in notices
        ])

        return f"""📢 **Campus Notices**

{notice_list}"""

    async def handle_events(self) -> str:
        return """📅 **Upcoming Events**

No events scheduled at the moment.
Check the notice board or campus website for updates."""


async def get_shuttle_schedule(route: str = None) -> list[dict]:
    return await university_data.get_shuttle_schedule(route)


async def get_shuttle_location(route: str) -> dict:
    schedules = await university_data.get_shuttle_schedule(route)
    if schedules:
        return {"current_stop": schedules[0].get("stop", "Unknown"), "eta": "5 mins"}
    return {"error": "Route not found"}


async def get_notices() -> list[dict]:
    return [
        {"title": "Midterm Exam Schedule", "date": "2026-05-15", "priority": "high"},
        {"title": "Library Holiday Notice", "date": "2026-05-20", "priority": "medium"},
        {"title": "Career Fair 2026", "date": "2026-06-01", "priority": "low"},
    ]