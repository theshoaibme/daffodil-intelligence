"""Block user mouse/keyboard during CopyCat replay — fullscreen red banner."""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from .audit import log_event

logger = logging.getLogger(__name__)

COPYCAT_MESSAGE = "CopyCat is running — do not use mouse or keyboard"

try:
    import tkinter as tk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

_state = {"active": False, "mode": None, "recording_name": None}
_lock = threading.Lock()


def is_locked() -> bool:
    with _lock:
        return _state["active"]


def lock_mode() -> Optional[str]:
    with _lock:
        return _state["mode"]


class CopyCatInputLock:
    """Fullscreen overlay — captures pointer, shows red CopyCat banner."""

    def __init__(self, message: str = COPYCAT_MESSAGE):
        self.message = message
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._root: Optional[tk.Tk] = None

    def start(self, mode: str = "replay", recording_name: Optional[str] = None) -> None:
        if not TK_AVAILABLE:
            logger.warning("Tkinter unavailable — input lock banner skipped")
            with _lock:
                _state["active"] = True
                _state["mode"] = mode
                _state["recording_name"] = recording_name
            return

        if self._running:
            return

        with _lock:
            _state["active"] = True
            _state["mode"] = mode
            _state["recording_name"] = recording_name

        log_event("copycat.lock_start", detail={"mode": mode, "recording": recording_name})
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        time.sleep(0.25)

    def stop(self) -> None:
        self._running = False
        with _lock:
            mode = _state.get("mode")
            _state["active"] = False
            _state["mode"] = None
            _state["recording_name"] = None

        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass
        self._root = None
        log_event("copycat.lock_end", detail={"mode": mode})

    def _run(self) -> None:
        try:
            root = tk.Tk()
            self._root = root
            root.title("CopyCat")
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            root.config(bg="#8b0000")
            root.attributes("-alpha", 0.35)

            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            frame = tk.Frame(root, bg="#8b0000")
            frame.place(relx=0.5, rely=0.08, anchor="n")

            tk.Label(
                frame,
                text="CopyCat is running",
                fg="white",
                bg="#ba1a1a",
                font=("Roboto", 22, "bold"),
                padx=24,
                pady=12,
            ).pack()

            tk.Label(
                frame,
                text=self.message,
                fg="#ffdad6",
                bg="#ba1a1a",
                font=("Roboto", 12),
                padx=24,
                pady=6,
            ).pack()

            tk.Label(
                frame,
                text="Mouse and keyboard are disabled for your safety",
                fg="#ffdad6",
                bg="#ba1a1a",
                font=("Roboto", 10),
                padx=24,
                pady=(0, 12),
            ).pack()

            # Block all pointer/keyboard events on overlay
            def _block(_event=None):
                log_event("copycat.input_blocked", detail={"event": "user_input"}, level="warn")
                return "break"

            for seq in (
                "<Button>",
                "<ButtonPress>",
                "<ButtonRelease>",
                "<Motion>",
                "<Key>",
                "<KeyPress>",
            ):
                root.bind_all(seq, _block)

            root.mainloop()
        except Exception as e:
            logger.error("CopyCat lock overlay error: %s", e)


# Singleton lock overlay
_input_lock = CopyCatInputLock()


def acquire(mode: str = "replay", recording_name: Optional[str] = None) -> None:
    _input_lock.start(mode=mode, recording_name=recording_name)


def release() -> None:
    _input_lock.stop()
