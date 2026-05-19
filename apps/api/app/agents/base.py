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
        if settings.USE_MOCK_DATA or not settings.OPENAI_API_KEY:
            name_lower = self.name.lower()
            if "academic" in name_lower:
                mock_res = "I am the Academic Agent. I can assist you with your CGPA, results, courses, and syllabus. Currently, your CGPA is 3.75 (Excellent status)."
            elif "library" in name_lower:
                mock_res = "I am the Library Agent. I searched our university databases and found several relevant books on your query. You can borrow them from the 3rd floor."
            elif "campus" in name_lower:
                mock_res = "I am the Campus Agent. The shuttle leaves every hour from the main gate. The library is open from 9 AM to 8 PM."
            elif "career" in name_lower:
                mock_res = "I am the Career Agent. I have found 3 active job postings for Software Engineer Intern in our campus portal."
            elif "coding" in name_lower:
                mock_res = "I am the Coding Agent. The error 'undefined is not a function' usually means you are calling a method on an undefined variable. Make sure to check if the object is null/undefined before invoking."
            elif "research" in name_lower:
                mock_res = "I am the Research Agent. I found 5 publications on Deep Learning in our institutional repository."
            elif "wellness" in name_lower:
                mock_res = "I am the Wellness Agent. It's completely normal to feel stressed. Try taking a 10-minute break, drinking water, or reaching out to the student advisor."
            elif "finance" in name_lower:
                mock_res = "I am the Finance Agent. Your pending tuition fee for this semester is 15,000 BDT."
            else:
                mock_res = f"Hello! I am the {self.name}. How can I assist you today with your query: '{user_message}'?"
            
            self.add_to_history("assistant", mock_res)
            return mock_res
            
        messages = [("system", system_prompt)] + self.history + [("human", user_message)]
        response = await self.llm.agenerate([messages])
        self.add_to_history("assistant", response.generations[0][0].text)
        return response.generations[0][0].text

    def get_tools_description(self) -> str:
        if not self.tools:
            return "No tools available."
        return ", ".join(self.tools)