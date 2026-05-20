# Daffodil Intelligence (DI)

360° Multi-Agent AI Operating System for University

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React + MUI)                     │
│                  http://localhost:3000                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                        ┌────────┴────────┐
                        │   API Gateway   │
                        │  FastAPI :8000  │
                        └────────┬────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │            │            │            │            │     │
┌───▼───┐   ┌────▼────┐  ┌───▼────┐  ┌──▼─────┐  ┌─▼────┐  │
│  MCP   │   │Messaging│  │  Live  │  │ Worker │  │ RAG  │  │
│ :8001  │   │ :8002   │  │ :8003  │  │  --    │  │ --   │  │
└────────┘   └─────────┘  └────────┘  └────────┘  └───────┘  │
```

## Available Agents

1. **Academic** - CGPA, results, courses, syllabus
2. **Library** - Books, journals, PDFs
3. **Campus** - Shuttle, rooms, notices
4. **Career** - Jobs, CV, roadmap
5. **Coding** - Debug, generate code
6. **Research** - Papers, thesis help
7. **Wellness** - Mental health support
8. **Finance** - Fees, payments, waivers
9. **Vision** - Image/PDF analysis
10. **Voice** - Speech-to-text, voice chat
11. **Automation** - Tasks, scheduling

## Quick Start

```bash
# Install dependencies
pnpm install

# Start all services (Windows, macOS, Linux compatible)
pnpm dev

# Or start individually:
# API: pnpm dev:api
# Web: pnpm dev:web
# MCP: pnpm --filter daffodil-mcp dev
# Live: pnpm --filter daffodil-live dev
# Messaging: pnpm --filter daffodil-messaging dev
# Worker: pnpm --filter daffodil-worker dev
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - OpenAI key
- `GEMINI_API_KEY` - Google Gemini key

## API Endpoints

- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/agents/chat` - Chat with agents
- `WS /ws/{user_id}` - WebSocket chat

## Tech Stack

- **Frontend**: React, Vite, MUI, Zustand
- **Backend**: FastAPI, SQLAlchemy, LangGraph
- **AI**: OpenAI, Gemini, LangChain
- **Real-time**: WebSockets, SSE
- **Messaging**: Telegram, WhatsApp, Discord