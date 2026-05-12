from .base import BaseAgent
from typing import Optional, Dict, List
from ..core.university_data import university_data
import logging

logger = logging.getLogger(__name__)


class TransportAgent(BaseAgent):
    name = "Transport Agent"
    description = "Handles shuttle schedules, routes, live tracking, and vehicle booking"
    tools = ["get_shuttle_schedule", "track_shuttle", "book_vehicle", "get_routes", "report_issue"]

    SYSTEM_PROMPT = """You are the Transport Agent for DI (Daffodil Intelligence).
You help students with:
- Shuttle schedules and routes
- Live shuttle tracking
- Vehicle booking for trips
- Transport complaints
- Bus stop information
- Estimated arrival times

Be accurate with times and routes. Use tools for live data."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["shuttle", "bus", "schedule"]):
            return await self.handle_schedule()

        elif any(k in message_lower for k in ["track", "live", "where", "location"]):
            return await self.handle_track(message)

        elif any(k in message_lower for k in ["book", "reserve", "van", "car"]):
            return await self.handle_booking(message)

        elif any(k in message_lower for k in ["route", "stop", "path"]):
            return await self.handle_routes()

        elif any(k in message_lower for k in ["complaint", "issue", "problem"]):
            return await self.handle_complaint()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_schedule(self) -> str:
        schedules = await university_data.get_shuttle_schedule()

        schedule_list = "\n".join([
            f"- **{s['route']}**: {s['time']} from {s['stop']}\n  Status: {s['status']}"
            for s in schedules
        ])

        return f"""🚌 **Shuttle Schedule**

{schedule_list}

📱 Track live: "Track shuttle [route name]"
⏰ Operating Hours: 6 AM - 10 PM"""

    async def handle_track(self, message: str) -> str:
        import re
        route_match = re.search(r'(mirpur|uttara|dhanmondi|gulshan|baz|cantonment)', message.lower())
        route = route_match.group(1) if route_match else "mirpur"

        return f"""📍 **Live Tracking: {route.title()} Route**

Current Location: **Near {route.title()} Bridge**
ETA to Campus: **12 minutes**
Passengers: **8/30**

🚌 Next shuttle: 15 minutes away

Note: Live tracking updates every 30 seconds."""

    async def handle_booking(self, message: str) -> str:
        return """🚗 **Vehicle Booking**

**Available Vehicles:**

1. **University Van** (Group)
   - Capacity: 14 passengers
   - Route: Pre-defined
   - Cost: 50 BDT/person

2. **Car/SUV** (Private)
   - Capacity: 4 passengers
   - Destination: Anywhere in Dhaka
   - Cost: 500-1500 BDT (depends on distance)

3. **Microbus** (Group)
   - Capacity: 8 passengers
   - Cost: 100 BDT/person

📞 Booking: 017xxxxxxxx
📱 WhatsApp: Available"""

    async def handle_routes(self) -> str:
        return """🗺️ **Transport Routes**

**Route 1: Mirpur**
- Mirpur 10 → Mirpur 6 → Campus
- Stops: 5 | Time: 25 min

**Route 2: Uttara**
- Uttara Sector 7 → Airport → Campus
- Stops: 4 | Time: 30 min

**Route 3: Dhanmondi**
- Dhanmondi 27 → Shbagh → Campus
- Stops: 6 | Time: 35 min

**Route 4: Gulshan**
- Gulshan 1 → Banani → Campus
- Stops: 4 | Time: 25 min

**Route 5: Cantonment**
- Cantonment → Baridhara → Campus
- Stops: 3 | Time: 20 min

🎯 All routes have WiFi-enabled shuttles!"""

    async def handle_complaint(self) -> str:
        return """📝 **Transport Complaint**

**Report an issue:**
1. 🚗 Driver behavior
2. ⏰ Schedule delay
3. 🚌 Vehicle condition
4. 👤 Harassment
5. 💰 Fare dispute

**How to report:**
- 📞 Call: 017xxxxxxxx
- 💬 WhatsApp: 017xxxxxxxx
- 📧 Email: transport@diu.edu.bd
- 📱 App: Transport Section

Your complaint will be resolved within 24 hours."""


async def get_shuttle_schedule(route: str = None) -> List[Dict]:
    return await university_data.get_shuttle_schedule(route)


async def track_shuttle(route: str) -> Dict:
    return {
        "route": route,
        "current_location": f"{route.title()} Bridge",
        "eta_minutes": 12,
        "passengers": 8,
        "capacity": 30,
        "last_updated": "Just now"
    }


async def book_vehicle(vehicle_type: str, destination: str, date: str) -> Dict:
    return {
        "booking_id": f"VEH-{hash(destination) % 10000}",
        "status": "confirmed",
        "vehicle": vehicle_type,
        "destination": destination,
        "cost": "To be confirmed"
    }


async def get_routes() -> List[Dict]:
    return [
        {"route": "Mirpur", "stops": 5, "time_minutes": 25},
        {"route": "Uttara", "stops": 4, "time_minutes": 30},
        {"route": "Dhanmondi", "stops": 6, "time_minutes": 35},
        {"route": "Gulshan", "stops": 4, "time_minutes": 25},
    ]


async def report_issue(issue_type: str, description: str) -> Dict:
    return {
        "complaint_id": f"TRAN-{hash(description) % 10000}",
        "status": "submitted",
        "response_time": "24 hours"
    }