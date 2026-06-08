from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pathlib import Path
# pyrefly: ignore [missing-import]
import langchain
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = None

from .core.config import get_settings
from .core.database import init_db, close_db
from .core.logging import configure_logging, log_startup_banner, log_startup_ready, mark_startup_begin
from .core.middleware import LoggingMiddleware
from .mcp.client import mcp_client
from .api import auth, agents, websocket, chat, rag, upload, admin, agent_builder, voice, memory, telegram_auth, status, skills, agent_hub
from .api.computer_use import router as computer_use_router
from .live_broadcaster import live_router
from .messaging_gateway import messaging_router

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
mark_startup_begin()

Path("logs").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)

OPENAPI_TAGS = [
    {"name": "system", "description": "Health, status, and service catalog"},
    {"name": "chats", "description": "Chat sessions and streaming messages"},
    {"name": "agents", "description": "Agent runtime, tools, and routing"},
    {"name": "auth", "description": "Authentication and sessions"},
    {"name": "telegram-auth", "description": "Telegram Google OAuth"},
    {"name": "memory", "description": "Semantic and session memory"},
    {"name": "RAG", "description": "Document retrieval and embeddings"},
    {"name": "Voice", "description": "Speech, TTS, and voice WebSockets"},
    {"name": "computer-use", "description": "Desktop automation and recording"},
    {"name": "upload", "description": "File uploads"},
    {"name": "admin", "description": "Administration"},
    {"name": "Agent Hub", "description": "Unified built-in + custom agent catalog"},
    {"name": "skills", "description": "Skill hub, rulesets, and global agent config"},
    {"name": "messaging", "description": "Telegram / WhatsApp webhooks"},
    {"name": "live", "description": "Gemini live sessions"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        from .agents.builder import load_registry_from_db
        await load_registry_from_db()
    except Exception as e:
        logging.getLogger("app.agents").warning(f"Could not load custom agents from DB: {e}")

    from .integrations.telegram import telegram_bot

    tg_user = None
    try:
        await telegram_bot.start()
        if telegram_bot.enabled and telegram_bot._app:
            me = await telegram_bot._app.bot.get_me()
            tg_user = me.username
    except Exception as e:
        logging.getLogger("app.telegram").error(f"Telegram bot failed: {e}")

    log_startup_banner(
        port=settings.API_PORT,
        telegram_enabled=telegram_bot.enabled,
        telegram_username=tg_user,
        db_url=settings.DATABASE_URL,
    )
    log_startup_ready()

    yield

    try:
        await telegram_bot.stop()
    except Exception:
        pass
    await mcp_client.close()
    await close_db()


app = FastAPI(
    title="Daffodil Intelligence API",
    description=(
        "360° multi-agent AI platform for Daffodil International University. "
        "REST, WebSockets, MCP tools, live voice, and Telegram — single backend on port 8000."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(status.router)
app.include_router(auth.router, prefix="/api")
app.include_router(telegram_auth.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(agent_hub.router, prefix="/api")
app.include_router(agent_builder.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(live_router)
app.include_router(messaging_router)
app.include_router(computer_use_router)
app.websocket("/ws/{user_id}")(websocket.websocket_endpoint)
app.websocket("/voice/ws/{user_id}")(voice.voice_websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
