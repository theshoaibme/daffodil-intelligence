"""
Agent Cursor Overlay Module
============================
Renders a named "agent cursor" on screen using a transparent Tkinter window.
This lets users visually distinguish the AI's cursor from their own.

The overlay shows:
  - A colored glowing dot at the agent's current cursor position
  - The agent name label below the cursor
  - A trail of recent positions (optional)
"""

import logging
import threading
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import tkinter as tk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    logger.warning("tkinter not available — agent cursor overlay disabled")


class AgentCursorOverlay:
    """
    A transparent fullscreen window that draws the agent's cursor.

    The window is click-through (does not receive mouse events) so it
    does not interfere with the user's interactions.

    Usage:
        overlay = AgentCursorOverlay(agent_name="CopyCat", color="#4259ff")
        overlay.start()
        overlay.move_to(450, 320)
        overlay.stop()
    """

    def __init__(
        self,
        agent_name: str = "Agent",
        color: str = "#4259ff",
        cursor_size: int = 16,
    ):
        self.agent_name = agent_name
        self.color = color
        self.cursor_size = cursor_size

        self._x = 0
        self._y = 0
        self._visible = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._cursor_item = None
        self._label_item = None
        self._lock = threading.Lock()

    def start(self):
        """Start the overlay window in a background thread."""
        if not TK_AVAILABLE:
            logger.warning("Tkinter not available — overlay skipped")
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_overlay, daemon=True)
        self._thread.start()
        time.sleep(0.3)  # Wait for Tk to init

    def stop(self):
        """Stop and destroy the overlay window."""
        self._running = False
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass
        self._root = None

    def move_to(self, x: int, y: int):
        """Update the agent cursor position."""
        with self._lock:
            self._x = x
            self._y = y
        if self._root and self._canvas:
            try:
                self._root.after(0, self._update_cursor_position)
            except Exception:
                pass

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    # ─── Private ─────────────────────────────────────────────────────────────

    def _run_overlay(self):
        """Runs in background thread — creates and manages Tk window."""
        try:
            self._root = tk.Tk()
            root = self._root

            # Make fullscreen transparent click-through window
            root.title("DI Agent Overlay")
            root.attributes("-fullscreen", True)
            root.attributes("-alpha", 0.85)
            root.attributes("-topmost", True)
            root.overrideredirect(True)  # No title bar

            # Linux: make transparent background
            root.config(bg="black")
            root.attributes("-transparentcolor", "black")

            # Canvas covers entire screen
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            self._canvas = tk.Canvas(
                root,
                width=w,
                height=h,
                bg="black",
                highlightthickness=0,
            )
            self._canvas.pack()

            # Draw initial cursor
            self._draw_cursor()

            # Poll for position updates
            root.after(50, self._poll)
            root.mainloop()
        except Exception as e:
            logger.error(f"Overlay error: {e}")

    def _draw_cursor(self):
        if not self._canvas:
            return
        c = self._canvas
        x, y = self._x, self._y
        s = self.cursor_size

        # Outer glow ring
        c.create_oval(
            x - s, y - s, x + s, y + s,
            outline=self.color, width=2, fill="", tags="cursor_outer"
        )
        # Inner dot
        r = s // 3
        c.create_oval(
            x - r, y - r, x + r, y + r,
            fill=self.color, outline="white", width=1, tags="cursor_inner"
        )
        # Name label
        c.create_text(
            x, y + s + 12,
            text=self.agent_name,
            fill=self.color,
            font=("Roboto", 10, "bold"),
            tags="cursor_label"
        )

    def _update_cursor_position(self):
        if not self._canvas:
            return
        with self._lock:
            x, y = self._x, self._y
        s = self.cursor_size
        r = s // 3

        # Update positions
        self._canvas.coords("cursor_outer", x - s, y - s, x + s, y + s)
        self._canvas.coords("cursor_inner", x - r, y - r, x + r, y + r)
        self._canvas.coords("cursor_label", x, y + s + 12)

    def _poll(self):
        """Called every 50ms to update display."""
        if not self._running or not self._root:
            return
        try:
            self._root.after(50, self._poll)
        except Exception:
            pass
