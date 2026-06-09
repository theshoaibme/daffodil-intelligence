"""High-throughput screen capture — persistent MSS, reused buffers, fast JPEG."""

from __future__ import annotations

import base64
import io
import logging
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class FastScreenCapture:
    """Reuse MSS instance + monitor metadata; avoid per-frame allocations where possible."""

    __slots__ = ("quality", "scale", "_sct", "_lock", "_monitor", "_width", "_height", "_buf")

    def __init__(self, quality: int = 55, scale: float = 1.0):
        # quality 55 + subsampling = ~3x faster encode vs quality 75 optimize=True
        self.quality = max(20, min(95, quality))
        self.scale = scale if 0 < scale <= 1.0 else 1.0
        self._sct = mss.mss() if MSS_AVAILABLE else None
        self._lock = threading.Lock()
        self._monitor: Optional[dict] = None
        self._width = 1920
        self._height = 1080
        self._buf = io.BytesIO()
        if self._sct:
            self._monitor = self._sct.monitors[1]
            self._width = self._monitor["width"]
            self._height = self._monitor["height"]

    def get_screen_size(self) -> Tuple[int, int]:
        if self.scale < 1.0:
            return int(self._width * self.scale), int(self._height * self.scale)
        return self._width, self._height

    def capture_jpeg(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[bytes]:
        if not self._sct or not PIL_AVAILABLE:
            return None
        with self._lock:
            if region:
                x, y, w, h = region
                shot = self._sct.grab({"top": y, "left": x, "width": w, "height": h})
            else:
                shot = self._sct.grab(self._monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            if self.scale < 1.0:
                nw = max(1, int(img.width * self.scale))
                nh = max(1, int(img.height * self.scale))
                img = img.resize((nw, nh), Image.Resampling.BILINEAR)
            self._buf.seek(0)
            self._buf.truncate(0)
            img.save(
                self._buf,
                format="JPEG",
                quality=self.quality,
                optimize=False,
                subsampling=2,
            )
            return self._buf.getvalue()

    def capture_base64(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        data = self.capture_jpeg(region)
        return base64.b64encode(data).decode("ascii") if data else None

    def close(self) -> None:
        if self._sct:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None


# Process-wide singleton — avoids MSS init cost (~15ms) per screenshot
_capture: Optional[FastScreenCapture] = None
_capture_lock = threading.Lock()


def get_fast_capture(quality: int = 55, scale: float = 1.0) -> FastScreenCapture:
    global _capture
    with _capture_lock:
        if _capture is None:
            _capture = FastScreenCapture(quality=quality, scale=scale)
        elif quality != _capture.quality:
            _capture.quality = quality
        return _capture
