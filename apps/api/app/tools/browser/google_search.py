"""Google-oriented web search tool with multi-backend fallback."""

from ..base import BaseTool, ToolParameter, ToolResult
from .search_backends import web_search


class GoogleWebSearchTool(BaseTool):
    name = "google_web_search"
    description = (
        "Search the web using Google (Custom Search, Serper, or Gemini grounding). "
        "Falls back to DuckDuckGo when Google APIs are not configured."
    )
    category = "browser"
    parameters = [
        ToolParameter(name="query", type="string", description="Search query"),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Max results to return (default 8)",
            required=False,
            default=8,
        ),
    ]

    async def execute(self, query: str, max_results: int = 8) -> ToolResult:
        try:
            payload = await web_search(query, max_results=max_results)
            return self.ok(payload)
        except Exception as e:
            return self.fail(f"Google web search failed: {e}")
