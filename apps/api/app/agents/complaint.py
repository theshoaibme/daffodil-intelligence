from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ComplaintAgent(BaseAgent):
    name = "Complaint Agent"
    description = "Handles student complaints, feedback, suggestions, and grievance resolution"
    tools = ["submit_complaint", "get_complaint_status", "escalate_issue", "give_feedback", "get_grievance_policy"]

    SYSTEM_PROMPT = """You are the Complaint Agent for DI (Daffodil Intelligence).
You help students with:
- Submitting complaints
- Tracking complaint status
- Providing feedback
- Escalating unresolved issues
- Understanding grievance policies
- Anonymous reporting

Be empathetic and helpful. Assure students their concerns are heard."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["complaint", "issue", "problem"]):
            return await self.handle_complaint(message)

        elif any(k in message_lower for k in ["status", "track", "progress"]):
            return await self.handle_status(context)

        elif any(k in message_lower for k in ["feedback", "suggestion", "opinion"]):
            return await self.handle_feedback()

        elif any(k in message_lower for k in ["escalate", "appeal", "unresolved"]):
            return await self.handle_escalate()

        elif any(k in message_lower for k in ["policy", "rule", "procedure"]):
            return await self.handle_policy()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_complaint(self, message: str) -> str:
        return """📝 **Submit a Complaint**

**Categories:**
1. 🏫 Academic (grades, courses, teachers)
2. 🏠 Hostel (room, facilities, mess)
3. 🚌 Transport (shuttle, driver)
4. 💰 Finance (fees, payments)
5. 👥 Harassment
6. 🏢 Administrative

**How to Submit:**
1. 📱 Online: Student Portal > Complaints
2. 📞 Call: 02-xxxxxxx
3. 📧 Email: grievance@diu.edu.bd
4. 📍 In Person: Student Affairs Office

**Processing Time:**
- Simple: 24-48 hours
- Complex: 7-10 days"""

    async def handle_status(self, context: Optional[Dict] = None) -> str:
        user_id = context.get("user_id", 1) if context else 1

        return f"""🔍 **Your Complaint Status**

| ID | Category | Status | Date |
|----|----------|--------|------|
| CMP-001 | Hostel | 🟢 Resolved | May 10 |
| CMP-002 | Transport | 🟡 In Progress | May 8 |

**CMP-002 Details:**
- Issue: Shuttle delay on Mirpur route
- Status: Under investigation
- Expected: 2 more days
- Assigned to: Transport Manager

📝 Type "escalate CMP-002" if you want to speed up."""

    async def handle_feedback(self) -> str:
        return """💬 **Submit Feedback**

We value your opinion! Help us improve.

**Types of Feedback:**
1. ⭐ Rate a service (1-5 stars)
2. 💡 Suggest an improvement
3. 🙌 Give a compliment
4. 📋 General feedback

**Where to submit:**
- 📱 DIU App > Feedback
- 📧 feedback@diu.edu.bd
- 📋 Feedback forms at admin office

🎁 Get 10 reward points for every feedback!

Your feedback helps shape DIU's future! 💙"""

    async def handle_escalate(self) -> str:
        return """⬆️ **Escalate an Issue**

**If your complaint is not resolved:**

1. **Level 1**: Department Head
2. **Level 2**: Dean/Principal
3. **Level 3**: Vice Chancellor
4. **Level 4**: University Board

**How to Escalate:**
1. Submit escalation request
2. Provide complaint ID
3. Explain why you're escalating
4. Attach previous correspondence

📋 Deadline: Within 14 days of last update

⚠️ False escalation may affect future requests."""

    async def handle_policy(self) -> str:
        return """📜 **Grievance Policy**

**Our Commitment:**
- All complaints addressed within 14 days
- Fair and transparent investigation
- No retaliation against complainants
- Confidentiality maintained

**Your Rights:**
- Right to be heard
- Right to updates
- Right to appeal
- Right to anonymity

**Protection:**
- No discrimination
- No victimization
- Complete privacy

📖 Full policy: studenthandbook.diu.edu.bd

Questions? Contact: grievance@diu.edu.bd"""


async def submit_complaint(category: str, description: str, student_id: str, priority: str = "medium") -> Dict:
    return {
        "complaint_id": f"CMP-{hash(description) % 100000}",
        "status": "submitted",
        "category": category,
        "priority": priority,
        "estimated_resolution": "7-10 days",
        "message": "Your complaint has been submitted. We'll keep you updated."
    }


async def get_complaint_status(complaint_id: str) -> Dict:
    return {
        "complaint_id": complaint_id,
        "status": "in_progress",
        "last_update": "2026-05-10",
        "assigned_to": "Department Head",
        "next_update": "2026-05-12"
    }


async def escalate_issue(complaint_id: str, reason: str) -> Dict:
    return {
        "escalation_id": f"ESC-{complaint_id}",
        "new_level": "Department Head",
        "status": "escalated",
        "message": "Your issue has been escalated. You will be contacted within 48 hours."
    }


async def give_feedback(category: str, rating: int, comment: str) -> Dict:
    return {
        "feedback_id": f"FB-{hash(comment) % 10000}",
        "status": "submitted",
        "reward_points": 10,
        "message": "Thank you for your feedback! You've earned 10 reward points."
    }


async def get_grievance_policy() -> Dict:
    return {
        "response_time": "14 days",
        "confidentiality": True,
        "appeal_available": True,
        "anon_reporting": True
    }