"""Real-time status and thinking signals streamed before model output."""

from __future__ import annotations

import asyncio
import random
from typing import Any, AsyncIterator, Optional

_THINKING_OPENERS = (
    "Hmm",
    "Hmm,",
    "Let me think",
    "Okay",
    "Alright",
)

_THINKING_MIDDLES = (
    " let me think about that",
    " considering your question",
    " working through this",
    " one moment",
)

_THINKING_ENDINGS = (
    "...\n",
    ".\n",
    " — almost there...\n",
)


async def stream_turn_preamble(
    *,
    status_lines: list[str],
    routing: str,
    simulate_thinking: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Yield status + thinking events before the model streams content."""
    for line in status_lines:
        yield {"type": "status", "content": line}

    if not simulate_thinking:
        return

    opener = random.choice(_THINKING_OPENERS)
    middle = random.choice(_THINKING_MIDDLES)
    ending = random.choice(_THINKING_ENDINGS)

    yield {"type": "thinking", "content": opener}
    await asyncio.sleep(0.08)
    yield {"type": "thinking", "content": middle}
    await asyncio.sleep(0.06)

    if routing in ("code", "code_complex", "reasoning"):
        yield {"type": "thinking", "content": " — this needs careful reasoning"}
        await asyncio.sleep(0.05)

    yield {"type": "thinking", "content": ending}
