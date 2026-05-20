from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/daffodil"
    REDIS_URL: str = "redis://localhost:6379"
    
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4-turbo-preview"
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 30

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"
    GEMINI_VOICE: str = "Charon"

    TTS_PROSODY_RATE: str = "fast"
    TTS_PROSODY_PITCH: str = "+0%"
    TTS_STREAMING_ENABLED: bool = True
    TTS_INTERRUPT_ENABLED: bool = True

    QDRANT_URL: str = "http://localhost:6333"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    NODE_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    USE_MOCK_DATA: bool = False

    CORS_ORIGINS: str = "http://localhost:3000"

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
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    return Settings()