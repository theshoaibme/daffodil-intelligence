from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/daffodil"
    REDIS_URL: str = "redis://localhost:6379"
    QDRANT_URL: str = "http://localhost:6333"

    OPENAI_API_KEY: str = "sk-test-key"
    GEMINI_API_KEY: str = "test-key"
    ANTHROPIC_API_KEY: str = "test-key"

    JWT_SECRET: str = "test-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 30

    TELEGRAM_BOT_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"
    GEMINI_VOICE: str = "Aoede"

    QDRANT_URL: str = "http://localhost:6333"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    NODE_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    USE_MOCK_DATA: bool = True

    UNIV_SIS_API_URL: str = "https://sis.daffodiluniversity.edu.bd/api"
    UNIV_SIS_API_KEY: str = ""
    UNIV_LIBRARY_API_URL: str = "https://library.daffodiluniversity.edu.bd/api"
    UNIV_LIBRARY_API_KEY: str = ""
    UNIV_HR_API_URL: str = "https://hr.daffodiluniversity.edu.bd/api"
    UNIV_HR_API_KEY: str = ""
    UNIV_TRANSPORT_API_URL: str = "https://transport.daffodiluniversity.edu.bd/api"
    UNIV_TRANSPORT_API_KEY: str = ""
    UNIV_EXAM_API_URL: str = "https://exam.daffodiluniversity.edu.bd/api"
    UNIV_EXAM_API_KEY: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()