"""
Computer Use API Router
========================
REST + WebSocket endpoints for agent computer control.

Endpoints:
  POST /api/computer/screenshot        — Capture current screen
  POST /api/computer/mouse/move        — Move agent cursor
  POST /api/computer/mouse/click       — Click at position
  POST /api/computer/mouse/scroll      — Scroll at position
  POST /api/computer/keyboard/type     — Type text
  POST /api/computer/keyboard/hotkey   — Send hotkey
  WS   /api/computer/screen-stream     — Live screen WebSocket stream
  POST /api/computer/record/start      — Start CopyCat recording
  POST /api/computer/record/stop       — Stop CopyCat recording
  GET  /api/computer/record/list       — List saved recordings
  POST /api/computer/record/replay     — Replay a recording
  DELETE /api/computer/record/{name}   — Delete a recording
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel

from ..core.security import get_current_user
from ..computer_use.screen import ScreenCapture
from ..computer_use.mouse import MouseController
from ..computer_use.keyboard import KeyboardController
from ..computer_use.recorder import get_recorder
from ..computer_use.replayer import get_replayer

router = APIRouter(prefix="/api/computer", tags=["computer-use"])
logger = logging.getLogger(__name__)

# Singletons
_screen = ScreenCapture(fps=10, quality=70)
_mouse = MouseController()
_keyboard = KeyboardController()
_replayer = get_replayer()

COPYCAT_MESSAGE = "CopyCat is running — mouse and keyboard are disabled"


def _copycat_blocks_input() -> bool:
    """True when replay is active and user input must be blocked."""
    return _replayer.is_running


def _raise_if_copycat_active() -> None:
    if _copycat_blocks_input():
        raise HTTPException(
            status_code=423,
            detail={
                "error": "copycat_running",
                "message": COPYCAT_MESSAGE,
                "blocked": True,
            },
        )


# ─── Request models ──────────────────────────────────────────────────────────

class MouseMoveRequest(BaseModel):
    x: int
    y: int
    duration: float = 0.2


class MouseClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"


class MouseScrollRequest(BaseModel):
    x: int
    y: int
    dy: int = -3


class KeyboardTypeRequest(BaseModel):
    text: str
    interval: float = 0.02


class KeyboardHotkeyRequest(BaseModel):
    keys: list[str]  # e.g. ["ctrl", "c"]


class RecordStartRequest(BaseModel):
    name: Optional[str] = None


class ReplayRequest(BaseModel):
    name: Optional[str] = None   # If None, replay last recording
    speed: float = 1.0
    skip_mouse_moves: bool = False


# ─── Screenshot ──────────────────────────────────────────────────────────────

@router.post("/screenshot")
async def take_screenshot(
    region: Optional[str] = None,   # "x,y,width,height"
    quality: int = 75,
):
    """Capture the current screen as a base64 JPEG."""
    sc = ScreenCapture(quality=quality)

    if region:
        try:
            x, y, w, h = [int(v) for v in region.split(",")]
            b64 = sc.capture_as_base64(region=(x, y, w, h))
        except ValueError:
            return {"error": "Invalid region format. Use 'x,y,width,height'"}
    else:
        b64 = sc.capture_as_base64()

    if not b64:
        return {"error": "Screen capture failed. Is a display available?"}

    width, height = sc.get_screen_size()
    return {
        "success": True,
        "image": b64,
        "width": width,
        "height": height,
        "format": "image/jpeg",
    }


# ─── Mouse ───────────────────────────────────────────────────────────────────

@router.post("/mouse/move")
async def mouse_move(req: MouseMoveRequest):
    _raise_if_copycat_active()
    result = await _mouse.move(req.x, req.y, req.duration)
    return result


@router.post("/mouse/click")
async def mouse_click(req: MouseClickRequest):
    _raise_if_copycat_active()
    result = await _mouse.click(req.x, req.y, req.button)
    return result


@router.post("/mouse/scroll")
async def mouse_scroll(req: MouseScrollRequest):
    _raise_if_copycat_active()
    result = await _mouse.scroll(req.x, req.y, req.dy)
    return result


@router.get("/mouse/position")
async def get_mouse_position():
    x, y = await _mouse.get_position()
    return {"x": x, "y": y}


# ─── Keyboard ────────────────────────────────────────────────────────────────

@router.post("/keyboard/type")
async def keyboard_type(req: KeyboardTypeRequest):
    _raise_if_copycat_active()
    result = await _keyboard.type_text(req.text, req.interval)
    return result


@router.post("/keyboard/hotkey")
async def keyboard_hotkey(req: KeyboardHotkeyRequest):
    _raise_if_copycat_active()
    result = await _keyboard.hotkey(*req.keys)
    return result


@router.post("/keyboard/press")
async def keyboard_press(key: str):
    _raise_if_copycat_active()
    result = await _keyboard.press_key(key)
    return result


# ─── Live Screen Stream (WebSocket) ──────────────────────────────────────────

@router.websocket("/screen-stream")
async def screen_stream_ws(websocket: WebSocket):
    """
    Adaptive screen stream — dynamic FPS/quality/scale from measured latency.

    Client control messages:
      {"action": "start", "config": {"max_fps": 30, "focus_mode": true, ...}}
      {"action": "stop"}
      {"action": "configure", "config": {...}}
    """
    from ..kit.stream_adapter import adaptive_frames

    await websocket.accept()
    logger.info("Adaptive screen stream connected")

    streaming = False
    stream_config: dict = {}
    frame_gen = None
    stop_event = asyncio.Event()

    async def pump_frames():
        nonlocal frame_gen
        try:
            async for frame in adaptive_frames(stream_config):
                if stop_event.is_set():
                    break
                await websocket.send_json(frame)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Stream pump error: %s", e)

    pump_task: asyncio.Task | None = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")

            if action == "start":
                stream_config = msg.get("config") or {}
                if msg.get("fps"):
                    stream_config.setdefault("max_fps", msg["fps"])
                if msg.get("quality"):
                    stream_config.setdefault("max_quality", msg["quality"])
                stop_event.clear()
                streaming = True
                if pump_task:
                    pump_task.cancel()
                pump_task = asyncio.create_task(pump_frames())

            elif action == "stop":
                streaming = False
                stop_event.set()
                if pump_task:
                    pump_task.cancel()
                    pump_task = None

            elif action == "configure":
                stream_config.update(msg.get("config") or {})

    except WebSocketDisconnect:
        logger.info("Screen stream disconnected")
    except Exception as e:
        logger.error("Screen stream error: %s", e)
    finally:
        stop_event.set()
        if pump_task:
            pump_task.cancel()


# ─── CopyCat Recording ───────────────────────────────────────────────────────

@router.post("/record/start")
async def start_recording(req: RecordStartRequest):
    """Start recording user actions."""
    recorder = get_recorder()
    if recorder.is_recording:
        return {"error": "Already recording. Stop the current session first."}
    success = recorder.start(req.name)
    if success:
        return {"success": True, "message": "Recording started", "name": req.name or "auto"}
    return {"error": "Failed to start recording. pynput may not be installed."}


@router.post("/record/stop")
async def stop_recording():
    """Stop the active recording and return stats."""
    recorder = get_recorder()
    if not recorder.is_recording:
        return {"error": "No active recording"}

    recording = recorder.stop()
    if not recording:
        return {"error": "Recording failed to capture data"}

    # Auto-save
    path = recorder.save(recording)

    return {
        "success": True,
        "name": recording.name,
        "duration_seconds": recording.duration,
        "action_count": recording.action_count,
        "saved_to": str(path),
    }


@router.get("/record/list")
async def list_recordings():
    """List all saved recordings."""
    recorder = get_recorder()
    recordings = recorder.list_recordings()
    return {"recordings": recordings, "count": len(recordings)}


@router.post("/record/replay")
async def replay_recording(req: ReplayRequest):
    """Replay a named recording (or the last one)."""
    recorder = get_recorder()

    if _replayer.is_running:
        return {"error": "A replay is already in progress"}

    if req.name:
        recording = recorder.load(req.name)
        if not recording:
            return {"error": f"Recording '{req.name}' not found"}
    else:
        recordings = recorder.list_recordings()
        if not recordings:
            return {"error": "No recordings available"}
        recording = recorder.load(recordings[0]["name"])
        if not recording:
            return {"error": "Could not load recording"}

    # Start replay in background
    asyncio.create_task(
        _replayer.replay(recording, speed=req.speed, skip_mouse_moves=req.skip_mouse_moves)
    )

    return {
        "success": True,
        "name": recording.name,
        "action_count": recording.action_count,
        "speed": req.speed,
        "message": "Replay started in background",
    }


@router.delete("/record/{name}")
async def delete_recording(name: str):
    """Delete a saved recording by name."""
    recorder = get_recorder()
    success = recorder.delete(name)
    if success:
        return {"success": True, "deleted": name}
    return {"error": f"Recording '{name}' not found"}


@router.post("/record/stop-replay")
async def stop_replay():
    """Stop an active CopyCat replay and release input lock."""
    if not _replayer.is_running:
        return {"stopped": False, "message": "No replay in progress"}
    _replayer.stop()
    return {"stopped": True, "message": "CopyCat replay stopped"}


@router.get("/record/status")
async def replay_status():
    """Check if a replay is currently running."""
    from ..computer_use.copycat_lock import is_locked

    replaying = _replayer.is_running
    locked = is_locked() or replaying
    return {
        "is_replaying": replaying,
        "copycat_running": locked,
        "message": COPYCAT_MESSAGE if locked else None,
        "current_action_index": _replayer.current_action if replaying else None,
        "is_recording": get_recorder().is_recording,
    }


@router.get("/audit/tail")
async def audit_tail(limit: int = 50):
    """Local CopyCat security audit log (machine running the API/kit)."""
    try:
        from daffodil_kit.audit import read_audit_tail
        return {"entries": read_audit_tail(limit)}
    except ImportError:
        return {"entries": [], "note": "Install daffodil-kit for local audit logs"}


@router.get("/audit/system-log")
async def audit_system_log(lines: int = 30):
    """Recent OS + kit log lines (local read only)."""
    try:
        from daffodil_kit.audit import read_kit_log_tail, read_system_log_tail
        return {
            "system": read_system_log_tail(lines),
            "kit_log": read_kit_log_tail(lines),
            "local_only": True,
        }
    except ImportError:
        return {"system": {"lines": []}, "kit_log": [], "local_only": True}


@router.get("/info")
async def computer_info():
    """Get system info for computer use capabilities."""
    sc = ScreenCapture()
    width, height = sc.get_screen_size()

    # Check what's available
    capabilities = {}
    try:
        import pyautogui
        capabilities["mouse_control"] = True
        capabilities["keyboard_control"] = True
        capabilities["screenshot"] = True
    except ImportError:
        capabilities["mouse_control"] = False
        capabilities["keyboard_control"] = False

    try:
        import mss
        capabilities["fast_capture"] = True
    except ImportError:
        capabilities["fast_capture"] = False

    try:
        from pynput import mouse
        capabilities["recording"] = True
    except ImportError:
        capabilities["recording"] = False

    return {
        "screen_width": width,
        "screen_height": height,
        "capabilities": capabilities,
        "is_recording": get_recorder().is_recording,
        "is_replaying": _replayer.is_running,
    }
