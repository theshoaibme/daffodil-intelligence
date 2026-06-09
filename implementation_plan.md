# Daffodil Intelligence — Universal Multi-Agent AI OS

## Overview

**Daffodil Intelligence** is being evolved from a university-specific multi-agent chatbot into a **Universal Multi-Agent AI Operating System** — think JARVIS from Iron Man, but running on your machine. The system will accept any task a computer can do (coding, browsing, file management, automation), coordinate hundreds of specialized agents, control the mouse/keyboard in real-time, see the screen live, and report everything back through a beautiful UI.

**Current state:** FastAPI backend with 18 domain agents (academic, library, career, etc.), a React+Vite frontend with a chat UI (Sidebar, PromptBar, TaskPanel, AiResponseCard), a MasterAgent orchestrator, LangGraph orchestrator stub, and partial MCP client. Workers, SDK, and Services packages are empty stubs.

**Target state:** A fully working, modular, scalable Universal AI Operating System with Computer Use, hundreds of tools, MCP v2, Telegram bot, voice input, and a premium live dashboard.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                             │
│  Chat Dashboard │ Agent Dashboard │ Screen View │ Live Activity Feed        │
│                          http://localhost:3000                              │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │ REST + WebSocket + SSE
┌────────────────────────────▼───────────────────────────────────────────────┐
│                    API GATEWAY  (FastAPI :8000)                             │
│   Auth │ Chat │ Agents │ Voice │ RAG │ Upload │ Admin │ AgentBuilder        │
└──────┬─────────────┬────────────┬────────────┬────────────┬────────────────┘
       │             │            │            │            │
┌──────▼──────┐ ┌───▼──────┐ ┌──▼──────┐ ┌──▼──────┐ ┌──▼──────────┐
│  ORCHESTRATOR│ │ MCP v2   │ │  LIVE   │ │ MESSAGING│ │   WORKER    │
│  (LangGraph) │ │ :8001    │ │ :8003   │ │ :8002    │ │  (Celery)   │
│  Master Agent│ │ 60+ Tools│ │ WS/SSE  │ │ Telegram │ │  Background │
└──────┬───────┘ └──────────┘ └─────────┘ └──────────┘ └─────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│                     AGENT POOL (Python)                                  │
│  Planning │ Computer-Use │ CopyCat │ Coding │ Browser │ File │ Research  │
│  Academic │ Library │ Career │ Finance │ Vision │ Voice │ Wellness …    │
└──────────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│                  TOOL LAYER (60+ Tools)                                  │
│  Mouse/Keyboard │ Screen Capture │ Browser │ File System │ Shell        │
│  VS Code │ Git │ Web Search │ PDF │ Image │ Audio │ API Calls           │
└──────────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                              │
│  PostgreSQL (users, sessions, history) │ Redis (cache, pub/sub)         │
│  Qdrant (vector/RAG) │ Local file store (recordings, uploads)           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Open Questions

> [!IMPORTANT]
> **Please review before execution starts:**

1. **Computer Use scope** — Should mouse/keyboard control work on the *same* machine as the server, or should it support remote machines via VNC/RDP as well?
2. **CopyCat agent** — Should recorded macro actions be stored permanently (database) or only in-session (memory)?
3. **LLM provider priority** — Current setup uses OpenAI/Gemini. Should Computer Use vision use Gemini 2.0 Flash (which supports it natively) or a dedicated vision model?
4. **Screen capture method** — `mss` library (fast, cross-platform) vs `pyautogui` screenshot vs Gemini native screen share. Which is preferred?
5. **Agent count target** — "Hundreds of agents" — do you mean hundreds of *concurrent task instances* of a few agent types, or hundreds of distinct *specialized agent classes*?
6. **Telegram bot** — Should the Telegram interface be read-only (receive commands) or fully interactive (receive files, images, voice notes)?

---

## Proposed Changes

### Phase 1 — Backend Foundation (Week 1)

---

#### MODIFY [master_agent.py](file:///home/kali/Desktop/daffodil-intelligence/apps/api/app/master_agent.py)

