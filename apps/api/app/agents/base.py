from abc import ABC, abstractmethod
from typing import Optional
import logging
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str
    description: str
    tools: list[str] = []

    def __init__(self):
        self._llm = None
        self.history: list = []

    @property
    def llm(self):
        if self._llm is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Please configure it in .env")
            self._llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY
            )
        return self._llm

    @abstractmethod
    async def process(self, message: str, context: Optional[dict] = None) -> str:
        pass

    def add_to_history(self, role: str, content: str):
        if role == "user":
            self.history.append(HumanMessage(content=content))
        else:
            self.history.append(AIMessage(content=content))

    def clear_history(self):
        self.history = []

    async def generate_response(self, system_prompt: str, user_message: str) -> str:
        messages = [("system", system_prompt)] + self.history + [("human", user_message)]
        response = await self.llm.agenerate([messages])
        self.add_to_history("assistant", response.generations[0][0].text)
        return response.generations[0][0].text

    def get_tools_description(self) -> str:
        if not self.tools:
            return "No tools available."
        return ", ".join(self.tools)