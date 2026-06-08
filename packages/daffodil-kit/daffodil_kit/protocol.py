"""JSON-RPC 2.0 protocol helpers for kit WebSocket communication."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Optional


def make_request(method: str, params: Optional[Dict[str, Any]] = None, req_id: Optional[str] = None) -> str:
    return json.dumps({
        "jsonrpc": "2.0",
        "id": req_id or str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    })


def make_response(req_id: str, result: Any = None, error: Optional[Dict[str, Any]] = None) -> str:
    msg: Dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    return json.dumps(msg)


def make_event(event: str, data: Optional[Dict[str, Any]] = None) -> str:
    return json.dumps({
        "jsonrpc": "2.0",
        "method": f"event.{event}",
        "params": data or {},
        "timestamp": time.time(),
    })


def parse_message(raw: str) -> Dict[str, Any]:
    return json.loads(raw)


# Supported RPC methods
KIT_METHODS = {
    "screenshot",
    "mouse.move", "mouse.click", "mouse.scroll", "mouse.drag",
    "keyboard.type", "keyboard.hotkey", "keyboard.press",
    "record.start", "record.stop", "record.list", "record.replay", "record.delete",
    "file.read", "file.write", "file.list", "file.mkdir", "file.move",
    "file.copy", "file.delete", "file.info", "file.search",
    "ping", "status",
}
