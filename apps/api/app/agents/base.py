from abc import ABC, abstractmethod
from typing import Optional
import logging
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
# pyrefly: ignore [missing-import]
from langchain.schema import HumanMessage, AIMessage, SystemMessage
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
            
            kwargs = {
                "model": settings.OPENAI_MODEL_NAME or "gpt-4-turbo-preview",
                "temperature": 0.7,
                "api_key": settings.OPENAI_API_KEY
            }
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
                
            if "openrouter.ai" in (settings.OPENAI_BASE_URL or ""):
                kwargs["default_headers"] = {
                    "HTTP-Referer": "https://daffodil.edu",
                    "X-Title": "Daffodil Intelligence",
                }
                
            self._llm = ChatOpenAI(**kwargs)
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
            msg_lower = user_message.lower().strip()
            
            # Friendly greetings
            if any(greeting in msg_lower for greeting in ["hello", "hi", "hey", "greetings"]):
                mock_res = f"Hello! I am the {self.name}. How can I assist you today?"
            elif "academic" in name_lower:
                if any(k in msg_lower for k in ["cgpa", "gpa"]):
                    mock_res = "I retrieved your student profile and your current CGPA is 3.75."
                elif any(k in msg_lower for k in ["course", "subject", "class"]):
                    mock_res = "You are currently registered for 4 courses this semester: Machine Learning, Computer Networks, Software Engineering, and Database Systems."
                elif any(k in msg_lower for k in ["result", "grade"]):
                    mock_res = "Your latest grade report shows excellent marks, including an A in Machine Learning."
                elif any(k in msg_lower for k in ["syllabus", "curriculum"]):
                    mock_res = "I have located the curriculum details for your CSE program."
                else:
                    mock_res = f"I am the Academic Agent. I can help you with your results, CGPA, courses, and syllabus. What would you like to know?"
            elif "library" in name_lower:
                if any(k in msg_lower for k in ["book", "search", "read"]):
                    mock_res = f"I searched the library databases for '{user_message}' and found several relevant books. You can borrow them from the 3rd floor."
                else:
                    mock_res = "I am the Library Agent. I can help you search the university libraries, check availability, or borrow books."
            elif "campus" in name_lower:
                mock_res = f"I am the Campus Agent. Regarding your query '{user_message}', let me know if you want shuttle schedules or room bookings."
            elif "career" in name_lower:
                mock_res = f"I am the Career Agent. I have found active job postings and internship listings matching '{user_message}' in our campus portal."
            elif "coding" in name_lower:
                mock_res = f"I am the Coding Agent. Regarding your programming query, make sure to check for null references or correct syntax."
            elif "research" in name_lower:
                mock_res = f"I am the Research Agent. I searched our repository and found publications related to '{user_message}'."
            elif "wellness" in name_lower:
                mock_res = "I am the Wellness Agent. It's completely normal to feel academic stress. Try taking a break, drinking water, or reaching out to the student advisor."
            elif "finance" in name_lower:
                mock_res = "I am the Finance Agent. Your pending tuition fee for this semester is 15,000 BDT."
            else:
                mock_res = f"Hello! I am the {self.name}. How can I assist you today with your query: '{user_message}'?"
            
            self.add_to_history("assistant", mock_res)
            return mock_res
            
        messages = [SystemMessage(content=system_prompt)] + self.history + [HumanMessage(content=user_message)]
        response = await self.llm.agenerate([messages])
        self.add_to_history("assistant", response.generations[0][0].text)
        return response.generations[0][0].text

    def get_tools_description(self) -> str:
        if not self.tools:
            return "No tools available."
        return ", ".join(self.tools)