The current `_execute_agent` and `_execute_tool` methods are stubs (`await asyncio.sleep(0.05)`). Replace with real LLM-backed dispatch that actually calls the supervisor + agent pool and returns real responses.

**Key changes:**
- Wire `_execute_agent` → `SupervisorAgent.process()` with real LLM calls
- Wire `_execute_tool` → MCP tool executor
- Add `CopyCatAgent` and `ComputerUseAgent` to the agent registry
- Increase concurrent capacity from 20 → 100 (configurable via env)
- Add priority queue with Redis-backed Celery for long-running tasks

---

#### [NEW] `apps/api/app/computer_use/` — Computer Use Module

New top-level module inside the API app for all computer interaction:

```
apps/api/app/computer_use/
├── __init__.py
├── screen.py          # Screen capture, streaming, region crop
├── mouse.py           # Mouse move, click, scroll, drag
├── keyboard.py        # Type, hotkeys, keypress
├── recorder.py        # Record user actions → replay script
├── replayer.py        # Replay recorded actions with optional AI improvisation
└── overlay.py         # Agent cursor overlay (virtual cursor with name tag)
```

**`screen.py`** — Uses `mss` for fast frame capture, streams JPEG frames over WebSocket at configurable FPS (default 5fps). Supports region-of-interest cropping for targeted vision analysis.

**`mouse.py`** — Uses `pyautogui` + `pynput` for cross-platform mouse control. Exposes `move(x,y)`, `click(x,y,button)`, `scroll(x,y,dy)`, `drag(x1,y1,x2,y2)`.

**`keyboard.py`** — Uses `pynput` for typing text and sending hotkeys. Exposes `type_text(text, delay)`, `hotkey(*keys)`, `keypress(key)`.

**`recorder.py`** — Listens to all mouse/keyboard events via `pynput` listeners, stores them as a timestamped action list in memory. Can export to JSON.

**`replayer.py`** — Takes a recorded action list and replays it, optionally with an AI layer that can adapt clicks to the current screen state using vision.

**`overlay.py`** — Draws a named "agent cursor" on screen using a transparent Tkinter overlay window, so the user can see where the agent is clicking.

---

#### [NEW] `apps/api/app/agents/computer_use.py`

New agent class that wraps the computer use module and exposes it to the orchestrator as a standard agent.

```python
class ComputerUseAgent(BaseAgent):
    name = "Computer Use Agent"
    description = "Controls mouse, keyboard, and screen on the host machine"
    tools = ["take_screenshot", "mouse_move", "mouse_click", "keyboard_type",
             "keyboard_hotkey", "scroll", "get_screen_text", "find_element"]
```

Integrates with Gemini Vision API to analyze screenshots and decide where to click when given natural language instructions like "click the login button".

---

#### [NEW] `apps/api/app/agents/copycat.py`

The CopyCat agent records everything the user does and can replay it on command.

```python
class CopyCatAgent(BaseAgent):
    name = "CopyCat Agent"
    description = "Records user actions and replays them autonomously"
    tools = ["start_recording", "stop_recording", "replay_last", "replay_named",
             "save_recording", "list_recordings"]
```

**Behavior:**
- `start_recording` → starts `pynput` listener, captures all events
- `stop_recording` → stops listener, stores recording in `recordings/` directory
- `replay_last` → replays last recording with `replayer.py`
- The agent's own "cursor" is shown as a separate overlay so user can distinguish it from their own cursor

---

#### [NEW] `apps/api/app/tools/` — Modular Tool Registry

Replace the current single `mcp/client.py` tool registry with a proper modular tool system:

