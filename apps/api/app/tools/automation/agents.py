"""Invoke specialized domain agents as tools."""

from __future__ import annotations

from ..base import BaseTool, ToolParameter, ToolResult
from ...runtime.tool_context import get_user_id


class ListAgentsTool(BaseTool):
    name = "list_agents"
    description = (
        "List all specialized agents available to invoke (academic, routine, exam, "
        "planning, library, etc.) plus any custom Agent Hub agents, with short descriptions."
    )
    category = "automation"
    parameters: list[ToolParameter] = []

    async def execute(self, **kwargs) -> ToolResult:
        from ...agents.registry import AGENT_MAP
        from ...agents.builder import list_agents

        agents = [
            {"id": key, "name": agent.name, "description": agent.description, "kind": "builtin"}
            for key, agent in AGENT_MAP.items()
        ]
        for custom in list_agents():
            if custom.id in AGENT_MAP:
                continue
            agents.append(
                {
                    "id": custom.id,
                    "name": custom.name,
                    "description": custom.description,
                    "kind": "custom",
                }
            )
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
        from ...agents.builder import get_agent

        key = (agent_type or "").strip().lower()
        uid = int(user_id) if user_id else get_user_id()

        agent = AGENT_MAP.get(key)
        if agent:
            try:
                from ...runtime.tool_context import get_department, get_section

                ctx = {
                    "user_id": uid,
                    "section": get_section(default=""),
                    "department": get_department(),
                }
                if key in ("routine", "planning", "academic", "exam", "library", "transport"):
                    from ...automation.routine_mcp import merge_invoke_metadata
                    from ...runtime.pipeline import run_turn

                    result = await run_turn(
                        message,
                        user_id=uid,
                        chat_id=f"invoke-{uid}-{key}",
                        agent_id=key,
                        metadata=merge_invoke_metadata(key, message, uid),
                    )
                    response = result.get("content", "")
                else:
                    response = await agent.process(message, ctx)
                return self.ok(
                    {
                        "agent_type": key,
                        "agent_name": agent.name,
                        "response": response,
                    }
                )
            except Exception as e:
                return self.fail(f"Agent '{key}' failed: {e}")

        custom = get_agent(key)
        if custom:
            try:
                from ...runtime.pipeline import run_turn

                result = await run_turn(
                    message,
                    user_id=uid,
                    chat_id=f"invoke-{uid}-{key}",
                    agent_id=key,
                )
                return self.ok(
                    {
                        "agent_type": key,
                        "agent_name": custom.name,
                        "response": result.get("content", ""),
                    }
                )
            except Exception as e:
                return self.fail(f"Custom agent '{key}' failed: {e}")

        available = ", ".join(sorted(AGENT_MAP.keys()))
        return self.fail(f"Unknown agent '{agent_type}'. Available: {available}")
