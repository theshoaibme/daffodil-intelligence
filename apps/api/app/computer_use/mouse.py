"""
Mouse Controller Module
========================
Cross-platform mouse control for agent computer use.
Supports move, click, double-click, right-click, scroll, and drag.
"""

import asyncio
import logging
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = True   # Move to corner to abort
    pyautogui.PAUSE = 0
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Mouse control disabled. Run: pip install pyautogui")

try:
    from pynput.mouse import Button, Controller as PynputMouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class MouseController:
    """
    Agent mouse controller.

    All methods are async-safe (they run blocking calls in a thread executor
    so they do not block the FastAPI event loop).

    Features:
    - move(x, y)              — Move cursor to absolute screen coordinates
    - click(x, y, button)     — Click at position
    - double_click(x, y)      — Double click
    - right_click(x, y)       — Right click
    - scroll(x, y, dy)        — Scroll at position
    - drag(x1, y1, x2, y2)   — Click-drag from one point to another
    - get_position()          — Get current cursor position
    """

    def __init__(self):
        self._loop = None

    async def move(self, x: int, y: int, duration: float = 0.2) -> dict:
        """
        Move agent cursor to (x, y).
        Args:
            x, y: Target screen coordinates
            duration: Seconds to animate the move (0 = instant)
        """
        return await self._run(self._move, x, y, duration)

    async def click(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> dict:
        """
        Move to (x, y) and click.
        Args:
            button: 'left', 'right', 'middle'
        """
        return await self._run(self._click, x, y, button, duration)

    async def double_click(self, x: int, y: int) -> dict:
        """Double-click at (x, y)."""
        return await self._run(self._double_click, x, y)

    async def right_click(self, x: int, y: int) -> dict:
        """Right-click at (x, y)."""
        return await self.click(x, y, button="right")

    async def scroll(self, x: int, y: int, dy: int = -3) -> dict:
        """
        Scroll at position (x, y).
        Args:
            dy: Positive = scroll up, negative = scroll down (in clicks)
        """
        return await self._run(self._scroll, x, y, dy)

    async def drag(
        self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5
    ) -> dict:
        """Click and drag from (x1, y1) to (x2, y2)."""
        return await self._run(self._drag, x1, y1, x2, y2, duration)

    async def get_position(self) -> Tuple[int, int]:
        """Return current cursor (x, y) position."""
        if PYAUTOGUI_AVAILABLE:
            pos = pyautogui.position()
            return pos.x, pos.y
        return 0, 0

    # ─── Sync implementations (run in thread pool) ──────────────────────────

    def _move(self, x: int, y: int, duration: float) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
            return {"action": "move", "x": x, "y": y, "success": True}
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return {"action": "move", "x": x, "y": y, "success": False, "error": str(e)}

    def _click(self, x: int, y: int, button: str, duration: float) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            btn_map = {"left": "left", "right": "right", "middle": "middle"}
            pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
            pyautogui.click(x, y, button=btn_map.get(button, "left"))
            return {"action": "click", "x": x, "y": y, "button": button, "success": True}
        except Exception as e:
            logger.error(f"Mouse click failed: {e}")
            return {"action": "click", "x": x, "y": y, "success": False, "error": str(e)}

    def _double_click(self, x: int, y: int) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            pyautogui.doubleClick(x, y)
            return {"action": "double_click", "x": x, "y": y, "success": True}
        except Exception as e:
            return {"action": "double_click", "x": x, "y": y, "success": False, "error": str(e)}

    def _scroll(self, x: int, y: int, dy: int) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.scroll(dy)
            return {"action": "scroll", "x": x, "y": y, "dy": dy, "success": True}
        except Exception as e:
            return {"action": "scroll", "x": x, "y": y, "success": False, "error": str(e)}

    def _drag(self, x1: int, y1: int, x2: int, y2: int, duration: float) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available"}
        try:
            pyautogui.moveTo(x1, y1, duration=0.15)
            pyautogui.dragTo(x2, y2, duration=duration, button="left", tween=pyautogui.easeInOutQuad)
            return {"action": "drag", "from": [x1, y1], "to": [x2, y2], "success": True}
        except Exception as e:
            return {"action": "drag", "success": False, "error": str(e)}

    async def _run(self, fn, *args):
        """Run a blocking mouse function in the thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, *args)
