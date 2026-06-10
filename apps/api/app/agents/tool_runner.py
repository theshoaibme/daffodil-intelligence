"""Execute registry tools and format user-facing replies."""

from __future__ import annotations

from typing import Optional

from ..tools.base import ToolResult
from ..tools.registry import get_registry
from ..ui_blocks.mappers import format_tool_results
from ..ui_blocks.schemas import TurnPresentation

__all__ = ["format_tool_results", "run_tool", "TurnPresentation"]


def _uid(context: Optional[dict]) -> int:
    return int((context or {}).get("user_id") or 0)


async def run_tool(name: str, context: Optional[dict] = None, **kwargs) -> ToolResult:
    uid = _uid(context)
    if uid and "user_id" not in kwargs:
        kwargs["user_id"] = str(uid)
    result = await get_registry().execute(name, **kwargs)
    from ..ui_blocks.mappers import enrich_tool_result
    from .tool_runner_ui import stash_blocks_from_result

    enriched = enrich_tool_result(result, name)
    stash_blocks_from_result(enriched, name)
    return enriched
