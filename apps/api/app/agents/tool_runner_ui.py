"""Bridge direct-agent tool results into turn UI block events."""

from __future__ import annotations

from ..runtime.task_events import stash_pending_ui_events
from ..tools.base import ToolResult
from ..ui_blocks.schemas import ui_block_to_dict


def stash_blocks_from_result(result: ToolResult, tool_name: str) -> None:
    if not result.ui_blocks:
        return
    events = [
        {
            "type": "ui",
            "block": ui_block_to_dict(block),
            "source": "local",
            "tool_name": tool_name,
        }
        for block in result.ui_blocks
    ]
    stash_pending_ui_events(events)


def stash_presentation_blocks(presentation, tool_name: str = "agent") -> None:
    from ..ui_blocks.schemas import TurnPresentation

    if not isinstance(presentation, TurnPresentation) or not presentation.blocks:
        return
    events = [
        {
            "type": "ui",
            "block": ui_block_to_dict(block),
            "source": "local",
            "tool_name": tool_name,
        }
        for block in presentation.blocks
    ]
    stash_pending_ui_events(events)
