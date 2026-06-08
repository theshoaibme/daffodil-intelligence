"""
Action Replayer Module
=======================
Replays recorded mouse/keyboard action sequences.
Supports speed multiplier and selective action filtering.
"""

import asyncio
import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.PAUSE = 0
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class ActionReplayer:
    """
    Replays a sequence of recorded actions.

    Usage:
        replayer = ActionReplayer()
        await replayer.replay(recording, speed=1.0)

    The replayer sends real-time progress events so the UI can show
    which action is currently being executed.
    """

    def __init__(self):
        self._running = False
        self._current_action_index = 0

    async def replay(
        self,
        recording,
        speed: float = 1.0,
        skip_mouse_moves: bool = False,
        on_action=None,  # async callback: on_action(index, action, total)
    ) -> dict:
        """
        Replay a recording.

        Args:
            recording: Recording object from ActionRecorder
            speed: Playback speed multiplier (1.0 = original speed, 2.0 = double speed)
            skip_mouse_moves: If True, skip intermediate mouse movements (faster)
            on_action: Async callback called before each action with (index, action, total)

        Returns:
            dict with replay stats
        """
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not available for replay"}

        if not recording or not recording.actions:
            return {"error": "No actions to replay"}

        from .input_lock import acquire, release

        acquire(mode="replay", recording_name=getattr(recording, "name", None))
        self._running = True
        self._current_action_index = 0
        start_time = time.time()
        total = len(recording.actions)
        executed = 0
        errors = 0

        actions = recording.actions
        if skip_mouse_moves:
            actions = [a for a in actions if a.type != "mouse_move"]

        try:
            for i, action in enumerate(actions):
                if not self._running:
                    break

                self._current_action_index = i

                if on_action:
                    try:
                        await on_action(i, action, total)
                    except Exception:
                        pass

                try:
                    await self._execute_action(action)
                    executed += 1
                except Exception as e:
                    logger.error(f"Replay action {i} failed: {e}")
                    errors += 1

                delay = getattr(action, "delay_after", 0) or 0
                if delay > 0 and speed > 0:
                    adjusted = delay / speed
                    if adjusted > 0.005:
                        await asyncio.sleep(min(adjusted, 2.0))
        finally:
            self._running = False
            release()

        elapsed = time.time() - start_time

        return {
            "name": recording.name,
            "total_actions": total,
            "executed": executed,
            "errors": errors,
            "duration_seconds": elapsed,
            "speed_multiplier": speed,
            "success": errors == 0,
        }

    def stop(self):
        """Stop a running replay."""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_action(self) -> int:
        return self._current_action_index

    # ─── Action execution ────────────────────────────────────────────────────

    async def _execute_action(self, action):
        """Execute a single action in the thread pool."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._execute_sync, action)

    def _execute_sync(self, action):
        """Synchronous action execution."""
        action_type = action.type

        if action_type == "mouse_move":
            pyautogui.moveTo(action.x, action.y, duration=0)

        elif action_type == "mouse_click":
            if action.pressed:  # Only execute on press, not release
                btn = action.button or "left"
                if btn == "button.left":
                    btn = "left"
                elif btn == "button.right":
                    btn = "right"
                elif btn == "button.middle":
                    btn = "middle"
                pyautogui.click(action.x, action.y, button=btn)

        elif action_type == "mouse_scroll":
            pyautogui.moveTo(action.x, action.y, duration=0)
            pyautogui.scroll(action.dy or 0)

        elif action_type == "key_type":
            if action.text:
                try:
                    pyautogui.typewrite(action.text, interval=0.0)
                except Exception:
                    pass  # Some chars not supported by typewrite

        elif action_type == "key_press":
            if action.pressed and action.key:
                key_name = action.key.replace("key.", "")
                try:
                    pyautogui.press(key_name)
                except Exception:
                    pass  # Unknown key
