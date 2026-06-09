from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Infrastructure
    POSTGRES_USER: str = "daffodil"
    POSTGRES_PASSWORD: str = "daffodil"
    POSTGRES_DB: str = "daffodil"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str = "postgresql://daffodil:daffodil@localhost:5432/daffodil"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "daffodil"
    MINIO_SECRET_KEY: str = "daffodil123"
    MINIO_BUCKET: str = "daffodil"
    MINIO_USE_SSL: bool = False
    MINIO_CONSOLE_URL: str = "http://localhost:9001"
    
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4-turbo-preview"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    GROQ_FAST_CHAT: bool = True
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 30

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Optional override; default matches /api/auth/telegram/google/callback on API_PUBLIC_URL
    GOOGLE_OAUTH_REDIRECT_URI: str = ""
    TELEGRAM_GOOGLE_OAUTH_REDIRECT_URI: str = ""
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

    # === Antigravity agent runtime ===
    ANTIGRAVITY_MODEL: str = "gemini-2.0-flash"
    ANTIGRAVITY_SAVE_DIR: str = "conversations"
    ANTIGRAVITY_ENABLE_SUBAGENTS: bool = True
    CONTEXT_WINDOW_TOKENS: int = 128_000

    # === MCP ===
    MCP_SERVER_PORT: int = 8001
    MCP_TRANSPORT: str = "stdio"  # 'stdio' or 'http'
    MCP_ENABLED: bool = True
    MCP_EXTERNAL_SERVERS: str = ""  # comma-separated name=command pairs for stdio servers

    # === Telegram ===
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_ALLOWED_USER_IDS: str = ""  # comma-separated telegram user ids (empty = allow all)
    # comma-separated telegram user ids allowed to run /shell (empty = nobody)
    TELEGRAM_ADMIN_USER_IDS: str = ""
    # Keep False so commands/messages sent during API restarts are processed when the bot is back.
    TELEGRAM_DROP_PENDING_UPDATES: bool = False
    # Telegram chat model; "auto" uses the router (Groq for simple chat, Gemini otherwise).
    TELEGRAM_CHAT_MODEL: str = "auto"
    API_PUBLIC_URL: str = "http://localhost:8000"
    FRONTEND_PUBLIC_URL: str = "http://localhost:3000"
    # Optional HTTPS/ngrok URL for Telegram Google sign-in buttons (empty = API_PUBLIC_URL)
    TELEGRAM_OAUTH_PUBLIC_URL: str = ""

    # === Email OTP (registration) ===
    # EMAIL_PROVIDER: auto | smtp | resend | none
    EMAIL_PROVIDER: str = "auto"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_SSL: bool = False
    SMTP_STARTTLS: bool = True
    RESEND_API_KEY: str = ""

    APP_SECRET_KEY: str = ""

    # === Computer Use ===
    COMPUTER_USE_ENABLED: bool = True
    COMPUTER_USE_REQUIRE_CONFIRM: bool = True
    SCREEN_CAPTURE_FPS: int = 5

    # === Celery ===
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # === Memory ===
    MEMORY_QDRANT_COLLECTION: str = "daffodil_memory"
    MEMORY_SEMANTIC_ENABLED: bool = True

    TTS_PROSODY_RATE: str = "fast"
    TTS_PROSODY_PITCH: str = "+0%"
    TTS_STREAMING_ENABLED: bool = True
    TTS_INTERRUPT_ENABLED: bool = True

    QDRANT_URL: str = "http://localhost:6333"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    NODE_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000

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