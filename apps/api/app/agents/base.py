from abc import ABC, abstractmethod
from typing import Optional
import logging
# pyrefly: ignore [missing-import]
import langchain
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = None
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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
            if settings.GROQ_API_KEY:
                kwargs = {
                    "model": settings.GROQ_MODEL,
                    "temperature": 0.7,
                    "api_key": settings.GROQ_API_KEY,
                    "base_url": settings.GROQ_BASE_URL,
                }
            elif settings.HUGGINGFACE_API_KEY and settings.HUGGINGFACE_ENABLED:
                kwargs = {
                    "model": settings.HUGGINGFACE_MODEL,
                    "temperature": 0.7,
                    "api_key": settings.HUGGINGFACE_API_KEY,
                    "base_url": settings.HUGGINGFACE_BASE_URL,
                }
            elif settings.OPENAI_API_KEY:
                kwargs = {
                    "model": settings.OPENAI_MODEL_NAME or "gpt-4-turbo-preview",
                    "temperature": 0.7,
                    "api_key": settings.OPENAI_API_KEY,
                }
                if settings.OPENAI_BASE_URL:
                    kwargs["base_url"] = settings.OPENAI_BASE_URL
                if "openrouter.ai" in (settings.OPENAI_BASE_URL or ""):
                    kwargs["default_headers"] = {
                        "HTTP-Referer": "https://daffodil.edu",
                        "X-Title": "Daffodil Intelligence",
                    }
            else:
                raise ValueError(
                    "No LLM API key configured. Set GROQ_API_KEY, HUGGINGFACE_API_KEY, or OPENAI_API_KEY in .env"
                )

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
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        
        # Primary attempt
        try:
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate" in err_str.lower() or "Too Many Requests" in err_str or "RESOURCE_EXHAUSTED" in err_str
            if not is_rate_limit:
                raise
            logger.warning(f"Primary model rate-limited, attempting fallback model")
        
        # Fallback to gemini-2.5-flash-lite (separate free-tier quota)
        try:
            fallback_llm = ChatOpenAI(
                model="models/gemini-2.5-flash-lite",
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            response = await fallback_llm.agenerate([messages])
            return response.generations[0][0].text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                raise RuntimeError("RATE_LIMITED") from e
            raise

    def get_tools_description(self) -> str:
        if not self.tools:
            return "No tools available."
        return ", ".join(self.tools)