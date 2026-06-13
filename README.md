# Daffodil Intelligence (DI)

360° Multi-Agent AI Operating System for University

## Documentation

For comprehensive technical specifications, architectural topology, database schemas, and integration guides, see the [Daffodil Intelligence Project Documentation](file:///c:/Users/User/Desktop/daffodil-intelligence/docs/PROJECT_DOCUMENTATION.md).

Key additions documented:
- **Intercommunication Ecosystem**: Asynchronous agent-to-agent event-driven collaboration, event delegation, Dynamic Agent Registry, and CloudEvents schemas.
- **Research Community**: Vector similarity matching for thesis advisors, collaborative knowledge vaults (RAG), and thesis milestone tracking.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Vite + React)                    │
│                  http://localhost:3000                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                        ┌────────┴────────┐
                        │  Backend (API)  │
                        │  FastAPI :8000  │
                        │  REST · WS · MCP│
                        │  Live · Telegram│
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │           │           │           │           │
    PostgreSQL    Redis       MinIO       Qdrant      Adminer
     :5432       :6379    :9000 / :9001    :6333       :8080
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

# Docker infra + frontend + backend (one API server on :8000)
pnpm dev

# Or step by step:
pnpm docker:infra   # Postgres, Redis, MinIO, Adminer, Qdrant
pnpm dev:api        # Backend only (API + MCP + live + Telegram + WS)
pnpm dev:web        # Frontend only
```

MCP, live voice, messaging webhooks, and WebSockets all run inside the **same** FastAPI process (`apps/api`) — there are no separate `:8001` / `:8002` servers.

## Environment Variables

Copy `.env.example` to `.env` at the repo root, then copy `apps/api/.env.example` to `apps/api/.env` for the API.

| Service | URL | Default login |
|---------|-----|----------------|
| PostgreSQL | `localhost:5432` | `daffodil` / `daffodil` |
| Adminer | http://localhost:8080 | Server: `postgres` (Docker) or `localhost` |
| Redis | `localhost:6379` | no auth |
| MinIO API | http://localhost:9000 | `daffodil` / `daffodil123` |
| MinIO Console | http://localhost:9001 | same as MinIO |
| Qdrant | http://localhost:6333 | — |

Start infrastructure:

```bash
docker compose up -d postgres redis minio adminer qdrant
```

## Database migrations

Skills, rulesets, custom agents, and agent profiles are stored in PostgreSQL. Use the project virtualenv (not system `apt install alembic`) from `apps/api`:

```bash
cd apps/api
../../.venv/bin/alembic upgrade head
../../.venv/bin/python scripts/archive/migrate_json_to_postgres.py   # one-time JSON backfill (idempotent)
```

Or from the repo root:

```bash
pnpm db:migrate
```

`apps/api/data/examples/` holds sample JSON for reference only — it is **not** loaded at runtime.

On deploy, run `alembic upgrade head` before starting the API (do not rely on `create_all` alone in production).

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