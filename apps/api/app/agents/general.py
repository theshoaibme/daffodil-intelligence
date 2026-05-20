from typing import Optional
from .base import BaseAgent


class GeneralAgent(BaseAgent):
    name = "General Agent"
    description = "Handles greetings, unknown queries, and basic clarification questions."
    tools = []

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        system_prompt = (
            "You are the General Agent for Daffodil Intelligence (DI).\n"
            "Your job is to handle casual greetings (e.g., 'Hello', 'Hi') and "
            "queries that don't match a specific topic (e.g., asking for clarification).\n"
            "If the user says a greeting, introduce yourself briefly as Daffodil Intelligence, "
            "and ask how you can help them today. Be warm and welcoming.\n"
            "If the user asks something you don't understand, politely ask them to clarify "
            "and give examples of what you can do (e.g., CGPA, library, shuttle schedules, career).\n"
            "Respond in the same language as the user (English or Bengali)."
        )
        return await self.generate_response(system_prompt, message)
