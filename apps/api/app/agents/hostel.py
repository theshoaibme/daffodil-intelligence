from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class HostelAgent(BaseAgent):
    name = "Hostel Agent"
    description = "Handles hostel bookings, room allocations, complaints, and facilities"
    tools = ["book_hostel", "get_hostel_info", "submit_complaint", "check_hostel_status", "get_hostel_facilities"]

    SYSTEM_PROMPT = """You are the Hostel Agent for DI (Daffodil Intelligence).
You help students with:
- Hostel room bookings and allocations
- Checking hostel status and availability
- Submitting maintenance complaints
- Hostel facilities information
- Check-in/check-out processes
- Mess and meal information

Be helpful and polite. Use tools for accurate information."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["book", "room", "allocate"]):
            return await self.handle_booking(message)

        elif any(k in message_lower for k in ["complaint", "issue", "problem", "repair"]):
            return await self.handle_complaint(message)

        elif any(k in message_lower for k in ["status", "my room", "allocation"]):
            return await self.handle_status(context)

        elif any(k in message_lower for k in ["facility", "amenities", "mess", "food"]):
            return await self.handle_facilities()

        elif any(k in message_lower for k in ["check in", "check out", "move"]):
            return await self.handle_checkin()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_booking(self, message: str) -> str:
        return """🏠 **Hostel Room Booking**

To book a hostel room:

1. **Eligibility**: Must be a full-time student with valid ID
2. **Documents Required**:
   - Student ID Card
   - Passport size photo
   - Payment receipt

3. **Hostels Available**:
   - Hostel A (Boys) - Single: 5000BDT, Double: 3500BDT
   - Hostel B (Girls) - Single: 5500BDT, Double: 4000BDT
   - International Hostel - Single: 8000BDT, Double: 6000BDT

📞 Contact: 017xxxxxxx for booking"""

    async def handle_complaint(self, message: str) -> str:
        return """📝 **Submit Hostel Complaint**

To submit a complaint:

1. **Online**: Visit hostel portal
2. **WhatsApp**: Send to hostel office
3. **In Person**: Meet the warden

**Common Issues:**
- 🛠️ Electrical problems
- 🚿 Plumbing issues
- 🧹 Cleaning services
- 🍽️ Mess problems
- 🔐 Security concerns

Your complaint will be addressed within 24-48 hours."""

    async def handle_status(self, context: Optional[Dict] = None) -> str:
        user_id = context.get("user_id", 1) if context else 1
        
        return f"""🏠 **Your Hostel Status**

Room: **{'B-302' if user_id else 'Not Allocated'}**
Building: **{'Hostel A (Boys)' if user_id else 'N/A'}**
Floor: **3rd Floor**
Bed: **Bed A**
Status: **Active**

📅 Check-in Date: 2026-01-15
📅 Valid Until: 2026-12-31

Facilities:
- ✅ WiFi
- ✅ AC Room
- ✅ Attached Bath
- ✅ 24/7 Security"""

    async def handle_facilities(self) -> str:
        return """🏡 **Hostel Facilities**

**Common Facilities:**
- 📶 High-speed WiFi (24/7)
- 🛏️ Beds with mattresses
- 🛁 Hot water (6AM-9AM, 6PM-10PM)
- 🍳 Mess with breakfast, lunch, dinner
- 🏋️ Gym (Hostel A & B)
- 🏀 Sports room
- 📚 Study room
- 🧺 Laundry (self-service)
- 🛒 Mini mart

**Mess Timings:**
- Breakfast: 6:30 AM - 9:00 AM
- Lunch: 12:00 PM - 2:30 PM
- Dinner: 7:00 PM - 9:30 PM

💰 Monthly Mess: 2500 BDT"""

    async def handle_checkin(self) -> str:
        return """🚪 **Check-in / Check-out Process**

**Check-in:**
1. Bring all documents to hostel office
2. Pay security deposit (5000 BDT)
3. Get room key and ID card
4. Complete inventory check

**Check-out:**
1. Submit room key
2. Final room inspection
3. Get deposit refund (within 7 days)
4. Clear all mess dues

⏰ Check-in: 9 AM - 5 PM (Weekdays)
⏰ Check-out: 10 AM (Same day)"""


async def book_hostel(student_id: str, preferences: Dict) -> Dict:
    return {
        "status": "pending",
        "application_id": f"HOST-{student_id}-001",
        "message": "Application submitted. Wait for confirmation."
    }


async def get_hostel_info(student_id: str) -> Dict:
    return {
        "room": "B-302",
        "building": "Hostel A",
        "floor": 3,
        "bed": "A",
        "status": "active"
    }


async def submit_complaint(student_id: str, issue: str, category: str) -> Dict:
    return {
        "complaint_id": f"COMP-{student_id}-{hash(issue) % 1000}",
        "status": "submitted",
        "estimated_resolution": "24-48 hours"
    }


async def get_hostel_facilities(building: str = None) -> List[Dict]:
    facilities = [
        {"name": "WiFi", "available": True, "speed": "100 Mbps"},
        {"name": "AC", "available": True, "cost": "Included"},
        {"name": "Hot Water", "available": True, "timing": "Morning & Evening"},
        {"name": "Mess", "available": True, "cost": "2500 BDT/month"},
        {"name": "Gym", "available": True, "cost": "Free"},
    ]
    return facilities