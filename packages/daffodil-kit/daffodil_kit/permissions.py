"""Cross-platform permission probes — screen, input, focus capture."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Any, Dict, List


def _run(cmd: List[str], timeout: float = 3.0) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout).returncode == 0
    except Exception:
        return False


def check_input_permissions() -> Dict[str, Any]:
    system = platform.system().lower()
    hints: List[str] = []
    mouse_keyboard = False

    try:
        import pyautogui
        pos = pyautogui.position()
        mouse_keyboard = pos is not None
    except Exception:
        mouse_keyboard = False

    if system == "darwin":
        hints.extend([
            "macOS: grant Accessibility in Privacy & Security",
            "macOS: grant Screen Recording for daffodil-kit / Terminal",
        ])
        if not mouse_keyboard:
            hints.append("Open System Settings → Privacy → Accessibility → enable your terminal")
    elif system == "linux":
        session = os.environ.get("XDG_SESSION_TYPE", "unknown")
        hints.append(f"Session: {session}")
        if session == "wayland":
            hints.append("Wayland: approve ScreenCast / RemoteDesktop portal dialogs")
        if not os.environ.get("DISPLAY") and session != "wayland":
            hints.append("Set DISPLAY for X11 capture")
        if shutil.which("groups"):
            try:
                groups = subprocess.check_output(["groups"], text=True)
                if "input" not in groups:
                    hints.append("Optional: sudo usermod -aG input $USER for low-level input")
            except Exception:
                pass
    elif system == "windows":
        hints.append("Windows: run on logged-in desktop (not RDP-only session)")
        mouse_keyboard = mouse_keyboard or True

    return {
        "platform": system,
        "mouse_keyboard": mouse_keyboard,
        "session": os.environ.get("XDG_SESSION_TYPE"),
        "hints": hints,
    }


def get_permission_status() -> Dict[str, Any]:
    from .rust_backend import check_permissions
    return check_permissions()


def request_focus_region() -> Dict[str, Any]:
    """Best-effort active window bounds for focus-area capture."""
    system = platform.system().lower()
    if system == "linux" and shutil.which("xdotool"):
        try:
            out = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowgeometry", "--shell"],
                text=True,
                timeout=2,
            )
            vals = {}
            for line in out.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
            if "X" in vals and "Y" in vals and "WIDTH" in vals and "HEIGHT" in vals:
                return {
                    "region": [
                        int(vals["X"]),
                        int(vals["Y"]),
                        int(vals["WIDTH"]),
                        int(vals["HEIGHT"]),
                    ],
                    "source": "xdotool",
                }
        except Exception:
            pass
    if system == "darwin" and shutil.which("osascript"):
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set {p, s} to position and size of front window of frontApp
            return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s) & "," & (item 2 of s)
        end tell
        '''
        try:
            out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3).strip()
            parts = [int(x) for x in out.split(",")]
            if len(parts) == 4:
                return {"region": parts, "source": "osascript"}
        except Exception:
            pass
    return {"region": None, "source": "unavailable", "hint": "Install xdotool (Linux) for focus capture"}
