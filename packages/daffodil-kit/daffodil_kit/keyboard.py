"""
Keyboard Controller Module
============================
Cross-platform keyboard control for agent computer use.
Supports typing text, pressing hotkeys, and single key presses.
"""

import asyncio
import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Keyboard control disabled.")

try:
    from pynput.keyboard import Key, Controller as PynputKeyController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


# Map common key names to pyautogui key strings
KEY_ALIASES = {
    "enter": "enter",
    "return": "enter",
    "escape": "escape",
    "esc": "escape",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "delete": "delete",
    "del": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "ctrl": "ctrl",
    "alt": "alt",
    "shift": "shift",
    "win": "win",
    "cmd": "command",
    "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
    "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
    "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
    "home": "home",
    "end": "end",
    "pageup": "pageup",
    "pagedown": "pagedown",
    "insert": "insert",
    "printscreen": "printscreen",
    "capslock": "capslock",
    "numlock": "numlock",
}


class KeyboardController:
    """
    Agent keyboard controller.

    All methods are async-safe and run in a thread pool.

    Features:
    - type_text(text)          — Type a string of text with configurable delay
    - press_key(key)           — Press and release a single key
    - hotkey(*keys)            — Press a combination (e.g., Ctrl+C)
    - hold_key(key, duration)  — Hold a key for a duration
    """

    async def type_text(self, text: str, interval: float = 0.0) -> dict:
        """
        Type text character by character.
        Args:
            text: The text to type
            interval: Delay between keystrokes in seconds (0 = fast)
        """
        return await self._run(self._type_text, text, interval)

    async def press_key(self, key: str) -> dict:
        """
        Press and release a single key.
        Args:
            key: Key name (e.g., 'enter', 'escape', 'f5')
        """
        return await self._run(self._press_key, key)

    async def hotkey(self, *keys: str) -> dict:
        """
        Press a key combination simultaneously.
        Args:
            keys: Key names in order (e.g., 'ctrl', 'c' for Ctrl+C)

        Examples:
            await keyboard.hotkey('ctrl', 'c')       # Copy
            await keyboard.hotkey('ctrl', 'shift', 's')  # Save As
            await keyboard.hotkey('alt', 'f4')       # Close window
            await keyboard.hotkey('ctrl', 'alt', 'del')  # Task manager
        """
        return await self._run(self._hotkey, list(keys))

    async def hold_key(self, key: str, duration: float = 1.0) -> dict:
        """Hold a key down for a specified duration."""
        return await self._run(self._hold_key, key, duration)

    async def clear_and_type(self, text: str) -> dict:
        """Select all existing text and replace with new text."""
        await self.hotkey("ctrl", "a")
        await asyncio.sleep(0.05)
        return await self.type_text(text)

    # ─── Sync implementations ────────────────────────────────────────────────

    def _type_text(self, text: str, interval: float) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            pyautogui.typewrite(text, interval=interval)
            return {
                "action": "type_text",
                "text": text[:50] + ("..." if len(text) > 50 else ""),
                "chars": len(text),
                "success": True,
            }
        except Exception as e:
            # pyautogui.typewrite doesn't support unicode well, fall back to clipboard paste
            try:
                import subprocess
                process = subprocess.Popen(
                    ["xclip", "-selection", "clipboard"],
                    stdin=subprocess.PIPE,
                )
                process.communicate(text.encode("utf-8"))
                pyautogui.hotkey("ctrl", "v")
                return {"action": "type_text_clipboard", "text": text[:50], "success": True}
            except Exception as e2:
                logger.error(f"Keyboard type failed: {e}, clipboard fallback failed: {e2}")
                return {"action": "type_text", "success": False, "error": str(e)}

    def _press_key(self, key: str) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            mapped = KEY_ALIASES.get(key.lower(), key.lower())
            pyautogui.press(mapped)
            return {"action": "press_key", "key": key, "success": True}
        except Exception as e:
            return {"action": "press_key", "key": key, "success": False, "error": str(e)}

    def _hotkey(self, keys: List[str]) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            mapped = [KEY_ALIASES.get(k.lower(), k.lower()) for k in keys]
            pyautogui.hotkey(*mapped)
            return {"action": "hotkey", "keys": keys, "success": True}
        except Exception as e:
            return {"action": "hotkey", "keys": keys, "success": False, "error": str(e)}

    def _hold_key(self, key: str, duration: float) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            mapped = KEY_ALIASES.get(key.lower(), key.lower())
            pyautogui.keyDown(mapped)
            time.sleep(duration)
            pyautogui.keyUp(mapped)
            return {"action": "hold_key", "key": key, "duration": duration, "success": True}
        except Exception as e:
            return {"action": "hold_key", "key": key, "success": False, "error": str(e)}

    async def _run(self, fn, *args):
        from .runtime import run_blocking
        return await run_blocking(fn, *args)
