"""
Live smoke test for the Antigravity runtime.

Skipped unless RUN_LIVE_AGENT=1 and GEMINI_API_KEY are set, because it makes a
real Gemini call. Use to verify the end-to-end agent loop in environments with
quota available.
"""

import os

import pytest

from app.runtime.agent_factory import is_available
from app.runtime import session_manager

RUN_LIVE = os.environ.get("RUN_LIVE_AGENT") == "1"


@pytest.mark.skipif(not (RUN_LIVE and is_available()), reason="live agent disabled or unavailable")
async def test_live_agent_chat():
    res = await session_manager.chat("Reply with exactly: PONG", user_id=1, chat_id="pytest-smoke")
    assert isinstance(res["content"], str)
    assert res["conversation_id"]