```
apps/api/app/tools/
├── __init__.py           # auto-discovers and registers all tools
├── base.py               # BaseTool class with schema validation
├── registry.py           # ToolRegistry singleton
├── academic/
│   ├── cgpa.py
│   ├── courses.py
│   └── results.py
├── browser/
│   ├── open_url.py
│   ├── web_search.py
│   └── scrape_page.py
├── computer/
│   ├── screenshot.py
│   ├── mouse_control.py
│   └── keyboard_control.py
├── file/
│   ├── read_file.py
│   ├── write_file.py
│   ├── list_dir.py
│   └── delete_file.py
├── shell/
│   ├── run_command.py
│   └── run_python.py
├── code/
│   ├── vscode_open.py
│   ├── git_commit.py
│   └── lint_code.py
├── communication/
│   ├── send_telegram.py
│   └── send_email.py
└── memory/
    ├── store_note.py
    └── recall_notes.py
```

**`base.py`** — `BaseTool` defines `name`, `description`, `parameters` (JSON Schema), and `execute(**kwargs) → dict`. Enforces typed input/output.

**`registry.py`** — `ToolRegistry` auto-discovers all `BaseTool` subclasses via Python's importlib, builds the tool manifest for MCP v2 exposure.

---

#### MODIFY `apps/api/app/mcp/client.py` → `apps/api/app/mcp/`

Upgrade the single-file MCP client to a full MCP v2 server + client package:

```
apps/api/app/mcp/
├── __init__.py
├── server.py        # FastMCP v2 server that exposes all registered tools
├── client.py        # Async client for the MCP server
├── protocol.py      # MCP v2 protocol models (Pydantic)
└── middleware.py    # Auth, rate limiting for MCP
```

**MCP Server** uses the `mcp` Python SDK (`pip install mcp[cli]`). Each registered tool in `ToolRegistry` is automatically exposed as an MCP tool.

---

#### [NEW] `apps/api/app/workers/` — Celery Task Workers

```
apps/api/app/workers/
├── __init__.py
├── celery_app.py     # Celery app configuration
├── agent_tasks.py    # Long-running agent task definitions
├── computer_tasks.py # Background computer use tasks
└── beat_schedule.py  # Periodic tasks (cron-style)
```

Celery workers enable:
- Non-blocking long-running agent tasks
- Scheduled/recurring automation (e.g., "every morning, check my email")
- Distributed scale-out (add more workers as needed)

---

#### MODIFY `apps/api/app/core/config.py`

Add new settings for computer use, MCP v2, and Celery:

```python
# Computer Use
COMPUTER_USE_ENABLED: bool = True
SCREEN_CAPTURE_FPS: int = 5
AGENT_CURSOR_VISIBLE: bool = True

# MCP v2
MCP_SERVER_PORT: int = 8001
MCP_AUTH_TOKEN: str = ""

# Celery
CELERY_BROKER_URL: str = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

# Computer Use Security
COMPUTER_USE_ALLOWED_DOMAINS: str = "*"  # restrict URLs agent can visit
COMPUTER_USE_SANDBOX: bool = False  # run in Docker sandbox
```

---

#### [NEW] `apps/api/app/agents/planning.py`

A meta-agent that takes a high-level goal and decomposes it into a step-by-step plan, then delegates each step to specialized sub-agents. Uses LangGraph for the planning loop.

```python
class PlanningAgent(BaseAgent):
    name = "Planning Agent"
    description = "Decomposes complex goals into multi-step execution plans"
```

**Planning loop:**
1. Receive goal
2. Generate plan as ordered list of sub-tasks
3. For each sub-task → select best agent + tools
4. Execute sub-tasks (in parallel where independent, sequential where dependent)
5. Aggregate results → final response

---

#### MODIFY `apps/api/app/graph/orchestrator.py`

Currently a stub. Build a real LangGraph orchestration flow:

```python
# Node definitions
START → intent_classifier → parallel_agent_executor → synthesizer → END
                          ↓
                    [planning_node] (for complex multi-step tasks)
```

---

### Phase 2 — API Endpoints (Week 1-2)

---

#### [NEW] `apps/api/app/api/computer_use.py`

