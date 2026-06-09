"""Daffodil Kit — local desktop daemon for screen, input, and file control."""

import importlib

__version__ = "0.1.0"
__all__ = [
    "ScreenCapture",
    "MouseController",
    "KeyboardController",
    "ActionRecorder",
    "ActionReplayer",
    "get_recorder",
]

_EXPORTS = {
    "ScreenCapture": ("screen", "ScreenCapture"),
    "MouseController": ("mouse", "MouseController"),
    "KeyboardController": ("keyboard", "KeyboardController"),
    "ActionRecorder": ("recorder", "ActionRecorder"),
    "ActionReplayer": ("replayer", "ActionReplayer"),
    "get_recorder": ("recorder", "get_recorder"),
}


def __getattr__(name: str):
    if name in _EXPORTS:
        module_name, attr_name = _EXPORTS[name]
        module = importlib.import_module(f"{__name__}.{module_name}")
        return getattr(module, attr_name)

    try:
        return importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) == f"{__name__}.{name}":
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
        raise
