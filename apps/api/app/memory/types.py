"""Memory type constants and helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

FACT_TYPES = {"fact", "preference", "episode"}
CONVERSATION_TYPES = {"conversation_turn", "conversation_summary"}
CONFIG_TYPES = {
    "system_prompt",
    "skill",
    "ruleset",
    "tool_definition",
    "mcp_server",
    "agent_config",
}
SUBAGENT_TYPES = {"subagent_definition", "subagent_result"}

ALL_MEMORY_TYPES = FACT_TYPES | CONVERSATION_TYPES | CONFIG_TYPES | SUBAGENT_TYPES

ROOT_AGENT_ID = "main"


def compute_content_hash(
    memory_type: str,
    agent_id: str,
    content: str,
    payload: Optional[Dict[str, Any]] = None,
) -> str:
    canonical = json.dumps(
        {"type": memory_type, "agent_id": agent_id, "content": content, "payload": payload or {}},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def resolve_scope(agent_id: str, parent_agent_id: Optional[str] = None) -> str:
    if parent_agent_id:
        return "subagent"
    if agent_id == ROOT_AGENT_ID:
        return "root"
    return "agent"


def canonical_embed_text(memory_type: str, content: str, payload: Optional[Dict[str, Any]] = None) -> str:
    parts: List[str] = [f"[{memory_type}]", content.strip()]
    if payload:
        for key in sorted(payload.keys()):
            val = payload[key]
            if isinstance(val, (list, dict)):
                val = json.dumps(val, ensure_ascii=False)
            parts.append(f"{key}: {val}")
    return "\n".join(parts)