```
POST /api/computer/screenshot        # Capture current screen
POST /api/computer/mouse/move        # Move agent cursor
POST /api/computer/mouse/click       # Click at position
POST /api/computer/keyboard/type     # Type text
POST /api/computer/keyboard/hotkey   # Send hotkey
WS   /api/computer/screen-stream     # Live screen stream (WebSocket)
POST /api/computer/record/start      # Start recording
POST /api/computer/record/stop       # Stop recording
GET  /api/computer/record/list       # List saved recordings
POST /api/computer/record/replay     # Replay a recording
```

---

#### MODIFY `apps/api/app/api/agents.py`

Add endpoints for dynamic agent creation and management:

```
GET  /api/agents                     # List all available agents (static + dynamic)
POST /api/agents/create              # Create a new custom agent with tools/prompt
GET  /api/agents/{id}               # Get agent details, capabilities, status
POST /api/agents/{id}/invoke         # Directly invoke a specific agent
GET  /api/agents/sessions            # Get all active agent sessions
GET  /api/agents/sessions/{id}       # Get session details with task breakdown
```

---

#### MODIFY `apps/api/app/api/websocket.py`

Upgrade the WebSocket handler to support real-time streaming of:
- Agent task status updates
- Screen capture frames (binary WebSocket messages)
- Typing indicators and agent action narration

---

### Phase 3 — Frontend Upgrade (Week 2)

---

#### MODIFY `apps/web/src/App.tsx`

Add new routes:

```tsx
/                  → ChatDashboard (existing, enhanced)
/agents            → AgentDashboard (NEW — shows all agents, their status, create custom)
/computer          → ComputerView  (NEW — live screen, agent cursor overlay, action log)
/recordings        → RecordingsPage (NEW — list, play, manage recorded macros)
/model             → ModelManagementPage (existing)
/live              → LiveVoicePage (existing)
```

---

#### [NEW] `apps/web/src/components/layout/AgentDashboard/`

A full-page view showing:
- Grid of all available agents with status indicators (idle / thinking / executing)
- Agent detail panel: current task, capabilities, tools used, performance metrics
- "Create Custom Agent" form: name, system prompt, tools selector, icon picker
- Real-time agent activity feed (WebSocket-powered)

---

#### [NEW] `apps/web/src/components/layout/ComputerView/`

The most visually impressive new feature:

```
ComputerView/
├── index.tsx          # Main page layout
├── ScreenViewer.tsx   # Live screen stream display (canvas element, WebSocket binary)
├── AgentCursor.tsx    # Overlay showing agent cursor position in real-time
├── ActionLog.tsx      # Scrolling log of every mouse/keyboard action
├── ControlPanel.tsx   # Buttons: Start Recording, Stop, Replay, Take Screenshot
└── MacroEditor.tsx    # Edit and manage recorded macro scripts
```

**`ScreenViewer.tsx`** — Connects to `/api/computer/screen-stream` WebSocket, decodes JPEG frames, renders on `<canvas>` at 5-10fps. Overlays agent cursor as a glowing dot with label.

**`ActionLog.tsx`** — Shows live stream of agent actions: `🖱️ Clicked (450, 320)`, `⌨️ Typed "hello world"`, `📸 Screenshot taken`, etc.

---

#### MODIFY `apps/web/src/components/layout/TaskPanel/`

Upgrade the TaskPanel to show:
- Hierarchical task tree (plan → sub-tasks → tools)
- Real-time status of each sub-task (pending → running → done)
- Expandable task details with timing and result preview
- Progress bar for multi-step plans

---

#### MODIFY `apps/web/src/components/layout/PromptBar/`

Add input modalities:
- **Voice input** button: hold to record, uses Whisper API or Web Speech API
- **Screen share** button: triggers screen capture, attaches frame to next prompt
- **File attach**: already partially implemented, ensure it works with vision agent
- **Agent selector**: chip picker to force-route to a specific agent

---

#### [NEW] `apps/web/src/components/layout/Sidebar/` — Conversation History

Currently the sidebar likely doesn't persist history. Add:
- Saved conversation sessions (fetched from PostgreSQL)
- Starred/pinned conversations
- Search through past conversations

---

### Phase 4 — Messaging Integration (Week 2-3)

---

