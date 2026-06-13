"""Deep research orchestration — multi-query search plus page fetching."""

from __future__ import annotations

import asyncio
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
            url_lock = asyncio.Lock()

            from ...runtime.task_events import emit_task, new_task_id
            from ...runtime.task_titles import short_title

            group_id = new_task_id("research")
            research_task = emit_task(
                kind="tool",
                name="deep_research",
                title=short_title("Deep research"),
                status="active",
                agent_id="research",
                depth=1,
            )
            parent_id = research_task["task_id"]

            async def run_subquery(subq: str) -> dict[str, Any]:
                sub_task = emit_task(
                    parent_id=parent_id,
                    kind="plan",
                    name="subquery",
                    title=short_title(f"Search {subq}"),
                    status="active",
                    parallel_group=group_id,
                    agent_id="research",
                    depth=2,
                )
                search_payload = await web_search(subq, max_results=max_sources)
                sub_pages: list[dict[str, Any]] = []

                for hit in search_payload.get("results") or []:
                    url = (hit.get("url") or "").strip()
                    if not url:
                        continue
                    async with url_lock:
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                    fetched = await fetcher.execute(url=url, max_chars=4000)
                    if fetched.success:
                        sub_pages.append(
                            {
                                "url": url,
                                "title": hit.get("title", ""),
                                "subquery": subq,
                                "content": fetched.data.get("content", ""),
                                "status_code": fetched.data.get("status_code"),
                            }
                        )
                    if len(sub_pages) >= max_sources:
                        break

                emit_task(
                    task_id=sub_task["task_id"],
                    parent_id=parent_id,
                    kind="plan",
                    name="subquery",
                    title=short_title(f"Search {subq}"),
                    status="success",
                    parallel_group=group_id,
                    agent_id="research",
                    depth=2,
                )
                return {"search": search_payload, "pages": sub_pages}

            sub_results = await asyncio.gather(*(run_subquery(q) for q in subqueries))
            for item in sub_results:
                searches.append(item["search"])
                pages.extend(item["pages"])

            emit_task(
                task_id=parent_id,
                kind="tool",
                name="deep_research",
                title=short_title("Deep research"),
                status="success",
                agent_id="research",
                depth=1,
            )
            return self.ok(
                {
                    "query": query,
                    "subqueries": subqueries,
                    "searches": searches,
                    "pages": pages,
                    "source_count": len(pages),
                    "parallel_group": group_id,
                }
            )
        except Exception as e:
            return self.fail(f"Deep research failed: {e}")
