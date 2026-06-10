"""Versioned AI event envelope schemas for SSE/WS transport."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

EVENT_VERSION = 1

AiEventType = str


class EventSource(BaseModel):
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    mcp_server: Optional[str] = None
    workflow_node_id: Optional[str] = None


class AiEventEnvelope(BaseModel):
    v: int = EVENT_VERSION
    id: str = Field(default_factory=lambda: str(uuid4()))
    seq: int = 0
    ts: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    session_id: str
    turn_id: str
    source: EventSource = Field(default_factory=EventSource)
    type: AiEventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    # Legacy compat: raw type for clients not yet on envelope
    legacy_type: Optional[str] = None

    def to_sse_dict(self, *, include_legacy: bool = True) -> Dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        if include_legacy and self.legacy_type:
            data["type"] = self.legacy_type
            data.update(self._legacy_flat_fields())
        return data

    def _legacy_flat_fields(self) -> Dict[str, Any]:
        """Flatten payload fields expected by legacy SSE consumers."""
        p = self.payload
        mapping: Dict[str, Any] = {}
        if self.type == "message.chunk":
            mapping["content"] = p.get("content", "")
        elif self.type == "message.thinking":
            mapping["content"] = p.get("content", "")
        elif self.type in ("tool.started", "tool.finished"):
            mapping["name"] = p.get("tool_name") or p.get("name")
            mapping["status"] = p.get("status", "active")
            if p.get("agent_id"):
                mapping["agent_id"] = p["agent_id"]
            if p.get("source"):
                mapping["source"] = p["source"]
            if p.get("mcp_server"):
                mapping["mcp_server"] = p["mcp_server"]
        elif self.type == "agent.started":
            mapping["agent_id"] = p.get("agent_id")
            mapping["name"] = p.get("name")
            mapping["status"] = p.get("status", "active")
        elif self.type == "agent.delegated":
            mapping["agent_id"] = p.get("agent_id")
            mapping["name"] = p.get("name", "delegated")
            mapping["status"] = p.get("status", "active")
            mapping["content"] = p.get("content", "")
        elif self.type == "ui.block":
            mapping["block"] = p.get("block")
            if p.get("source"):
                mapping["source"] = p["source"]
            if p.get("tool_name"):
                mapping["tool_name"] = p["tool_name"]
        elif self.type == "context.usage":
            mapping.update(p)
        elif self.type == "model.resolved":
            mapping["model_id"] = p.get("model_id")
            mapping["model_mode"] = p.get("model_mode")
            mapping["model_routing"] = p.get("model_routing")
        elif self.type == "workflow.node":
            for key in (
                "task_id", "parent_id", "kind", "name", "title",
                "short_title", "status", "agent_id", "parallel_group", "depth",
            ):
                if key in p:
                    mapping[key] = p[key]
        elif self.type == "memory.active":
            mapping["name"] = p.get("name", "memory")
            mapping["status"] = p.get("status", "active")
        elif self.type == "status.progress":
            mapping["content"] = p.get("content", "")
        return mapping


# Legacy type → canonical type mapping
LEGACY_TYPE_MAP: Dict[str, str] = {
    "content": "message.chunk",
    "thinking": "message.thinking",
    "status": "status.progress",
    "tool": "tool.started",
    "agent": "agent.started",
    "subagent": "agent.delegated",
    "memory": "memory.active",
    "task": "workflow.node",
    "ui": "ui.block",
    "model": "model.resolved",
    "context": "context.usage",
}


def legacy_event_to_envelope(
    event: Dict[str, Any],
    *,
    session_id: str,
    turn_id: str,
    seq: int,
    correlation_id: Optional[str] = None,
) -> AiEventEnvelope:
    """Convert a legacy runtime event dict into a versioned envelope."""
    raw_type = str(event.get("type", "content"))
    canonical = LEGACY_TYPE_MAP.get(raw_type, raw_type)

    source = EventSource()
    payload: Dict[str, Any] = {}

    if raw_type == "content":
        payload = {"content": event.get("content", ""), "role": "assistant"}
    elif raw_type == "thinking":
        payload = {"content": event.get("content", "")}
    elif raw_type == "status":
        payload = {"content": event.get("content", "")}
    elif raw_type == "tool":
        tool_name = event.get("name", "")
        status = event.get("status", "active")
        canonical = "tool.finished" if status == "success" else "tool.started"
        payload = {
            "tool_name": tool_name,
            "name": tool_name,
            "status": status,
            "agent_id": event.get("agent_id"),
            "source": event.get("source", "local"),
            "mcp_server": event.get("mcp_server"),
        }
        source.tool_name = tool_name
        if event.get("agent_id"):
            source.agent_id = event["agent_id"]
    elif raw_type == "agent":
        payload = {
            "agent_id": event.get("agent_id"),
            "name": event.get("name"),
            "status": event.get("status", "active"),
        }
        if event.get("agent_id"):
            source.agent_id = event["agent_id"]
    elif raw_type == "subagent":
        payload = {
            "agent_id": event.get("agent_id"),
            "name": event.get("name", "delegated"),
            "status": event.get("status", "active"),
            "content": event.get("content", ""),
        }
        if event.get("agent_id"):
            source.agent_id = event["agent_id"]
    elif raw_type == "memory":
        payload = {
            "name": event.get("name", "memory"),
            "status": event.get("status", "active"),
        }
    elif raw_type == "task":
        payload = {k: v for k, v in event.items() if k != "type" and v is not None}
        if event.get("agent_id"):
            source.agent_id = event["agent_id"]
        if event.get("task_id"):
            source.workflow_node_id = event["task_id"]
    elif raw_type == "ui":
        payload = {
            "block": event.get("block"),
            "source": event.get("source"),
            "tool_name": event.get("tool_name"),
        }
        if event.get("tool_name"):
            source.tool_name = event["tool_name"]
    elif raw_type == "model":
        payload = {
            "model_id": event.get("model_id"),
            "model_mode": event.get("model_mode"),
            "model_routing": event.get("model_routing"),
        }
    elif raw_type == "context":
        payload = {k: v for k, v in event.items() if k != "type"}
    else:
        payload = {k: v for k, v in event.items() if k != "type"}

    return AiEventEnvelope(
        seq=seq,
        session_id=session_id,
        turn_id=turn_id,
        source=source,
        type=canonical,
        payload=payload,
        correlation_id=correlation_id,
        legacy_type=raw_type,
    )
