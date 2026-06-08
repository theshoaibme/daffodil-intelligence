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
from .core.middleware import LoggingMiddleware
from .mcp.client import mcp_client
from .api import auth, agents, websocket, chat, rag, upload, admin, agent_builder, voice
from .api.computer_use import router as computer_use_router
from .live_broadcaster import live_router
from .messaging_gateway import messaging_router

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

Path("logs").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await mcp_client.close()
    await close_db()


app = FastAPI(
    title="Daffodil Intelligence API",
    description="360° Multi-Agent AI Operating System for University",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

@app.get("/api/agents/list")
async def list_agents():
    return {
        "agents": [
            {"id": "academic", "name": "Academic Agent", "status": "active", "category": "university"},
            {"id": "library", "name": "Library Agent", "status": "active", "category": "university"},
            {"id": "campus", "name": "Campus Agent", "status": "active", "category": "university"},
            {"id": "career", "name": "Career Agent", "status": "active", "category": "university"},
            {"id": "coding", "name": "Coding Agent", "status": "active", "category": "productivity"},
            {"id": "research", "name": "Research Agent", "status": "active", "category": "productivity"},
            {"id": "wellness", "name": "Wellness Agent", "status": "active", "category": "university"},
            {"id": "finance", "name": "Finance Agent", "status": "active", "category": "university"},
            {"id": "vision", "name": "Vision Agent", "status": "active", "category": "ai"},
            {"id": "voice", "name": "Voice Agent", "status": "active", "category": "ai"},
            {"id": "exam", "name": "Exam Agent", "status": "active", "category": "university"},
            {"id": "hostel", "name": "Hostel Agent", "status": "active", "category": "university"},
            {"id": "transport", "name": "Transport Agent", "status": "active", "category": "university"},
            {"id": "event", "name": "Event Agent", "status": "active", "category": "university"},
            {"id": "complaint", "name": "Complaint Agent", "status": "active", "category": "university"},
            {"id": "notification", "name": "Notification Agent", "status": "active", "category": "university"},
            {"id": "fee", "name": "Fee Agent", "status": "active", "category": "university"},
            {"id": "computer_use", "name": "Computer Use Agent", "status": "active", "category": "computer"},
            {"id": "copycat", "name": "CopyCat Agent", "status": "active", "category": "computer"},
            {"id": "planning", "name": "Planning Agent", "status": "active", "category": "orchestration"},
        ]
    }

app.include_router(auth.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(agent_builder.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(live_router)
app.include_router(messaging_router)
app.include_router(computer_use_router)
app.websocket("/ws/{user_id}")(websocket.websocket_endpoint)
app.websocket("/voice/ws/{user_id}")(voice.voice_websocket)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Daffodil Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "services": ["api", "mcp", "live", "messaging"]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "di-api", "tools": len(mcp_client.registry) if hasattr(mcp_client, 'registry') else 0}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)