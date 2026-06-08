"""Daffodil Kit — local desktop daemon for screen, input, and file control."""

from .screen import ScreenCapture
from .mouse import MouseController
from .keyboard import KeyboardController
from .recorder import ActionRecorder, get_recorder
from .replayer import ActionReplayer

__version__ = "0.1.0"
__all__ = [
    "ScreenCapture",
    "MouseController",
    "KeyboardController",
    "ActionRecorder",
    "ActionReplayer",
    "get_recorder",
]
