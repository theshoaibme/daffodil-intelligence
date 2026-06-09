"""Event hook automation tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.store import automation_store
from ...runtime.tool_context import get_user_id


class CreateAutomationHookTool(BaseTool):
    name = "create_automation_hook"
    description = (
        "Create an event hook: when event fires (on_login, on_keyword, on_schedule), "
        "run action (message, prompt, agent)."
    )
    category = "automation"
    parameters = [
        ToolParameter(name="name", type="string", description="Hook label"),
        ToolParameter(
            name="event",
            type="string",
            description="on_login | on_keyword | on_schedule",
        ),
        ToolParameter(
            name="action",
            type="string",
            description="message | prompt | agent",
        ),
        ToolParameter(
            name="payload",
            type="object",
            description="Action payload: text, agent_id, keyword, hour, etc.",
            required=False,
        ),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(
        self,
        name: str,
        event: str,
        action: str,
        payload: dict = None,
        user_id: str = None,
        **kwargs,
    ) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        if not uid:
            return self.fail("user_id required")
        hook = automation_store.create_hook(
            user_id=uid,
            name=name,
            event=event,
            action=action,
            payload=payload or {},
        )
        return self.ok({"hook": hook.to_dict(), "status": "created"})


class ListAutomationHooksTool(BaseTool):
    name = "list_automation_hooks"
    description = "List active automation hooks for the user."
    category = "automation"
    parameters = [
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        hooks = automation_store.list_hooks(user_id=uid)
        return self.ok({"hooks": [h.to_dict() for h in hooks], "count": len(hooks)})


class DeleteAutomationHookTool(BaseTool):
    name = "delete_automation_hook"
    description = "Deactivate an automation hook by id."
    category = "automation"
    parameters = [
        ToolParameter(name="hook_id", type="string", description="Hook id"),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, hook_id: str, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        ok = automation_store.delete_hook(uid, hook_id)
        if not ok:
            return self.fail("Hook not found")
        return self.ok({"hook_id": hook_id, "status": "deleted"})
