"""Deep research orchestration — multi-query search plus page fetching."""

from __future__ import annotations

import re
from typing import Any

from ..base import BaseTool, ToolParameter, ToolResult
from .search import FetchURLTool
from .search_backends import web_search


def _split_subqueries(query: str, max_queries: int) -> list[str]:
    parts = [p.strip() for p in re.split(r"[;\n]|(?:\band\b)", query, flags=re.I) if p.strip()]
    unique: list[str] = []
    for part in parts:
        if part not in unique:
            unique.append(part)
    if not unique:
        return [query]
    return unique[:max_queries]


class DeepResearchTool(BaseTool):
    name = "deep_research"
    description = (
        "Run multi-step web research: decomposes the query, searches the web, "
        "fetches top pages, and returns structured findings for synthesis."
    )
    category = "research"
    parameters = [
        ToolParameter(name="query", type="string", description="Research question or topic"),
        ToolParameter(
            name="max_sources",
            type="integer",
            description="Max URLs to fetch per sub-query (default 3)",
            required=False,
            default=3,
        ),
        ToolParameter(
            name="max_subqueries",
            type="integer",
            description="Max search sub-queries to run (default 3)",
            required=False,
            default=3,
        ),
    ]

    async def execute(
        self,
        query: str,
        max_sources: int = 3,
        max_subqueries: int = 3,
    ) -> ToolResult:
        try:
            subqueries = _split_subqueries(query, max_subqueries)
            fetcher = FetchURLTool()
            searches: list[dict[str, Any]] = []
            pages: list[dict[str, Any]] = []
            seen_urls: set[str] = set()

            for subq in subqueries:
                search_payload = await web_search(subq, max_results=max_sources)
                searches.append(search_payload)

                for hit in search_payload.get("results") or []:
                    url = (hit.get("url") or "").strip()
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    fetched = await fetcher.execute(url=url, max_chars=4000)
                    if fetched.success:
                        pages.append(
                            {
                                "url": url,
                                "title": hit.get("title", ""),
                                "subquery": subq,
                                "content": fetched.data.get("content", ""),
                                "status_code": fetched.data.get("status_code"),
                            }
                        )
                    if len(pages) >= max_sources * len(subqueries):
                        break

            return self.ok(
                {
                    "query": query,
                    "subqueries": subqueries,
                    "searches": searches,
                    "pages": pages,
                    "source_count": len(pages),
                }
            )
        except Exception as e:
            return self.fail(f"Deep research failed: {e}")
