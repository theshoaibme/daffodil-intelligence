from typing import Optional
from ..prompts.manager import GREETING_EN
from .base import BaseAgent


class GeneralAgent(BaseAgent):
    name = "General Agent"
    description = "Handles greetings, unknown queries, and basic clarification questions."
    tools = []

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        system_prompt = (
            "You are the General Agent for Daffodil Intelligence.\n"
            "Handle casual greetings and queries that don't match a specific topic.\n"
            f"If the message is only a greeting (hello/hi/hey), reply with exactly: {GREETING_EN}\n"
            "Otherwise respond naturally and briefly in the user's language (English or Bengali). "
            "Do not repeat the greeting. If unclear, ask a short clarifying question and mention "
            "examples (CGPA, library, shuttle, career)."
        )
        return await self.generate_response(system_prompt, message)