#### MODIFY `apps/api/app/messaging_gateway.py`

Currently a stub router. Implement full Telegram bot integration:

- `/start` → Welcome message, show capabilities
- Any text message → routes through `SupervisorAgent`
- Voice messages → transcribe via Whisper, then route
- Photos → route to Vision agent
- `/record` → trigger CopyCat recording
- `/replay` → replay last recording
- Bot replies with formatted text + inline keyboard buttons

Use `python-telegram-bot` v21 (async).

---

### Phase 5 — Sandboxing & Security (Week 3)

---

#### [NEW] `apps/api/app/sandbox/`

```
apps/api/app/sandbox/
├── __init__.py
├── docker_sandbox.py   # Run agent commands inside Docker container
├── process_jail.py     # Unix process isolation with resource limits
└── network_policy.py   # Allow/block specific domains for computer use
```

**Docker sandbox** — For shell command execution and untrusted code, spin up a lightweight Docker container (`python:3.12-slim`), execute the command, capture output, destroy container. Prevents agents from damaging the host system.

**Network policy** — Configurable domain allowlist/blocklist for browser tool. Prevents data exfiltration.

---

### Phase 6 — Scalability & Performance (Week 3-4)

---

#### MODIFY `apps/api/app/core/database.py`

Ensure proper async connection pooling for high-concurrency scenarios. Add connection pool sizing configuration.

#### [NEW] `apps/api/app/services/agent_pool.py`

Agent instance pool management. Currently agents are instantiated as singletons in `AGENT_MAP`. For hundreds of concurrent tasks, implement a pool that can spawn multiple instances of the same agent type and route tasks to idle instances.

#### [NEW] `packages/sdk/`

TypeScript SDK for frontend consumption:
```
packages/sdk/
├── src/
│   ├── client.ts          # API client with auth
│   ├── agents.ts          # Agent management
│   ├── computer.ts        # Computer use (screen stream, mouse/keyboard)
│   ├── websocket.ts       # Real-time subscriptions
│   └── types.ts           # Shared TypeScript types
└── package.json
```

---

## File Structure (Target)

```
daffodil-intelligence/
├── apps/
│   ├── api/
│   │   └── app/
│   │       ├── agents/
│   │       │   ├── base.py              [EXISTS]
│   │       │   ├── supervisor.py        [EXISTS — enhance]
│   │       │   ├── academic.py          [EXISTS]
│   │       │   ├── ...17 others...      [EXISTS]
│   │       │   ├── computer_use.py      [NEW]
│   │       │   ├── copycat.py           [NEW]
│   │       │   └── planning.py          [NEW]
│   │       ├── computer_use/            [NEW MODULE]
│   │       │   ├── screen.py
│   │       │   ├── mouse.py
│   │       │   ├── keyboard.py
│   │       │   ├── recorder.py
│   │       │   ├── replayer.py
│   │       │   └── overlay.py
│   │       ├── tools/                   [NEW MODULE]
│   │       │   ├── base.py
│   │       │   ├── registry.py
│   │       │   ├── academic/
│   │       │   ├── browser/
│   │       │   ├── computer/
│   │       │   ├── file/
│   │       │   ├── shell/
│   │       │   ├── code/
│   │       │   ├── communication/
│   │       │   └── memory/
│   │       ├── mcp/                     [UPGRADE to v2]
│   │       │   ├── server.py
│   │       │   ├── client.py
│   │       │   ├── protocol.py
│   │       │   └── middleware.py
│   │       ├── workers/                 [NEW MODULE]
│   │       │   ├── celery_app.py
│   │       │   ├── agent_tasks.py
│   │       │   ├── computer_tasks.py
│   │       │   └── beat_schedule.py
│   │       ├── sandbox/                 [NEW MODULE]
│   │       │   ├── docker_sandbox.py
│   │       │   ├── process_jail.py
│   │       │   └── network_policy.py
│   │       ├── services/
│   │       │   └── agent_pool.py        [NEW]
│   │       ├── api/
│   │       │   ├── computer_use.py      [NEW]
│   │       │   └── agents.py            [ENHANCE]
│   │       ├── graph/
│   │       │   └── orchestrator.py      [ENHANCE]
│   │       ├── core/
│   │       │   └── config.py            [ENHANCE]
│   │       ├── master_agent.py          [ENHANCE]
│   │       └── main.py                  [ENHANCE]
│   └── web/
│       └── src/
│           ├── App.tsx                  [ENHANCE — new routes]
│           ├── components/layout/
│           │   ├── AgentDashboard/      [NEW]
│           │   ├── ComputerView/        [NEW]
│           │   ├── TaskPanel/           [ENHANCE]
│           │   ├── PromptBar/           [ENHANCE]
│           │   └── Sidebar/             [ENHANCE]
│           └── hooks/
│               ├── useChat.ts           [EXISTS]
│               ├── useComputerStream.ts [NEW]
│               └── useAgents.ts        [NEW]
├── packages/
│   └── sdk/                            [IMPLEMENT — currently stub]
└── .env.example                        [UPDATE with new vars]
```

