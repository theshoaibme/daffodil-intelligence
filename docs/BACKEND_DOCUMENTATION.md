# Daffodil Intelligence - Backend Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Backend Applications](#backend-applications)
4. [Agents System](#agents-system)
5. [Core Modules](#core-modules)
6. [API Routes](#api-routes)
7. [MCP Tool Server](#mcp-tool-server)
8. [Voice & Realtime](#voice--realtime)
9. [Database & Configuration](#database--configuration)
10. [External Integrations](#external-integrations)

---

## Project Overview

**Daffodil Intelligence** is an AI-powered university assistant system that provides students with intelligent responses across multiple domains including academics, career, library, finance, campus services, and more. The system uses a multi-agent architecture with a supervisor orchestrator to route queries to specialized agents.

**Technology Stack:**
- **Backend:** FastAPI (Python)
- **AI/LLM:** OpenAI GPT-4, Google Gemini
- **Vector Database:** Qdrant (for RAG)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Real-time:** WebSocket, SSE (Server-Sent Events)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Web)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                     │
│                    apps/api/app/main.py                        │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
   ┌────────────┐      ┌────────────┐      ┌────────────┐
   │  Agents    │      │   Voice    │      │    RAG     │
   │  System    │      │  Pipeline  │      │   API      │
   └────────────┘      └────────────┘      └────────────┘
          │
          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │              Supervisor Agent (Orchestrator)               │
   │                    agents/supervisor.py                     │
   └─────────────────────────────────────────────────────────────┘
          │
          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    18 Specialized Agents                   │
   └─────────────────────────────────────────────────────────────┘
```

---

## Backend Applications

### 1. API Application (`apps/api/`)
Main REST API server handling all HTTP requests, agent orchestration, and business logic.

**Entry Point:** `apps/api/app/main.py`

**Key Directories:**
```
apps/api/app/
├── agents/           # AI Agent implementations
├── api/             # API route handlers
├── core/            # Core utilities (config, security, database)
├── models/          # Database models
├── schemas/         # Pydantic schemas
├── voice/          # Voice processing modules
├── prompts/         # Prompt templates
├── rag_api.py       # RAG API handler
├── master_agent.py  # Master agent orchestration
├── auth_engine.py  # Authentication engine
├── messaging_gateway.py  # Messaging integration
└── live_broadcaster.py   # Live broadcast handler
```

### 2. MCP Server (`packages/mcp/`)
Model Context Protocol server providing tools/function calling capabilities.

**Entry Point:** `packages/mcp/app/server.py`

**Features:**
- 20+ registered tools across categories
- Rate limiting (100 requests/minute)
- Input sanitization & validation
- Caching system (TTL-based)
- Permission-based access control (Student/Faculty/Admin/Public)
- Real-time tools support

### 3. Live Application (`packages/live/`)
WebRTC-based real-time voice communication.

**Entry Point:** `packages/live/app/server.py`

**Key Components:**
- `webrtc_integration.py` - WebRTC integration
- `nano_bridge.py` - Nano bridge for voice
- `webrtc_client.py` - Client management

### 4. Messaging Application (`packages/messaging/`)
Handles messaging integrations (Telegram, WhatsApp).

**Entry Point:** `packages/messaging/app/main.py`

**Features:**
- `voice_handler.py` - Voice message processing

### 5. Worker Application (`packages/worker/`)
Background job processing.

**Entry Point:** `packages/worker/app/tasks.py`

---

## Agents System

The system uses a **Supervisor Pattern** where a master supervisor agent routes queries to 18 specialized agents based on intent detection.

### Agent Architecture

**Base Class:** `agents/base.py`
- Abstract base class for all agents
- Provides LLM integration (OpenAI GPT-4)
- Message history management
- Response generation

### 18 Specialized Agents

| # | Agent | File | Description |
|---|-------|------|-------------|
| 1 | **Supervisor** | `agents/supervisor.py` | Main orchestrator that routes to correct agents |
| 2 | **Academic** | `agents/academic.py` | CGPA, grades, courses, syllabus, results |
| 3 | **Library** | `agents/library.py` | Books, journals, PDFs, reservations |
| 4 | **Campus** | `agents/campus.py` | Shuttle, rooms, notices, facilities |
| 5 | **Career** | `agents/career.py` | Jobs, internships, CV review, career roadmap |
| 6 | **Coding** | `agents/coding.py` | Debugging, code generation, programming help |
| 7 | **Research** | `agents/research.py` | Papers, thesis, citations, publications |
| 8 | **Wellness** | `agents/wellness.py` | Mental health, study tips, stress management |
| 9 | **Finance** | `agents/finance.py` | Fees, payments, waivers, scholarships |
| 10 | **Vision** | `agents/vision.py` | Image/PDF analysis, OCR, screen reading |
| 11 | **Voice** | `agents/voice.py` | Speech-to-text, text-to-speech, voice calls |
| 12 | **Exam** | `agents/exam.py` | Exam schedules, seat plans, attendance |
| 13 | **Hostel** | `agents/hostel.py` | Room booking, complaints, facilities |
| 14 | **Transport** | `agents/transport.py` | Shuttle tracking, routes, vehicle booking |
| 15 | **Event** | `agents/event.py` | Workshops, seminars, clubs, activities |
| 16 | **Complaint** | `agents/complaint.py` | Grievances, feedback, escalations |
| 17 | **Notification** | `agents/notification.py` | Alerts, announcements, preferences |
| 18 | **Fee** | `agents/fee_agent.py` | Tuition, installments, payment status |

### Supervisor Agent

**File:** `agents/supervisor.py`

The Supervisor Agent:
1. Detects user intent using keyword matching
2. Routes to appropriate agent(s)
3. Coordinates multiple agents for complex queries
4. Synthesizes responses from multiple agents
5. Supports bilingual responses (English/Bengali)

**Intent Detection Keywords:**
```python
{
    "academic": ["cgpa", "gpa", "grade", "result", "course", "syllabus"],
    "library": ["book", "journal", "pdf", "borrow", "library"],
    "career": ["job", "internship", "cv", "resume", "interview", "career"],
    "finance": ["fee", "payment", "waiver", "scholarship", "tuition"],
    "exam": ["exam", "exam schedule", "seating", "seat plan", "midterm"],
    # ... more keywords
}
```

### Master Agent

**File:** `master_agent.py`

Provides advanced orchestration with:
- **Parallel Task Runner:** Execute multiple agents concurrently (max 20)
- **Memory Manager:** Conversation history, episode storage, entity caching
- **Session Management:** Track user sessions, tasks, and results
- **Stats & Monitoring:** Real-time system statistics

**Key Classes:**
```python
class MasterAgent:
    - agents: Dict of available agents with capabilities
    - tools: Dict of available tools
    - intents: Intent patterns for detection
    - process(): Main entry point for processing
    - get_session(): Get session details
    - get_stats(): Get system statistics
```

### Graph Orchestrator

**File:** `graph/orchestrator.py`

Uses LangGraph for workflow orchestration:
```
route → execute → synthesize → END
```

---

## Core Modules

### 1. Configuration (`core/config.py`)

**Settings Class** with environment variables:
```python
# Database
DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/daffodil"
REDIS_URL: str = "redis://localhost:6379"

# AI Providers
OPENAI_API_KEY: str = ""
GEMINI_API_KEY: str = ""
ANTHROPIC_API_KEY: str = ""

# JWT
JWT_SECRET: str = ""
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_MINUTES: int = 30

# OAuth Providers
GOOGLE_CLIENT_ID: str = ""
MICROSOFT_CLIENT_ID: str = ""
GITHUB_CLIENT_ID: str = ""

# Messaging
TELEGRAM_BOT_TOKEN: str = ""
WHATSAPP_PHONE_ID: str = ""

# TTS Settings
GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"
GEMINI_VOICE: str = "Charon"
TTS_PROSODY_RATE: str = "fast"

# RAG
QDRANT_URL: str = "http://localhost:6333"
EMBEDDING_MODEL: str = "text-embedding-3-small"

# University APIs
UNIV_SIS_API_URL: str = "https://sis.daffodiluniversity.edu.bd/api"
UNIV_LIBRARY_API_URL: str = "https://library.daffodiluniversity.edu.bd/api"
UNIV_HR_API_URL: str = "https://hr.daffodiluniversity.edu.bd/api"
UNIV_TRANSPORT_API_URL: str = "https://transport.daffodiluniversity.edu.bd/api"
UNIV_EXAM_API_URL: str = "https://exam.daffodiluniversity.edu.bd/api"

# Feature Flags
USE_MOCK_DATA: bool = True
```

### 2. Security (`core/security.py`)
- JWT token handling
- Password hashing
- OAuth integrations

### 3. Database (`core/database.py`)
- Async SQLAlchemy setup
- Session management

### 4. University Data (`core/university_data.py`)

**UniversityDataConnector** class providing:
- Mock data fallback system
- API integration with university systems
- Functions:
  - `get_student_info(student_id)` - Get student details
  - `get_cgpa(student_id)` - Get CGPA
  - `get_courses(student_id, semester)` - Get courses
  - `get_attendance(student_id)` - Get attendance
  - `search_books(query)` - Search library
  - `get_shuttle_schedule(route)` - Get shuttle times
  - `get_jobs(query)` - Search jobs
  - `get_exam_schedule(student_id)` - Get exam schedule

### 5. Logging (`core/logging.py`)
- Centralized logging configuration

---

## API Routes

### Agents API (`api/agents.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/test-chat` | POST | Test chat with agent |
| `/agents/tools` | GET | List available tools |
| `/agents/tools/execute` | POST | Execute a tool |
| `/agents/vision/analyze` | POST | Analyze image |
| `/agents/chat` | POST | Regular chat |
| `/agents/chat/stream` | POST | Streaming chat (SSE) |
| `/agents/gemini/chat` | POST | Gemini streaming chat |
| `/agents/gemini/chat/simple` | POST | Gemini simple chat |

### Authentication API (`api/auth.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | User login |
| `/auth/google` | GET | Google OAuth |
| `/auth/microsoft` | GET | Microsoft OAuth |
| `/auth/github` | GET | GitHub OAuth |
| `/auth/refresh` | POST | Refresh token |

### Chat API (`api/chat.py`)
- General chat endpoints

### Voice API (`api/voice.py`)
- Voice processing endpoints
- Real-time voice pipeline

### RAG API (`api/rag.py`)
- Document ingestion
- Query handling
- Search endpoints

### Admin API (`api/admin.py`)
- Administrative functions

### Upload API (`api/upload.py`)
- File upload handling

### WebSocket (`api/websocket.py`)
- Real-time WebSocket connections

---

## MCP Tool Server

**File:** `packages/mcp/app/server.py`

### Tools by Category

#### Academic Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_cgpa` | Get current CGPA | `user_id` |
| `get_courses` | Get semester courses | `semester` |
| `get_results` | Get academic results | `user_id`, `semester` |
| `check_prerequisites` | Check course prerequisites | `course_code` |

#### Library Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `search_books` | Search library books | `query`, `limit` |
| `check_book_availability` | Check book availability | `book_title` |
| `get_seat_availability` | Get library seats | - |

#### Campus Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_shuttle_schedule` | Get shuttle schedule | - |
| `get_shuttle_location` | Track shuttle | `route` |
| `get_notices` | Get campus notices | `category` |

#### Career Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `search_jobs` | Search job opportunities | `query`, `limit` |
| `analyze_cv` | Analyze CV/resume | `cv_text` |
| `generate_career_roadmap` | Generate career roadmap | `role`, `current_level` |

#### Finance Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `calculate_tuition` | Calculate tuition | `semester` |
| `check_financial_dues` | Check pending dues | `user_id` |
| `get_scholarships` | Get scholarships | - |

#### Vision Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_screen` | Analyze screen/UI | `image_data` |
| `extract_text_from_image` | OCR text extraction | `image_data` |

#### Memory Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `search_memory` | Search screen/audio memory | `query`, `limit`, `content_type` |

### MCP Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/tools` | GET | List all tools |
| `/tools/execute` | POST | Execute a tool |
| `/tools/{tool_name}` | GET | Get tool info |
| `/tools/cache/invalidate` | POST | Clear cache |
| `/health` | GET | Health check |

---

## Voice & Realtime

### Voice Module (`voice/`)

| File | Description |
|------|-------------|
| `transcript.py` | Speech-to-text processing |
| `tts_providers.py` | Text-to-speech providers |
| `realtime.py` | Real-time voice processing |
| `voice_effects.py` | Voice effects |
| `conversation_memory.py` | Conversation context |
| `call_recorder.py` | Call recording |
| `personality.py` | Voice personality settings |
| `real_time_analytics.py` | Real-time analytics |
| `failover.py` | Failover handling |
| `agent_orchestrator.py` | Voice agent orchestration |
| `microphone.py` | Microphone handling |

### Live Application (`packages/live/`)

- WebRTC server for real-time voice
- End-to-end encryption support
- Nano WebRTC engine integration

---

## Database & Configuration

### Database Models (`models/`)

- User model with roles (student/faculty/admin)
- Student profile, courses, grades
- Sessions and conversations

### Schemas (`schemas/`)

- Pydantic models for request/response validation
- User schemas, agent request/response

### Environment Variables

Create `.env` file from `.env.example`:
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/daffodil

# Redis
REDIS_URL=redis://localhost:6379

# AI Providers
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# JWT
JWT_SECRET=your_jwt_secret

# OAuth (optional)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx

# University APIs (optional)
UNIV_SIS_API_KEY=xxx
```

---

## External Integrations

### University Systems
- **SIS API** - Student Information System
- **Library API** - Library management
- **HR API** - Career services
- **Transport API** - Shuttle tracking
- **Exam API** - Examination system

### Messaging Platforms
- **Telegram Bot** - Telegram integration
- **WhatsApp** - WhatsApp Business API

### AI Providers
- **OpenAI** - GPT-4 for agent processing
- **Google Gemini** - Voice and chat
- **Anthropic** - Claude (optional)

### External Services
- **Qdrant** - Vector database for RAG
- **Screenpipe** - Screen/audio memory

---

## Running the Backend

### Start API Server
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Start MCP Server
```bash
cd packages/mcp
pip install -r requirements.txt
python app/server.py --port 8001
```

### Start Live Server
```bash
cd packages/live
# Build and run WebRTC server
```

### Start Worker
```bash
cd packages/worker
pip install -r requirements.txt
python app/tasks.py
```

---

## Quick Reference

| Component | File/Path | Purpose |
|-----------|-----------|---------|
| Supervisor | `agents/supervisor.py` | Route queries to agents |
| Master Agent | `master_agent.py` | Advanced orchestration |
| Graph Orchestrator | `graph/orchestrator.py` | LangGraph workflow |
| MCP Tools | `mcp/app/server.py` | Tool registry |
| University Data | `core/university_data.py` | Data connector |
| Config | `core/config.py` | Settings |
| API Routes | `api/` | HTTP endpoints |
| Voice Pipeline | `voice/` | Voice processing |

---

*Generated: May 2026*