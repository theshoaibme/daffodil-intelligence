"""Daffodil Kit — local desktop daemon for screen, input, and file control."""

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
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = __import__(f"{__name__}.{module_name}", fromlist=[attr_name])
    return getattr(module, attr_name)
