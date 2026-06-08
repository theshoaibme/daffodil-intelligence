"""Live infrastructure and runtime health probes (no mock placeholders)."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from .config import get_settings

settings = get_settings()
_started_at = time.time()


def uptime_seconds() -> float:
    return round(time.time() - _started_at, 1)


async def _timed(coro) -> tuple[Any, float]:
    t0 = time.perf_counter()
    try:
        result = await coro
        return result, round((time.perf_counter() - t0) * 1000, 1)
    except Exception as e:
        return e, round((time.perf_counter() - t0) * 1000, 1)


async def _check_postgres() -> Dict[str, Any]:
    from .database import is_mock_database, get_engine

    if is_mock_database():
        return {"status": "mock", "mode": "in-memory", "message": "No PostgreSQL connection"}

    engine = get_engine()
    if not engine:
        return {"status": "down", "mode": "unavailable"}

    async def ping():
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")

    result, ms = await _timed(ping())
    if isinstance(result, Exception):
        return {"status": "down", "mode": "postgres", "error": str(result), "latency_ms": ms}
    return {"status": "up", "mode": "postgres", "latency_ms": ms}


async def _check_redis() -> Dict[str, Any]:
    try:
        import redis.asyncio as aioredis
    except ImportError:
        return {"status": "down", "error": "redis package missing"}

    async def ping():
        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        try:
            ok = await client.ping()
            return ok
        finally:
            await client.aclose()

    result, ms = await _timed(ping())
    if isinstance(result, Exception) or not result:
        err = str(result) if isinstance(result, Exception) else "ping failed"
        return {"status": "down", "latency_ms": ms, "error": err}
    return {"status": "up", "latency_ms": ms}


async def _check_minio() -> Dict[str, Any]:
    host = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    scheme = "https" if settings.MINIO_USE_SSL else "http"
    url = f"{scheme}://{host}/minio/health/live"

    async def ping():
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(url)
            r.raise_for_status()

    result, ms = await _timed(ping())
    if isinstance(result, Exception):
        return {"status": "down", "endpoint": host, "latency_ms": ms, "error": str(result)}
    return {"status": "up", "endpoint": host, "latency_ms": ms}


async def _check_qdrant() -> Dict[str, Any]:
    base = settings.QDRANT_URL.rstrip("/")

    async def ping():
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{base}/healthz")
            r.raise_for_status()

    result, ms = await _timed(ping())
    if isinstance(result, Exception):
        return {"status": "down", "url": base, "latency_ms": ms, "error": str(result)}
    return {"status": "up", "url": base, "latency_ms": ms}


def _check_tools() -> Dict[str, Any]:
    from ..tools.registry import get_registry

    try:
        registry = get_registry()
        count = registry.count
        categories = registry.categories()
        return {"status": "up", "count": count, "categories": len(categories)}
    except Exception as e:
        return {"status": "down", "count": 0, "error": str(e)}


def _check_agent_runtime() -> Dict[str, Any]:
    from ..runtime.agent_factory import is_available

    ok = is_available()
    return {
        "status": "up" if ok else "down",
        "engine": "antigravity" if ok else "unavailable",
        "model": settings.ANTIGRAVITY_MODEL,
    }


def _check_telegram() -> Dict[str, Any]:
    from ..integrations.telegram import telegram_bot

    if not telegram_bot.enabled:
        return {"status": "disabled", "enabled": False}
    return {
        "status": "up" if telegram_bot._started else "starting",
        "enabled": True,
    }


def _check_university_data() -> Dict[str, Any]:
    from .university_data import university_data

    mode = "mock" if university_data.use_mock else "live"
    return {"status": "up", "mode": mode}


def _check_ai_providers() -> Dict[str, Any]:
    providers = []
    if settings.OPENAI_API_KEY or settings.GEMINI_API_KEY:
        providers.append("openai/gemini")
    if settings.ANTHROPIC_API_KEY:
        providers.append("anthropic")
    if settings.GEMINI_API_KEY:
        providers.append("gemini")
    return {
        "status": "up" if providers else "degraded",
        "configured": providers,
    }


def _overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
    critical = ("database", "tools", "agent_runtime")
    for key in critical:
        st = checks.get(key, {}).get("status")
        if st in ("down", "unavailable"):
            return "unhealthy"
    optional_down = sum(
        1 for k, v in checks.items()
        if k not in critical and v.get("status") == "down"
    )
    if checks.get("database", {}).get("status") == "mock":
        return "degraded"
    if optional_down > 0:
        return "degraded"
    return "healthy"


async def collect_health() -> Dict[str, Any]:
    db, redis_c, minio, qdrant = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
        _check_minio(),
        _check_qdrant(),
    )
    checks = {
        "database": db,
        "redis": redis_c,
        "minio": minio,
        "qdrant": qdrant,
        "tools": _check_tools(),
        "agent_runtime": _check_agent_runtime(),
        "telegram": _check_telegram(),
        "mcp": {
            "status": "up" if settings.MCP_ENABLED else "disabled",
            "enabled": settings.MCP_ENABLED,
            "transport": settings.MCP_TRANSPORT,
        },
        "university_data": _check_university_data(),
        "ai_providers": _check_ai_providers(),
    }
    return {
        "status": _overall_status(checks),
        "service": "daffodil-intelligence-api",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds(),
        "environment": settings.NODE_ENV,
        "checks": checks,
        "links": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health_ui": "/health/ui",
            "frontend": settings.FRONTEND_PUBLIC_URL,
        },
    }
