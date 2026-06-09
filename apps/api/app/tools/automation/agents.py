"""Invoke specialized domain agents as tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...runtime.tool_context import get_user_id


class ListAgentsTool(BaseTool):
    name = "list_agents"
    description = (
        "List all specialized agents available to invoke (academic, routine, exam, "
        "planning, library, etc.) with short descriptions."
    )
    category = "automation"
    parameters: list[ToolParameter] = []

    async def execute(self, **kwargs) -> ToolResult:
        from ...agents.registry import AGENT_MAP

        agents = [
            {"id": key, "name": agent.name, "description": agent.description}
            for key, agent in AGENT_MAP.items()
        ]
        return self.ok({"agents": agents, "count": len(agents)})


class InvokeAgentTool(BaseTool):
    name = "invoke_agent"
    description = (
        "Run a specialized agent (routine, exam, planning, academic, library, etc.) "
        "with a message and return its response. Use for tasks that need a specific expert agent."
    )
    category = "automation"
    parameters = [
        ToolParameter(
            name="agent_type",
            type="string",
            description=(
                "Agent key e.g. routine, exam, planning, academic, notification, research"
            ),
        ),
        ToolParameter(
            name="message",
            type="string",
            description="Task or question to send to that agent",
        ),
        ToolParameter(
            name="user_id",
            type="string",
            description="Web user id (optional; uses current session if omitted)",
            required=False,
        ),
    ]

    async def execute(
        self, agent_type: str, message: str, user_id: str = None, **kwargs
    ) -> ToolResult:
        from ...agents.registry import AGENT_MAP

        key = (agent_type or "").strip().lower()
        agent = AGENT_MAP.get(key)
        if not agent:
            available = ", ".join(sorted(AGENT_MAP.keys()))
            return self.fail(f"Unknown agent '{agent_type}'. Available: {available}")

        uid = int(user_id) if user_id else get_user_id()
        try:
            response = await agent.process(message, {"user_id": uid})
            return self.ok(
                {
                    "agent_type": key,
                    "agent_name": agent.name,
                    "response": response,
                }
            )
        except Exception as e:
            return self.fail(f"Agent '{key}' failed: {e}")