---

## New Python Dependencies

```txt
# Computer Use
mss>=9.0.0              # Fast screen capture
pyautogui>=0.9.54       # Mouse + keyboard control
pynput>=1.7.6           # Event recording (mouse/keyboard listener)
pillow>=10.0.0          # Image processing for screenshots

# MCP v2
mcp[cli]>=1.0.0         # Model Context Protocol SDK

# Messaging
python-telegram-bot>=21.0.0  # Async Telegram bot

# Workers
celery>=5.3.6           # Already in requirements.txt ✓
flower>=2.0.0           # Celery monitoring UI

# Browser Control
playwright>=1.40.0      # Browser automation (alternative to selenium)

# Security / Sandbox
docker>=7.0.0           # Docker SDK for sandbox
```

---

## Verification Plan

### Automated Tests

```bash
# Backend unit tests
cd apps/api && python -m pytest test_agents.py -v
cd apps/api && python -m pytest test_auth.py -v

# JARVIS mode integration test (already exists)
cd /home/kali/Desktop/daffodil-intelligence
python test_jarvis_mode.py

# New computer use test
cd apps/api && python -m pytest tests/test_computer_use.py -v

# Full system smoke test
pnpm dev  # start all services
curl http://localhost:8000/health
```

### Manual Verification

1. **Agent Dashboard** — Open `/agents` in browser, verify all 18+ agents show with real-time status
2. **Computer View** — Open `/computer`, verify live screen stream appears, click a button via the UI and see the agent cursor move to it
3. **CopyCat** — Record a simple action (open Notepad, type text), replay it via UI
4. **Telegram** — Send a message to the bot, verify it responds correctly
5. **Voice Input** — Hold the mic button in PromptBar, speak a query, verify transcription and response
6. **Parallel Agents** — Send a complex query, verify TaskPanel shows multiple agents executing simultaneously with correct timing

---

## Implementation Priority Order

| Priority | Component | Reason |
|---|---|---|
| 🔴 P0 | `computer_use/` module | Core new capability, everything depends on it |
| 🔴 P0 | `tools/` modular registry | Foundation for all agent capabilities |
| 🔴 P0 | `agents/computer_use.py` + `copycat.py` | New agents |
| 🔴 P0 | `planning.py` agent | Required for complex task coordination |
| 🟠 P1 | MCP v2 upgrade | Real tool execution currently missing |
| 🟠 P1 | `master_agent.py` real dispatch | Currently returns fake mock data |
| 🟠 P1 | `ComputerView` frontend | Showpiece feature |
| 🟠 P1 | `AgentDashboard` frontend | Required for agent management |
| 🟡 P2 | Telegram bot | Messaging integration |
| 🟡 P2 | Workers / Celery tasks | Long-running task support |
| 🟡 P2 | Sandbox security | Safety for production use |
| 🟢 P3 | TypeScript SDK | Developer ergonomics |
| 🟢 P3 | Conversation history in Sidebar | UX polish |
