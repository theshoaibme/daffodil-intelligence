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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from ..core.security import get_current_user
from ..computer_use.screen import ScreenCapture
from ..computer_use.mouse import MouseController
from ..computer_use.keyboard import KeyboardController
from ..computer_use.recorder import get_recorder
from ..computer_use.replayer import ActionReplayer

router = APIRouter(prefix="/api/computer", tags=["computer-use"])
logger = logging.getLogger(__name__)

# Singletons
_screen = ScreenCapture(fps=10, quality=70)
_mouse = MouseController()
_keyboard = KeyboardController()
_replayer = ActionReplayer()


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
    result = await _mouse.move(req.x, req.y, req.duration)
    return result


@router.post("/mouse/click")
async def mouse_click(req: MouseClickRequest):
    result = await _mouse.click(req.x, req.y, req.button)
    return result


@router.post("/mouse/scroll")
async def mouse_scroll(req: MouseScrollRequest):
    result = await _mouse.scroll(req.x, req.y, req.dy)
    return result


@router.get("/mouse/position")
async def get_mouse_position():
    x, y = await _mouse.get_position()
    return {"x": x, "y": y}


# ─── Keyboard ────────────────────────────────────────────────────────────────

@router.post("/keyboard/type")
async def keyboard_type(req: KeyboardTypeRequest):
    result = await _keyboard.type_text(req.text, req.interval)
    return result


@router.post("/keyboard/hotkey")
async def keyboard_hotkey(req: KeyboardHotkeyRequest):
    result = await _keyboard.hotkey(*req.keys)
    return result


@router.post("/keyboard/press")
async def keyboard_press(key: str):
    result = await _keyboard.press_key(key)
    return result


# ─── Live Screen Stream (WebSocket) ──────────────────────────────────────────

@router.websocket("/screen-stream")
async def screen_stream_ws(websocket: WebSocket):
    """
    WebSocket endpoint that streams screen frames as base64 JPEG.

    Client sends JSON messages to control streaming:
      {"action": "start", "fps": 5, "quality": 70}
      {"action": "stop"}
      {"action": "region", "x": 0, "y": 0, "width": 1920, "height": 1080}

    Server sends JSON frames:
      {"type": "frame", "frame": "<base64>", "width": 1920, "height": 1080, "timestamp": ...}
    """
    await websocket.accept()
    logger.info("Screen stream WebSocket connected")

    fps = 5
    quality = 70
    region = None
    streaming = False
    stream_task = None

    try:
        while True:
            try:
                # Wait for control message (non-blocking with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                msg = json.loads(data)
                action = msg.get("action")

                if action == "start":
                    fps = msg.get("fps", 5)
                    quality = msg.get("quality", 70)
                    streaming = True

                elif action == "stop":
                    streaming = False

                elif action == "region":
                    region = (
                        msg.get("x", 0), msg.get("y", 0),
                        msg.get("width", 1920), msg.get("height", 1080)
                    )

            except asyncio.TimeoutError:
                pass  # No message this cycle — continue streaming
            except Exception:
                break

            # Send a frame if streaming
            if streaming:
                sc = ScreenCapture(fps=fps, quality=quality)
                b64 = sc.capture_as_base64(region=region)
                if b64:
                    width, height = sc.get_screen_size()
                    await websocket.send_json({
                        "type": "frame",
                        "frame": b64,
                        "width": width if not region else region[2],
                        "height": height if not region else region[3],
                        "timestamp": asyncio.get_event_loop().time(),
                    })

                await asyncio.sleep(1.0 / fps)

    except WebSocketDisconnect:
        logger.info("Screen stream WebSocket disconnected")
    except Exception as e:
        logger.error(f"Screen stream error: {e}")


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


@router.get("/record/status")
async def replay_status():
    """Check if a replay is currently running."""
    return {
        "is_replaying": _replayer.is_running,
        "current_action_index": _replayer.current_action if _replayer.is_running else None,
        "is_recording": get_recorder().is_recording,
    }


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
