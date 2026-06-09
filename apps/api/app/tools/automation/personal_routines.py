"""Personal study/habit routines (stored per user)."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...automation.store import automation_store
from ...runtime.tool_context import get_user_id


class CreateRoutineTool(BaseTool):
    name = "create_routine"
    description = "Create a named personal routine with schedule label and task list."
    category = "automation"
    parameters = [
        ToolParameter(name="name", type="string", description="Routine name"),
        ToolParameter(name="schedule", type="string", description="e.g. Mon–Fri 7:00 AM"),
        ToolParameter(
            name="tasks",
            type="array",
            description="List of task strings",
            required=False,
        ),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(
        self,
        name: str,
        schedule: str,
        tasks: list = None,
        user_id: str = None,
        **kwargs,
    ) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        if not uid:
            return self.fail("user_id required")
        rec = automation_store.create_personal_routine(
            user_id=uid,
            name=name,
            schedule=schedule,
            tasks=tasks or [],
        )
        return self.ok({"routine": rec.to_dict(), "status": "created"})


class ListRoutinesTool(BaseTool):
    name = "list_routines"
    description = "List the user's saved personal routines."
    category = "automation"
    parameters = [
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        items = automation_store.list_personal_routines(uid)
        return self.ok({"routines": [r.to_dict() for r in items], "count": len(items)})


class DeleteRoutineTool(BaseTool):
    name = "delete_routine"
    description = "Deactivate a personal routine by id."
    category = "automation"
    parameters = [
        ToolParameter(name="routine_id", type="string", description="Routine id"),
        ToolParameter(name="user_id", type="string", description="User id", required=False),
    ]

    async def execute(self, routine_id: str, user_id: str = None, **kwargs) -> ToolResult:
        uid = int(user_id) if user_id else get_user_id()
        ok = automation_store.delete_personal_routine(uid, routine_id)
        if not ok:
            return self.fail("Routine not found")
        return self.ok({"routine_id": routine_id, "status": "deleted"})
