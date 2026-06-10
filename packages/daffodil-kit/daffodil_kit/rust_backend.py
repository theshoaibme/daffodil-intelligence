"""Rust-native screen capture — Python handles input (cross-platform, no dbus)."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_native = None
_native_checked = False


def _load_native():
    global _native, _native_checked
    if _native_checked:
        return _native
    _native_checked = True
    try:
        import daffodil_kit_native  # type: ignore
        _native = daffodil_kit_native
        logger.info("daffodil-kit: Rust capture backend active")
    except ImportError:
        logger.info("daffodil-kit: Rust not built — pip install -e '.[native]'")
        _native = None
    return _native


def is_rust_available() -> bool:
    return _load_native() is not None


def capture_jpeg(
    quality: int = 55,
    scale: float = 0.75,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[bytes]:
    n = _load_native()
    if n:
        try:
            reg = tuple(region) if region else None
            return bytes(n.capture_jpeg(quality, float(scale), reg))
        except Exception as e:
            logger.warning("Rust capture failed: %s", e)
    from .fast_capture import get_fast_capture
    return get_fast_capture(quality=quality, scale=scale).capture_jpeg(region)


def capture_frame(
    quality: int = 55,
    scale: float = 0.75,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[Dict[str, Any]]:
    n = _load_native()
    if n:
        try:
            reg = tuple(region) if region else None
            data, w, h = n.capture_jpeg_scaled(quality, float(scale), reg)
            return {
                "jpeg": bytes(data),
                "width": int(w),
                "height": int(h),
                "backend": "rust",
            }
        except Exception as e:
            logger.warning("Rust capture_frame failed: %s", e)
    from .fast_capture import get_fast_capture
    cap = get_fast_capture(quality=quality, scale=scale)
    jpeg = cap.capture_jpeg(region)
    if not jpeg:
        return None
    w, h = cap.get_screen_size()
    return {"jpeg": jpeg, "width": w, "height": h, "backend": "python"}


def capture_base64(
    quality: int = 55,
    scale: float = 0.75,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[str]:
    data = capture_jpeg(quality, scale, region)
    return base64.b64encode(data).decode("ascii") if data else None


def screen_size() -> Tuple[int, int]:
    n = _load_native()
    if n:
        try:
            w, h = n.screen_size()
            return int(w), int(h)
        except Exception:
            pass
    from .fast_capture import get_fast_capture
    return get_fast_capture().get_screen_size()


def check_permissions() -> Dict[str, Any]:
    import platform
    return {
        "screen_capture": True,
        "mouse_keyboard": True,
        "ready": True,
        "platform": platform.system().lower(),
        "backend": "python",
        "hints": []
    }
