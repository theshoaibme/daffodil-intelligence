"""Routes computer/file commands to paired daffodil-kit daemons — low-latency RPC."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_connections: Dict[str, Any] = {}
_pending: Dict[str, asyncio.Future] = {}
_device_cache: Dict[int, Dict[str, Any]] = {}
_device_cache_ts: Dict[int, float] = {}
_CACHE_TTL = 5.0


def sign_kit_command(secret: str, params: Dict[str, Any]) -> Dict[str, Any]:
    ts = time.time()
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(secret.encode(), f"{int(ts)}.{payload}".encode(), hashlib.sha256).hexdigest()
    out = dict(params)
    out["_timestamp"] = ts
    out["_signature"] = sig
    return out


def dispatch_kit_message(device_id: str, raw: str) -> None:
    """Resolve a pending RPC future when kit responds."""
    try:
        resp = json.loads(raw)
    except json.JSONDecodeError:
        return
    req_id = resp.get("id")
    if req_id and req_id in _pending:
        fut = _pending.pop(req_id)
        if not fut.done():
            fut.set_result(resp)


class KitBridge:
    """Proxy RPC calls to a user's online kit daemon."""

    def register_connection(self, device_id: str, ws: Any) -> None:
        _connections[device_id] = ws
        logger.info("Kit device connected: %s", device_id)

    def unregister_connection(self, device_id: str) -> None:
        _connections.pop(device_id, None)
        for rid, fut in list(_pending.items()):
            if not fut.done():
                fut.cancel()
            _pending.pop(rid, None)
        logger.info("Kit device disconnected: %s", device_id)

    def is_device_online(self, device_id: str) -> bool:
        return device_id in _connections

    async def call(
        self,
        device_id: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        device_secret: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        ws = _connections.get(device_id)
        if ws is None:
            return {"error": "kit_offline", "message": f"Device {device_id} not connected"}

        req_id = str(uuid.uuid4())
        signed = sign_kit_command(device_secret or "", params or {}) if device_secret else (params or {})
        msg = json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": signed,
        }, separators=(",", ":"))

        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        _pending[req_id] = fut

        try:
            await ws.send_text(msg)
            resp = await asyncio.wait_for(fut, timeout=timeout)
            if "error" in resp:
                return {"error": resp["error"]}
            return resp.get("result", {})
        except asyncio.TimeoutError:
            _pending.pop(req_id, None)
            return {"error": "timeout"}
        except Exception as e:
            _pending.pop(req_id, None)
            return {"error": str(e)}

    async def call_for_user(
        self,
        user_id: int,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from .repository import KitRepository

        device = await self._get_device_cached(user_id, device_id)
        if not device:
            return {"error": "no_kit", "message": "No online kit device for user"}

        # Fast path defaults for agent hot commands
        params = dict(params or {})
        if method == "screenshot":
            params.setdefault("quality", 55)
            params.setdefault("scale", 0.75)
        elif method == "mouse.move":
            params.setdefault("duration", 0.0)
        elif method == "keyboard.type":
            params.setdefault("interval", 0.0)

        result = await self.call(device["id"], method, params, device_secret=device["device_secret"])

        # Fire-and-forget audit — don't block the hot path
        asyncio.create_task(self._audit(user_id, device["id"], method, params, result))
        return result

    async def _get_device_cached(self, user_id: int, device_id: Optional[str]) -> Optional[Dict[str, Any]]:
        now = time.time()
        if not device_id and user_id in _device_cache and now - _device_cache_ts.get(user_id, 0) < _CACHE_TTL:
            cached = _device_cache[user_id]
            if cached["id"] in _connections:
                return cached
        from .repository import KitRepository
        repo = KitRepository()
        device = await repo.get_online_device(user_id, device_id)
        if device:
            _device_cache[user_id] = device
            _device_cache_ts[user_id] = now
        return device

    async def _audit(
        self,
        user_id: int,
        device_id: str,
        method: str,
        params: Optional[Dict],
        result: Dict,
    ) -> None:
        try:
            from .repository import KitRepository
            await KitRepository().log_audit(
                user_id, device_id, method, params,
                success="error" not in result,
                error=str(result.get("error")) if "error" in result else None,
            )
        except Exception:
            logger.debug("Audit log failed", exc_info=True)


_bridge: Optional[KitBridge] = None


def get_kit_bridge() -> KitBridge:
    global _bridge
    if _bridge is None:
        _bridge = KitBridge()
    return _bridge
