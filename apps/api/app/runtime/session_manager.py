"""
Session Manager
===============
Single entry point the rest of the app uses to talk to the Antigravity runtime.

Maps ``(user_id, chat_id)`` to a stable Antigravity ``conversation_id`` so
context persists across requests via the SDK's on-disk conversation store. The
SDK assigns the conversation id when an agent first runs; we capture it and
persist a small JSON index so later turns resume the same conversation.

It opens an agent per call (``async with``) which keeps lifecycle correct and
lets multiple users run concurrently without sharing mutable agent state.

Provides:
  - ``chat(...)``  -> full response text + metadata
  - ``stream(...)`` -> async generator of text tokens
Both accept optional multimodal attachments (images/audio/documents).
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, TypedDict, Literal

from .agent_factory import build_agent, get_save_dir, AgentPersona, is_available

try:
    from google.antigravity.types import Text, Thought, ToolCall
except Exception:  # pragma: no cover - import guard
    Text = Thought = ToolCall = None  # type: ignore


class StreamEvent(TypedDict, total=False):
    type: Literal["content", "thinking", "tool", "agent", "subagent", "context"]
    content: str
    name: str
    status: Literal["active", "success"]

logger = logging.getLogger(__name__)


def _key(user_id: Any, chat_id: Any) -> str:
    return f"u{user_id}-c{chat_id}"


def _build_prompt(message: str, attachments: Optional[List[Any]]) -> Any:
    if not attachments:
        return message
    return [message, *attachments]


class _ConversationIndex:
    """Persists (user,chat) -> antigravity conversation_id mappings."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, str] = {}
        self._loaded = False

    @property
    def _path(self) -> Path:
        return Path(get_save_dir()) / "_index.json"

    def _load(self):
        if self._loaded:
            return
        try:
            if self._path.exists():
                self._cache = json.loads(self._path.read_text("utf-8"))
        except Exception as e:
            logger.warning(f"Could not load conversation index: {e}")
            self._cache = {}
        self._loaded = True

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            self._load()
            return self._cache.get(key)

    def set(self, key: str, conversation_id: str):
        with self._lock:
            self._load()
            if self._cache.get(key) == conversation_id:
                return
            self._cache[key] = conversation_id
            try:
                self._path.write_text(json.dumps(self._cache), "utf-8")
            except Exception as e:
                logger.warning(f"Could not persist conversation index: {e}")


class SessionManager:
    """Coordinates Antigravity agent conversations for all callers."""

    def __init__(self):
        self._index = _ConversationIndex()

    def available(self) -> bool:
        return is_available()

    async def chat(
        self,
        message: str,
        user_id: Any = 0,
        chat_id: Any = "default",
        persona: AgentPersona | str = AgentPersona.MAIN,
        attachments: Optional[List[Any]] = None,
        lang: Optional[str] = None,
        extra_system: Optional[str] = None,
        model: Optional[str] = None,
        include_tools: Optional[List[str]] = None,
    ) -> dict:
        """Run one turn and return the full response.

        Returns a dict: {content, tool_calls, thoughts, persona, conversation_id}.
        """
        key = _key(user_id, chat_id)
        conv = self._index.get(key)
        prompt = _build_prompt(message, attachments)

        agent = build_agent(
            persona=persona,
            conversation_id=conv,
            lang=lang,
            extra_system=extra_system,
            model=model,
            include_tools=include_tools,
        )
        async with agent:
            response = await agent.chat(prompt)
            content = await response.text()
            tool_calls = await _collect(response, "tool_calls")
            thoughts = await _collect(response, "thoughts")
            new_conv = getattr(agent, "conversation_id", None)

        if new_conv:
            self._index.set(key, new_conv)

        return {
            "content": content,
            "tool_calls": [getattr(t, "name", str(t)) for t in tool_calls],
            "thoughts": [str(t) for t in thoughts],
            "persona": persona.value if isinstance(persona, AgentPersona) else str(persona),
            "conversation_id": new_conv,
            "model_id": model,
        }

    async def stream(
        self,
        message: str,
        user_id: Any = 0,
        chat_id: Any = "default",
        persona: AgentPersona | str = AgentPersona.MAIN,
        attachments: Optional[List[Any]] = None,
        lang: Optional[str] = None,
        extra_system: Optional[str] = None,
        model: Optional[str] = None,
        include_tools: Optional[List[str]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Run one turn and yield structured stream events as they arrive."""
        key = _key(user_id, chat_id)
        conv = self._index.get(key)
        prompt = _build_prompt(message, attachments)

        agent = build_agent(
            persona=persona,
            conversation_id=conv,
            lang=lang,
            extra_system=extra_system,
            model=model,
            include_tools=include_tools,
        )
        async with agent:
            response = await agent.chat(prompt)
            active_tools: List[str] = []

            def _complete_tools() -> List[StreamEvent]:
                events: List[StreamEvent] = []
                for name in active_tools:
                    events.append({"type": "tool", "name": name, "status": "success"})
                active_tools.clear()
                return events

            async for chunk in response.chunks:
                if Text is not None and isinstance(chunk, Text):
                    for event in _complete_tools():
                        yield event
                    if chunk.text:
                        yield {"type": "content", "content": chunk.text}
                elif Thought is not None and isinstance(chunk, Thought):
                    if chunk.text:
                        yield {"type": "thinking", "content": chunk.text}
                        if _is_subagent_thought(chunk.text):
                            yield {
                                "type": "subagent",
                                "name": "delegated",
                                "status": "active",
                                "content": chunk.text[:200],
                            }
                        await _maybe_store_subagent_thought(
                            chunk.text,
                            user_id=user_id,
                            chat_id=chat_id,
                        )
                elif ToolCall is not None and isinstance(chunk, ToolCall):
                    for event in _complete_tools():
                        yield event
                    name = chunk.name or "tool"
                    active_tools.append(name)
                    yield {"type": "tool", "name": name, "status": "active"}

            for event in _complete_tools():
                yield event

            new_conv = getattr(agent, "conversation_id", None)

        if new_conv:
            self._index.set(key, new_conv)


async def _collect(response: Any, attr: str) -> List[Any]:
    """Best-effort drain of an optional async-iterable property on ChatResponse."""
    items: List[Any] = []
    stream = getattr(response, attr, None)
    if stream is None:
        return items
    try:
        async for item in stream:
            items.append(item)
    except TypeError:
        pass
    except Exception as e:  # pragma: no cover - defensive
        logger.debug(f"Could not collect {attr}: {e}")
    return items


_SUBAGENT_MARKERS = ("sub-agent", "subagent", "delegat", "spawn agent")


def _is_subagent_thought(text: str) -> bool:
    lower = (text or "").lower()
    return any(m in lower for m in _SUBAGENT_MARKERS)


async def _maybe_store_subagent_thought(
    text: str,
    *,
    user_id: Any,
    chat_id: Any,
) -> None:
    """Heuristic: capture sub-agent delegation thoughts as memories."""
    if not _is_subagent_thought(text):
        return
    try:
        from ..memory import memory_service

        subagent_id = f"sub-{hash(text) % 100000:05d}"
        await memory_service.store_subagent_event(
            user_id=int(user_id or 0),
            parent_agent_id="main",
            subagent_id=subagent_id,
            name="delegated",
            task=text[:500],
            chat_id=chat_id,
        )
    except Exception as e:
        logger.debug("subagent memory store skipped: %s", e)


session_manager = SessionManager()
