"""Proxy computer commands to kit daemon with embedded fallback."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..computer_use.keyboard import KeyboardController
from ..computer_use.mouse import MouseController
from ..computer_use.recorder import get_recorder
from ..computer_use.replayer import get_replayer
from ..computer_use.fast_capture import get_fast_capture
from ..computer_use.runtime import run_blocking
from .bridge import get_kit_bridge


async def kit_or_embedded(
    user_id: Optional[int],
    method: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Try kit daemon first, fall back to embedded computer_use."""
    if user_id:
        bridge = get_kit_bridge()
        result = await bridge.call_for_user(user_id, method, params)
        if "error" not in result or result.get("error") not in ("no_kit", "kit_offline"):
            if "error" not in result:
                return result

    # Embedded fallback
    params = params or {}
    if method == "screenshot":
        cap = get_fast_capture(quality=params.get("quality", 55), scale=params.get("scale", 0.75))
        b64 = await run_blocking(cap.capture_base64)
        w, h = cap.get_screen_size()
        return {"frame": b64, "width": w, "height": h, "image": b64, "success": True}

    replayer = get_replayer()
    if replayer.is_running and method in {
        "mouse.move",
        "mouse.click",
        "mouse.scroll",
        "keyboard.type",
        "keyboard.hotkey",
        "keyboard.press",
    }:
        return {
            "error": "copycat_running",
            "message": "CopyCat is running — mouse and keyboard are disabled",
            "blocked": True,
        }

    mouse = MouseController()
    keyboard = KeyboardController()

    if method == "mouse.move":
        return await mouse.move(params["x"], params["y"], params.get("duration", 0.2))
    if method == "mouse.click":
        return await mouse.click(params["x"], params["y"], params.get("button", "left"))
    if method == "mouse.scroll":
        return await mouse.scroll(params["x"], params["y"], params.get("dy", -3))
    if method == "keyboard.type":
        return await keyboard.type_text(params["text"], params.get("interval", 0.02))
    if method == "keyboard.hotkey":
        return await keyboard.hotkey(*params["keys"])
    if method == "keyboard.press":
        return await keyboard.press_key(params["key"])
    if method == "record.start":
        ok = get_recorder().start(params.get("name"))
        return {"started": ok}
    if method == "record.stop":
        rec = get_recorder().stop()
        if rec:
            path = get_recorder().save(rec)
            return {"name": rec.name, "action_count": rec.action_count, "duration": rec.duration, "saved_to": str(path)}
        return {"error": "Not recording"}
    if method == "record.list":
        return {"recordings": get_recorder().list_recordings()}
    if method == "record.replay":
        name = params.get("name")
        recorder = get_recorder()
        if not name:
            recs = recorder.list_recordings()
            if not recs:
                return {"error": "No recordings"}
            name = recs[0]["name"]
        recording = recorder.load(name)
        if not recording:
            return {"error": f"Not found: {name}"}
        import asyncio

        replayer = get_replayer()
        if replayer.is_running:
            return {"error": "copycat_running", "message": "CopyCat is running"}
        asyncio.create_task(
            replayer.replay(
                recording,
                speed=params.get("speed", 1.0),
                skip_mouse_moves=params.get("skip_mouse_moves", True),
            )
        )
        return {"success": True, "name": name}
    if method == "record.delete":
        return {"deleted": get_recorder().delete(params["name"])}

    return {"error": f"Unknown method: {method}"}
