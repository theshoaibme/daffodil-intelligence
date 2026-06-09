"""Browser tools — web search and URL fetching."""
import logging

from ..base import BaseTool, ToolParameter, ToolResult
from .search_backends import web_search

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the web and return ranked results. Uses Google APIs when configured, "
        "otherwise DuckDuckGo."
    )
    category = "browser"
    parameters = [
        ToolParameter(name="query", type="string", description="Search query"),
        ToolParameter(name="max_results", type="integer", description="Max results to return (default 5)", required=False, default=5),
    ]

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            payload = await web_search(query, max_results=max_results)
            return self.ok(payload)
        except Exception as e:
            return self.fail(f"Web search failed: {e}")


class FetchURLTool(BaseTool):
    name = "fetch_url"
    description = "Fetch the content of a URL and return text (converts HTML to readable text)"
    category = "browser"
    parameters = [
        ToolParameter(name="url", type="string", description="URL to fetch"),
        ToolParameter(name="max_chars", type="integer", description="Max chars to return (default 5000)", required=False, default=5000),
    ]

    async def execute(self, url: str, max_chars: int = 5000) -> ToolResult:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 DaffodilIntelligence/1.0"},
                )

                content_type = response.headers.get("content-type", "")
                text = response.text

                # Strip HTML tags if it's an HTML page
                if "html" in content_type:
                    import re
                    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
                    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()

                truncated = len(text) > max_chars
                return self.ok({
                    "url": url,
                    "status_code": response.status_code,
                    "content": text[:max_chars],
                    "truncated": truncated,
                    "content_type": content_type,
                })
        except Exception as e:
            return self.fail(f"URL fetch failed: {e}")
