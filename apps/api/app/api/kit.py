"""Kit pairing and device management API."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..core.security import get_current_user
from ..kit.bridge import dispatch_kit_message, get_kit_bridge
from ..kit.repository import KitRepository

router = APIRouter(prefix="/api/kit", tags=["kit"])
logger = logging.getLogger(__name__)


class PairConfirmRequest(BaseModel):
    code: str
    device_id: str
    device_name: str = "desktop"
    allowed_roots: list[str] | None = None


@router.post("/pair/code")
async def generate_pairing_code(user=Depends(get_current_user)):
    repo = KitRepository()
    code = await repo.create_pairing_code(user.id)
    return {"code": code, "expires_in_seconds": 300}


@router.post("/pair/confirm")
async def confirm_pairing(req: PairConfirmRequest):
    repo = KitRepository()
    result = await repo.confirm_pairing(
        req.code, req.device_id, req.device_name, req.allowed_roots
    )
    if not result:
        return {"error": "Invalid or expired pairing code"}
    return result


@router.get("/devices")
async def list_devices(user=Depends(get_current_user)):
    repo = KitRepository()
    devices = await repo.list_devices(user.id)
    bridge = get_kit_bridge()
    for d in devices:
        d["is_online"] = bridge.is_device_online(d["id"])
    return {"devices": devices}


@router.get("/status")
async def kit_status(user=Depends(get_current_user)):
    bridge = get_kit_bridge()
    return await bridge.call_for_user(user.id, "status")


@router.get("/permissions")
async def kit_permissions(user=Depends(get_current_user)):
    bridge = get_kit_bridge()
    result = await bridge.call_for_user(user.id, "permissions.status")
    if "error" in result:
        try:
            import sys
            from pathlib import Path
            kit_path = Path(__file__).resolve().parents[4] / "packages" / "daffodil-kit"
            if str(kit_path) not in sys.path:
                sys.path.insert(0, str(kit_path))
            from daffodil_kit.permissions import get_permission_status
            return get_permission_status()
        except Exception as e:
            return {"ready": False, "error": str(result.get("error")), "fallback_error": str(e)}
    return result


class StreamConfigBody(BaseModel):
    min_fps: int | None = None
    max_fps: int | None = None
    min_quality: int | None = None
    max_quality: int | None = None
    min_scale: float | None = None
    max_scale: float | None = None
    focus_mode: bool | None = None
    target_latency_ms: float | None = None


@router.post("/stream/configure")
async def configure_stream(body: StreamConfigBody, user=Depends(get_current_user)):
    bridge = get_kit_bridge()
    config = body.model_dump(exclude_none=True)
    return await bridge.call_for_user(user.id, "stream.configure", {"config": config})


@router.get("/focus")
async def focus_region(user=Depends(get_current_user)):
    bridge = get_kit_bridge()
    return await bridge.call_for_user(user.id, "focus.region")


@router.get("/audit/tail")
async def kit_audit_tail(limit: int = 50, user=Depends(get_current_user)):
    """CopyCat security audit log from paired kit device."""
    bridge = get_kit_bridge()
    return await bridge.call_for_user(user.id, "audit.tail", {"limit": limit})


@router.get("/audit/system-log")
async def kit_audit_system_log(lines: int = 30, user=Depends(get_current_user)):
    """OS + kit log tail from paired device (local data only)."""
    bridge = get_kit_bridge()
    return await bridge.call_for_user(user.id, "audit.system_log", {"lines": lines})


@router.post("/record/stop-replay")
async def kit_stop_replay(user=Depends(get_current_user)):
    """Stop CopyCat replay on kit and release input lock."""
    bridge = get_kit_bridge()
    return await bridge.call_for_user(user.id, "record.stop_replay")


@router.websocket("/ws/{device_id}")
async def kit_device_ws(websocket: WebSocket, device_id: str):
    """Kit daemon connects here; inbound messages are RPC responses."""
    await websocket.accept()
    bridge = get_kit_bridge()
    repo = KitRepository()
    bridge.register_connection(device_id, websocket)
    await repo.set_online(device_id, True)
    logger.info("Kit WS connected: %s", device_id)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "hello":
                continue
            # API → kit commands are sent via bridge.call; kit → API responses land here
            if "id" in data and ("result" in data or "error" in data):
                dispatch_kit_message(device_id, raw)
    except WebSocketDisconnect:
        pass
    finally:
        bridge.unregister_connection(device_id)
        await repo.set_online(device_id, False)
        logger.info("Kit WS disconnected: %s", device_id)
