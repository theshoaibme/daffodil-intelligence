"""Agent-callable tool to present validated structured UI blocks."""

from __future__ import annotations

from typing import Any, Dict, List

from ..base import BaseTool, ToolParameter, ToolResult
from ...ui_blocks.schemas import TurnPresentation, validate_block_payload


class PresentUiTool(BaseTool):
    name = "present_ui"
    description = (
        "Present structured UI blocks (tables, schedules, reminders) to the user. "
        "Use when auto-mapping is insufficient. Keep summary to one short sentence."
    )
    category = "ui"
    parameters = [
        ToolParameter(
            name="summary",
            type="string",
            description="One short sentence for the user (no table rows).",
            required=True,
        ),
        ToolParameter(
            name="blocks",
            type="list",
            description="List of UI block objects with schema, title, and data.",
            required=True,
        ),
    ]

    async def execute(self, **kwargs) -> ToolResult:
        summary = str(kwargs.get("summary") or "").strip()
        raw_blocks = kwargs.get("blocks")
        if not summary:
            return self.fail("summary is required")
        if not isinstance(raw_blocks, list) or not raw_blocks:
            return self.fail("blocks must be a non-empty list")

        blocks = []
        try:
            for raw in raw_blocks:
                if not isinstance(raw, dict):
                    return self.fail("each block must be an object")
                blocks.append(validate_block_payload(raw))
        except ValueError as e:
            return self.fail(str(e))

        presentation = TurnPresentation(summary=summary, blocks=blocks)
        return ToolResult(
            success=True,
            data={"summary": summary, "blocks": [b.model_dump() for b in blocks]},
            tool_name=self.name,
            ui_blocks=blocks,
            summary=summary,
        )
