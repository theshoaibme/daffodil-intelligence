from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class NotificationAgent(BaseAgent):
    name = "Notification Agent"
    description = "Handles notifications, announcements, alerts, and messaging preferences"
    tools = ["get_notifications", "send_notification", "set_preferences", "mark_read", "get_announcements"]

    SYSTEM_PROMPT = """You are the Notification Agent for Daffodil Intelligence.
You help students with:
- Viewing notifications and announcements
- Managing notification preferences
- Sending messages to departments
- Marking notifications as read
- Subscribing to channels

Keep users informed and help them manage their communication!"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["notification", "alert", "notice"]):
            return await self.handle_notifications(context)

        elif any(k in message_lower for k in ["announcement", "broadcast", "notice"]):
            return await self.handle_announcements()

        elif any(k in message_lower for k in ["preference", "setting", "subscribe"]):
            return await self.handle_preferences()

        elif any(k in message_lower for k in ["send", "message", "contact"]):
            return await self.handle_send(message)

        elif any(k in message_lower for k in ["mark", "read", "clear"]):
            return await self.handle_mark_read()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_notifications(self, context: Optional[Dict] = None) -> str:
        notifications = [
            {"id": 1, "title": "Exam Schedule Released", "time": "2 hours ago", "read": False, "type": "urgent"},
            {"id": 2, "title": "Shuttle Route Changed - Mirpur", "time": "5 hours ago", "read": False, "type": "info"},
            {"id": 3, "title": "Library Holiday Tomorrow", "time": "1 day ago", "read": True, "type": "info"},
            {"id": 4, "title": "Hostel Fee Due in 5 Days", "time": "2 days ago", "read": True, "type": "warning"},
            {"id": 5, "title": "New Club Event: AI Workshop", "time": "3 days ago", "read": True, "type": "event"},
        ]

        unread_count = sum(1 for n in notifications if not n['read'])

        notif_list = "\n".join([
            f"{'🔴' if not n['read'] else '✅'} **{n['title']}**\n   ⏰ {n['time']}"
            for n in notifications[:5]
        ])

        return f"""🔔 **Your Notifications** ({unread_count} unread)

{notif_list}

📱 Tap to view details. Type "mark read [number]" to mark as read."""

    async def handle_announcements(self) -> str:
        return """📢 **Announcements**

**Important:**
🔴 **Exam Schedule 2026** - All students must check portal

**Upcoming:**
- 🆕 Career Fair - May 16, Auditorium
- 🆕 Hostel Registration Open
- 🆕 New Shuttle Routes Available

**General:**
- Library Hours: 8 AM - 10 PM
- cafeteria: 7 AM - 9 PM
- Emergency: 017xxxxxxxx

📱 All announcements also sent to email!"""

    async def handle_preferences(self) -> str:
        return """⚙️ **Notification Preferences**

**Current Settings:**
- 📧 Email: ✅ Enabled
- 📱 Push: ✅ Enabled
- 💬 SMS: ✅ Enabled
- 🔔 WhatsApp: ✅ Enabled

**Channel Subscriptions:**
- 📚 Academic Updates: ✅
- 🚌 Transport Alerts: ✅
- 🏠 Hostel Notices: ✅
- 🎉 Event Updates: ✅
- 💰 Payment Reminders: ✅
- 🎓 Career Opportunities: ✅

**To change settings:**
📱 DIU App > Settings > Notifications
📧 email: notifs@diu.edu.bd"""

    async def handle_send(self, message: str) -> str:
        return """📤 **Send a Message**

**Contact Departments:**
- 📞 Admission: admission@diu.edu.bd
- 📞 Academic: academic@diu.edu.bd
- 📞 Hostel: hostel@diu.edu.bd
- 📞 Transport: transport@diu.edu.bd
- 📞 IT Support: it@diu.edu.bd
- 📞 General: info@diu.edu.bd

**Response Time:**
- General: 24-48 hours
- Urgent: 4-8 hours

Include your Student ID for faster response!"""

    async def handle_mark_read(self) -> str:
        return """✅ **Mark as Read**

**Options:**
1. Mark all as read: "mark all read"
2. Mark specific: "mark read 1"
3. Delete old: "clear notifications"

📝 Your notification history is saved for 30 days."""


async def get_notifications(user_id: str, limit: int = 10) -> List[Dict]:
    return [
        {"id": 1, "title": "Exam Schedule Released", "read": False},
        {"id": 2, "title": "Shuttle Route Changed", "read": False},
    ]


async def send_notification(user_id: str, title: str, message: str, priority: str = "normal") -> Dict:
    return {
        "notification_id": f"NOTIF-{hash(message) % 10000}",
        "status": "sent",
        "message": "Notification sent successfully"
    }


async def set_preferences(user_id: str, preferences: Dict) -> Dict:
    return {
        "status": "saved",
        "message": "Your preferences have been updated"
    }


async def mark_read(notification_id: str) -> Dict:
    return {
        "status": "updated",
        "notification_id": notification_id,
        "read": True
    }


async def get_announcements(channel: str = None) -> List[Dict]:
    return [
        {"title": "Exam Schedule 2026", "date": "2026-05-12", "priority": "high"},
        {"title": "Career Fair", "date": "2026-05-10", "priority": "medium"},
    ]