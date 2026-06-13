"""Workflow automation agent — delegates to specialists and parallel runbooks."""

from __future__ import annotations

from typing import Dict, Optional

from .base import BaseAgent


class AutomationAgent(BaseAgent):
    name = "Automation Agent"
    description = "Workflow automation — delegate to specialists and parallel agent runbooks"
    tools = [
        "invoke_agent",
        "parallel_invoke_agents",
        "list_agents",
    ]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are the Automation Agent — delegate to specialists and coordinate multi-agent workflows.",
            message,
        )
