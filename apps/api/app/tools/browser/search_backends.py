"""Shared search backends for browser and research tools."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ...core.config import get_settings

logger = logging.getLogger(__name__)


async def search_google_cse(query: str, max_results: int) -> list[dict[str, Any]] | None:
    settings = get_settings()
    api_key = getattr(settings, "GOOGLE_SEARCH_API_KEY", "") or ""
    cse_id = getattr(settings, "GOOGLE_CSE_ID", "") or ""
    if not api_key or not cse_id:
        return None

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cse_id,
                "q": query,
                "num": min(max_results, 10),
            },
        )
        if response.status_code != 200:
            logger.warning("Google CSE error %s: %s", response.status_code, response.text[:200])
            return None

        items = response.json().get("items") or []
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "google_cse",
            }
            for item in items[:max_results]
        ]


async def search_serper(query: str, max_results: int) -> list[dict[str, Any]] | None:
    settings = get_settings()
    api_key = getattr(settings, "SERPER_API_KEY", "") or ""
    if not api_key:
        return None

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": min(max_results, 10)},
        )
        if response.status_code != 200:
            logger.warning("Serper error %s: %s", response.status_code, response.text[:200])
            return None

        organic = response.json().get("organic") or []
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "serper",
            }
            for item in organic[:max_results]
        ]


async def search_gemini_grounding(query: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=(
                f"Research this topic using Google Search and return factual findings: {query}"
            ),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        text = getattr(response, "text", None) or ""
        citations: list[dict[str, str]] = []
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            metadata = getattr(candidate, "grounding_metadata", None)
            if not metadata:
                continue
            for chunk in getattr(metadata, "grounding_chunks", None) or []:
                web = getattr(chunk, "web", None)
                if web:
                    citations.append(
                        {
                            "title": getattr(web, "title", "") or "",
                            "url": getattr(web, "uri", "") or "",
                        }
                    )

        if not text and not citations:
            return None
        return {"answer": text, "citations": citations, "source": "gemini_grounding"}
    except Exception as e:
        logger.warning("Gemini grounding search failed: %s", e)
        return None


async def search_duckduckgo(query: str, max_results: int) -> list[dict[str, Any]]:
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            rows = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": row.get("title", ""),
                "url": row.get("href", ""),
                "snippet": row.get("body", ""),
                "source": "duckduckgo",
            }
            for row in rows
        ]
    except ImportError:
        pass
    except Exception as e:
        logger.warning("duckduckgo-search failed: %s", e)

    # Fallback: DuckDuckGo instant-answer API (limited SERP)
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": "1", "no_html": "1"},
            headers={"User-Agent": "DaffodilIntelligence/1.0"},
        )
        if response.status_code != 200:
            return []

        data = response.json()
        results: list[dict[str, Any]] = []
        if data.get("Abstract"):
            results.append(
                {
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["Abstract"],
                    "source": "duckduckgo_instant",
                }
            )
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo_instant",
                    }
                )
        return results[:max_results]


async def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Try search backends in priority order and return unified payload."""
    for backend in (search_google_cse, search_serper):
        results = await backend(query, max_results)
        if results:
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "backend": results[0].get("source", "unknown"),
            }

    grounding = await search_gemini_grounding(query)
    if grounding:
        citations = grounding.get("citations") or []
        results = [
            {
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "snippet": grounding.get("answer", "")[:500],
                "source": "gemini_grounding",
            }
            for c in citations
        ]
        if not results and grounding.get("answer"):
            results = [
                {
                    "title": query,
                    "url": "",
                    "snippet": grounding["answer"],
                    "source": "gemini_grounding",
                }
            ]
        return {
            "query": query,
            "results": results[:max_results],
            "count": len(results[:max_results]),
            "backend": "gemini_grounding",
            "synthesis": grounding.get("answer"),
        }

    results = await search_duckduckgo(query, max_results)
    return {
        "query": query,
        "results": results,
        "count": len(results),
        "backend": results[0].get("source", "duckduckgo") if results else "none",
    }
