"""Academic research tools — Semantic Scholar paper search and citations."""

from __future__ import annotations

from typing import Any

import httpx

from ..base import BaseTool, ToolParameter, ToolResult

_S2_BASE = "https://api.semanticscholar.org/graph/v1"


async def _s2_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.get(
            f"{_S2_BASE}{path}",
            params=params,
            headers={"User-Agent": "DaffodilIntelligence/1.0"},
        )
        response.raise_for_status()
        return response.json()


class SearchPapersTool(BaseTool):
    name = "search_papers"
    description = "Search academic papers via Semantic Scholar (title, authors, year, citations)."
    category = "research"
    parameters = [
        ToolParameter(name="query", type="string", description="Paper topic or keywords"),
        ToolParameter(
            name="limit",
            type="integer",
            description="Max papers to return (default 8)",
            required=False,
            default=8,
        ),
        ToolParameter(
            name="year",
            type="string",
            description="Optional year filter e.g. '2024' or '2020-2024'",
            required=False,
        ),
    ]

    async def execute(self, query: str, limit: int = 8, year: str = None) -> ToolResult:
        try:
            params: dict[str, Any] = {
                "query": query,
                "limit": min(limit, 20),
                "fields": "title,year,authors,citationCount,url,externalIds,abstract",
            }
            if year:
                params["year"] = year

            data = await _s2_get("/paper/search", params)
            papers = []
            for item in data.get("data") or []:
                authors = [a.get("name", "") for a in item.get("authors") or []]
                papers.append(
                    {
                        "paper_id": item.get("paperId"),
                        "title": item.get("title"),
                        "year": item.get("year"),
                        "authors": authors,
                        "citations": item.get("citationCount", 0),
                        "url": item.get("url"),
                        "doi": (item.get("externalIds") or {}).get("DOI"),
                        "abstract": (item.get("abstract") or "")[:500],
                    }
                )
            return self.ok({"query": query, "papers": papers, "count": len(papers)})
        except Exception as e:
            return self.fail(f"Paper search failed: {e}")


class GetCitationsTool(BaseTool):
    name = "get_citations"
    description = "Get citation count and references for a paper by Semantic Scholar paper ID or DOI."
    category = "research"
    parameters = [
        ToolParameter(
            name="paper_id",
            type="string",
            description="Semantic Scholar paper ID or DOI:... identifier",
        ),
        ToolParameter(
            name="include_references",
            type="boolean",
            description="Include reference list (default false)",
            required=False,
            default=False,
        ),
    ]

    async def execute(self, paper_id: str, include_references: bool = False) -> ToolResult:
        try:
            pid = paper_id.strip()
            if pid.lower().startswith("doi:"):
                pid = f"DOI:{pid[4:].strip()}"

            fields = "title,year,citationCount,references.title,references.year"
            data = await _s2_get(f"/paper/{pid}", {"fields": fields})

            payload: dict[str, Any] = {
                "paper_id": data.get("paperId"),
                "title": data.get("title"),
                "year": data.get("year"),
                "citation_count": data.get("citationCount", 0),
            }
            if include_references:
                refs = data.get("references") or []
                payload["references"] = [
                    {"title": r.get("title"), "year": r.get("year")} for r in refs[:30]
                ]
                payload["reference_count"] = len(refs)
            return self.ok(payload)
        except Exception as e:
            return self.fail(f"Citation lookup failed: {e}")
