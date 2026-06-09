"""Daffodil Kit — local desktop daemon for screen, input, and file control."""

from .keyboard import KeyboardController
from .mouse import MouseController
from .recorder import ActionRecorder, get_recorder
from .replayer import ActionReplayer
from .screen import ScreenCapture

__version__ = "0.1.0"
__all__ = [
    "ScreenCapture",
    "MouseController",
    "KeyboardController",
    "ActionRecorder",
    "ActionReplayer",
    "get_recorder",
]
