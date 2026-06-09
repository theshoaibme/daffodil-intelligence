"""Reminder CRUD tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.store import automation_store
from ...runtime.tool_context import get_user_id


class CreateReminderTool(BaseTool):
    name = "create_reminder"
    description = (
        "Schedule a reminder for the user. Supports Telegram delivery when the account "
        "is linked. Use ISO datetime for fire_at (e.g. 2026-06-10T09:00:00)."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="title", type="string", description="Reminder title"),
        ToolParameter(
            name="fire_at",
            type="string",
            description="When to fire (ISO datetime UTC)",
        ),
        ToolParameter(
            name="repeat",
            type="string",
            description="once | daily | weekly",
            required=False,
            default="once",
        ),
        ToolParameter(
            name="channel",
            type="string",
            description="telegram | in_app",
            required=False,
            default="telegram",
        ),
        ToolParameter(
            name="body",
            type="string",
            description="Optional full message body for Telegram",
            required=False,
        ),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(
        self,
        title: str,
        fire_at: str,
        repeat: str = "once",
        channel: str = "telegram",
        body: str = None,
        user_id: str = None,
        **kwargs,
    ) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        if not uid:
            return self.fail("user_id required to create reminder")
        rec = automation_store.create_reminder(
            user_id=uid,
            title=title,
            fire_at=fire_at,
            repeat=repeat,
            channel=channel,
            payload={"body": body} if body else {},
        )
        return self.ok({"reminder": rec.to_dict(), "status": "scheduled"})


class ListRemindersTool(BaseTool):
    name = "list_reminders"
    description = "List active scheduled reminders for the user."
    category = "automation"
    parameters = [
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        items = automation_store.list_reminders(uid)
        return self.ok({"reminders": [r.to_dict() for r in items], "count": len(items)})


class DeleteReminderTool(BaseTool):
    name = "delete_reminder"
    description = "Cancel/deactivate a reminder by id."
    category = "automation"
    parameters = [
        ToolParameter(name="reminder_id", type="string", description="Reminder id"),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, reminder_id: str, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        ok = automation_store.delete_reminder(uid, reminder_id)
        if not ok:
            return self.fail("Reminder not found or access denied")
        return self.ok({"reminder_id": reminder_id, "status": "cancelled"})
