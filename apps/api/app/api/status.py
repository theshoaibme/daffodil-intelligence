"""System status and service catalog."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..agents.registry import AGENT_MAP
from ..core.models_catalog import MODEL_CATALOG, dashboard_models, resolve_model_name

router = APIRouter(tags=["system"])

_AGENT_CATEGORIES = {
    "academic": "university",
    "library": "university",
    "campus": "university",
    "career": "university",
    "wellness": "university",
    "finance": "university",
    "exam": "university",
    "hostel": "university",
    "transport": "university",
    "event": "university",
    "complaint": "university",
    "fee": "university",
    "coding": "productivity",
    "research": "productivity",
    "writing": "productivity",
    "tasks": "productivity",
    "notification": "productivity",
    "vision": "ai",
    "voice": "ai",
    "computer_use": "computer",
    "copycat": "computer",
    "planning": "orchestration",
    "routine": "university",
    "general": "general",
}


def _agent_catalog() -> list[dict]:
    return [
        {
            "id": aid,
            "name": agent.name,
            "description": agent.description,
            "tools": agent.tools,
            "category": _AGENT_CATEGORIES.get(aid, "general"),
            "status": "active",
        }
        for aid, agent in sorted(AGENT_MAP.items())
    ]


@router.get("/")
async def root():
    return RedirectResponse(url="/health", status_code=302)


@router.get("/api/agents/list", deprecated=True)
async def list_agents():
    """Deprecated — use GET /api/agents/hub instead."""
    return {"agents": _agent_catalog(), "count": len(AGENT_MAP)}


@router.get("/api/models/list")
async def list_models():
    return {
        "models": MODEL_CATALOG,
        "dashboard_models": dashboard_models(),
        "count": len(MODEL_CATALOG),
    }


@router.get("/api/system/mcp")
async def mcp_status():
    """MCP integration status for the chat tools menu."""
    from ..core.health_checks import _check_mcp

    return _check_mcp()


@router.get("/api/system/runtime")
async def system_runtime():
    """Live runtime snapshot for dashboard simulation (model, engine, integrations)."""
    from ..core.health_checks import collect_health

    health = await collect_health()
    checks = health.get("checks", {})
    agent_runtime = checks.get("agent_runtime", {})
    tools = checks.get("tools", {})
    active_model = agent_runtime.get("model", "gemini-2.0-flash")
    return {
        "status": health.get("status"),
        "engine": agent_runtime.get("engine", "unavailable"),
        "model": active_model,
        "model_name": resolve_model_name(active_model),
        "models": dashboard_models(),
        "runtime_status": agent_runtime.get("status", "down"),
        "tools_count": tools.get("count", 0),
        "telegram": checks.get("telegram", {}),
        "mcp": checks.get("mcp", {}),
        "agents_count": len(AGENT_MAP),
    }


@router.get("/api/system/flow")
async def system_flow(limit: int = 20):
    """Recent runtime turn traces across chats for the live agent-flow view."""
    from ..runtime.trace import trace_recorder

    return {"turns": trace_recorder.all_recent(limit=limit)}


@router.get("/health", response_class=HTMLResponse)
async def health_page(request: Request):
    now = datetime.now(timezone.utc)
    base = str(request.base_url).rstrip("/")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Daffodil Intelligence — Health</title>
  <style>
    :root {{
      --bg: #fbf8ff; --surface: #fff; --text: #1a1b24; --muted: #64748b;
      --border: #e2e1ef; --primary: #4259ff; --ok: #16a34a;
    }}
    * {{ box-sizing: border-box; margin: 0; }}
    body {{
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: var(--bg); color: var(--text); min-height: 100vh;
      display: flex; align-items: center; justify-content: center; padding: 24px;
    }}
    .panel {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 20px; padding: 32px; max-width: 420px; width: 100%;
      text-align: center;
    }}
    h1 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 8px; }}
    .status {{
      display: inline-flex; align-items: center; gap: 8px;
      color: var(--ok); font-weight: 600; font-size: 1.1rem; margin: 16px 0;
    }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--ok); }}
    .message {{ color: var(--muted); margin-bottom: 8px; }}
    .time {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 24px; }}
    .links {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }}
    .links a {{
      text-decoration: none; color: var(--primary); font-size: 0.9rem;
      padding: 8px 14px; border-radius: 999px; border: 1px solid var(--border);
    }}
    .links a:hover {{ border-color: var(--primary); }}
  </style>
</head>
<body>
  <div class="panel">
    <h1>Daffodil Intelligence</h1>
    <div class="status"><span class="dot"></span> healthy</div>
    <p class="message">Server is healthy</p>
    <p class="time">{time_str}</p>
    <nav class="links">
      <a href="{base}/docs">API Docs</a>
      <a href="{base}/openapi.json">OpenAPI</a>
    </nav>
  </div>
</body>
</html>"""
