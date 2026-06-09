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
            "Your job is to handle casual greetings (e.g., 'Hello', 'Hi') and "
            "queries that don't match a specific topic (e.g., asking for clarification).\n"
            f"If the user says a greeting, reply with exactly: {GREETING_EN}\n"
            "If the user asks something you don't understand, politely ask them to clarify "
            "and give examples of what you can do (e.g., CGPA, library, shuttle schedules, career).\n"
            "Respond in the same language as the user (English or Bengali)."
        )
        return await self.generate_response(system_prompt, message)
