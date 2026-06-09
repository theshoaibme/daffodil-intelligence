"""WebSocket daemon — optimized for low-latency agent control."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .stream_engine import AdaptiveStreamEngine

import websockets
from websockets.server import WebSocketServerProtocol

from .fast_capture import get_fast_capture
from .file_agent import (
    PathPolicyError,
    copy_path,
    create_directory,
    delete_path,
    file_info,
    list_directory,
    move_path,
    read_file,
    search_files,
    write_file,
)
from .keyboard import KeyboardController
from .mouse import MouseController
from .overlay import AgentCursorOverlay
from .protocol import make_response, parse_message
from .recorder import get_recorder
from .replayer import ActionReplayer
from .runtime import run_blocking
from .security import get_device_secret, sign_command, verify_command

logger = logging.getLogger(__name__)

_mouse = MouseController()
_keyboard = KeyboardController()
_recorder = get_recorder()
_replayer = ActionReplayer()
_overlay: Optional[AgentCursorOverlay] = None
_stream_engine: Optional["AdaptiveStreamEngine"] = None

# Hot path: reuse capture singleton (persistent MSS / Rust)
_capture = get_fast_capture(quality=55, scale=0.75)


def _verify_signed(params: Dict[str, Any]) -> bool:
    secret = get_device_secret()
    if not secret:
        return True
    sig = params.pop("_signature", "")
    ts = float(params.pop("_timestamp", 0))
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return verify_command(secret, payload, ts, sig)


async def _handle_method(method: str, params: Dict[str, Any]) -> Any:
    from .copycat_guard import check_method_allowed
    blocked = check_method_allowed(method, source=params.pop("_source", "user"))
    if blocked:
        return blocked

    if method == "ping":
        return {"pong": True, "time": time.time()}

    if method == "status":
        from .permissions import get_permission_status
        from .rust_backend import is_rust_available
        from .vault import vault_status
        perms = get_permission_status()
        return {
            "recording": _recorder.is_recording,
            "replaying": _replayer.is_running,
            "rust": is_rust_available(),
            "permissions": perms,
            "vault": vault_status(),
            "stream": _stream_engine.status() if _stream_engine else None,
        }

    if method == "permissions.status":
        from .permissions import get_permission_status
        return get_permission_status()

    if method == "focus.region":
        from .permissions import request_focus_region
        return await run_blocking(request_focus_region)

    if method == "vault.status":
        from .vault import vault_status
        return vault_status()

    if method == "vault.set_password":
        from .vault import set_system_password
        pw = params.get("password", "")
        if not pw:
            return {"error": "password required"}
        return set_system_password(pw, params.get("label", "sudo"))

    if method == "stream.configure":
        global _stream_engine
        from .stream_engine import AdaptiveStreamEngine, StreamConfig
        if _stream_engine is None:
            _stream_engine = AdaptiveStreamEngine(StreamConfig.from_dict(params.get("config")))
        return _stream_engine.update_config(params.get("config") or {})

    if method == "screenshot":
        quality = params.get("quality", 55)
        scale = params.get("scale", 0.75)
        if quality != _capture.quality:
            _capture.quality = quality
        if scale != _capture.scale:
            _capture.scale = scale
        region = params.get("region")
        if region:
            b64 = await run_blocking(_capture.capture_base64, tuple(region))
        else:
            b64 = await run_blocking(_capture.capture_base64)
        w, h = _capture.get_screen_size()
        return {"frame": b64, "width": w, "height": h}

    if method == "mouse.move":
        return await _mouse.move(params["x"], params["y"], params.get("duration", 0.0))

    if method == "mouse.click":
        return await _mouse.click(params["x"], params["y"], params.get("button", "left"))

    if method == "mouse.scroll":
        return await _mouse.scroll(params["x"], params["y"], params.get("dy", -3))

    if method == "mouse.drag":
        return await _mouse.drag(
            params["x1"], params["y1"], params["x2"], params["y2"],
            params.get("duration", 0.15),
        )

    if method == "keyboard.type":
        return await _keyboard.type_text(params["text"], params.get("interval", 0.0))

    if method == "keyboard.hotkey":
        return await _keyboard.hotkey(*params["keys"])

    if method == "keyboard.press":
        return await _keyboard.press_key(params["key"])

    if method == "audit.tail":
        from .audit import read_audit_tail
        return {"entries": read_audit_tail(params.get("limit", 50))}

    if method == "audit.system_log":
        from .audit import read_kit_log_tail, read_system_log_tail
        return {
            "system": read_system_log_tail(params.get("lines", 30)),
            "kit_log": read_kit_log_tail(params.get("lines", 40)),
        }

    if method == "record.status":
        from .input_lock import is_locked, lock_mode
        return {
            "is_recording": _recorder.is_recording,
            "is_replaying": _replayer.is_running,
            "copycat_running": is_locked(),
            "mode": lock_mode(),
            "message": "CopyCat is running" if is_locked() else None,
        }

    if method == "record.stop_replay":
        _replayer.stop()
        from .input_lock import release
        release()
        return {"stopped": True}

    if method == "record.start":
        from .input_lock import acquire
        name = params.get("name")
        ok = _recorder.start(name)
        if ok:
            acquire(mode="recording", recording_name=name)
        return {"started": ok, "name": name}

    if method == "record.stop":
        rec = _recorder.stop()
        from .input_lock import release
        release()
        if rec:
            path = await run_blocking(_recorder.save, rec)
            from .audit import log_event
            log_event("copycat.record_stop", detail={"name": rec.name, "actions": rec.action_count})
            return {
                "name": rec.name,
                "action_count": rec.action_count,
                "duration": rec.duration,
                "path": str(path),
            }
        return {"error": "Not recording"}

    if method == "record.list":
        return {"recordings": await run_blocking(_recorder.list_recordings)}

    if method == "record.replay":
        name = params.get("name")
        if not name:
            recs = await run_blocking(_recorder.list_recordings)
            if not recs:
                return {"error": "No recordings"}
            name = recs[0]["name"]
        recording = await run_blocking(_recorder.load, name)
        if not recording:
            return {"error": f"Recording not found: {name}"}

        from .audit import log_event
        log_event("copycat.replay_start", detail={"name": name, "actions": recording.action_count})

        global _overlay
        if params.get("show_cursor", False):
            _overlay = AgentCursorOverlay(agent_name="CopyCat")
            _overlay.start()

        async def on_action(_i, action, _total):
            if _overlay and action.x is not None and action.y is not None:
                _overlay.move_to(action.x, action.y)

        result = await _replayer.replay(
            recording,
            speed=params.get("speed", 2.0),
            skip_mouse_moves=params.get("skip_mouse_moves", True),
            on_action=on_action,
        )
        if _overlay:
            _overlay.stop()
            _overlay = None
        from .audit import log_event
        log_event("copycat.replay_end", detail=result)
        result["copycat_running"] = False
        return result

    if method == "record.delete":
        return {"deleted": await run_blocking(_recorder.delete, params["name"])}

    file_ops = {
        "file.read": lambda: read_file(params["path"], params.get("max_chars", 5000)),
        "file.write": lambda: write_file(params["path"], params["content"], params.get("mode", "write")),
        "file.list": lambda: list_directory(params["path"], params.get("recursive", False)),
        "file.mkdir": lambda: create_directory(params["path"]),
        "file.move": lambda: move_path(params["src"], params["dst"]),
        "file.copy": lambda: copy_path(params["src"], params["dst"]),
        "file.delete": lambda: delete_path(params["path"]),
        "file.info": lambda: file_info(params["path"]),
        "file.search": lambda: search_files(params["path"], params.get("glob", "*")),
    }
    if method in file_ops:
        try:
            return await run_blocking(file_ops[method])
        except PathPolicyError as e:
            return {"error": str(e)}

    return {"error": f"Unknown method: {method}"}


async def _process_message(ws: WebSocketServerProtocol, raw: str) -> None:
    try:
        msg = parse_message(raw)
        if "method" not in msg:
            return
        req_id = msg.get("id", "0")
        params = dict(msg.get("params") or {})
        if not _verify_signed(params):
            await ws.send(make_response(req_id, error={"code": 401, "message": "Invalid signature"}))
            return
        result = await _handle_method(msg["method"], params)
        await ws.send(make_response(req_id, result=result))
    except Exception as e:
        logger.exception("Kit daemon error")
        await ws.send(make_response("0", error={"code": -32603, "message": str(e)}))


async def _handle_connection(ws: WebSocketServerProtocol) -> None:
    """Handle multiple concurrent RPCs without serializing on one slow screenshot."""
    pending: set[asyncio.Task] = set()

    async for raw in ws:
        task = asyncio.create_task(_process_message(ws, raw))
        pending.add(task)
        task.add_done_callback(pending.discard)

    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def run_daemon(host: str = "127.0.0.1", port: int = 9477) -> None:
    logger.info("Starting daffodil-kit daemon on ws://%s:%d", host, port)
    async with websockets.serve(
        _handle_connection,
        host,
        port,
        compression=None,
        max_size=16 * 1024 * 1024,
        ping_interval=20,
        ping_timeout=10,
    ):
        await asyncio.Future()


def sign_params(params: Dict[str, Any]) -> Dict[str, Any]:
    secret = get_device_secret()
    if not secret:
        return params
    ts = time.time()
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    out = dict(params)
    out["_timestamp"] = ts
    out["_signature"] = sign_command(secret, payload, ts)
    return out
