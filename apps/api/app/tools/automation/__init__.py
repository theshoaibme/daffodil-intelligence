"""Automation & agent-invocation tools."""

from .agents import InvokeAgentTool, ListAgentsTool
from .hooks_tools import (
    CreateAutomationHookTool,
    DeleteAutomationHookTool,
    ListAutomationHooksTool,
)
from .personal_routines import CreateRoutineTool, DeleteRoutineTool, ListRoutinesTool
from .reminders import CreateReminderTool, DeleteReminderTool, ListRemindersTool
from .routine import EnableRoutineAutomationTool, GetClassRoutineTool
from .schedule_tools import GetDailyScheduleTool, ScheduleTaskTool
from .telegram_tool import SendTelegramMessageTool

__all__ = [
    "InvokeAgentTool",
    "ListAgentsTool",
    "CreateReminderTool",
    "ListRemindersTool",
    "DeleteReminderTool",
    "SendTelegramMessageTool",
    "GetClassRoutineTool",
    "EnableRoutineAutomationTool",
    "CreateRoutineTool",
    "ListRoutinesTool",
    "DeleteRoutineTool",
    "GetDailyScheduleTool",
    "ScheduleTaskTool",
    "CreateAutomationHookTool",
    "ListAutomationHooksTool",
    "DeleteAutomationHookTool",
]
