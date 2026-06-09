"""
Screen Capture Module
======================
Real-time screen capture with WebSocket streaming support.
Uses `mss` for fast cross-platform capture with fallback to PIL.
"""

import asyncio
import base64
import io
import logging
import time
from typing import AsyncGenerator, Optional, Tuple

logger = logging.getLogger(__name__)

# Try fast capture first, fall back gracefully
try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logger.warning("mss not available, falling back to PIL/pyautogui")

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False


class ScreenCapture:
    """
    High-performance screen capture for agent vision.

    Features:
    - Full screen capture as JPEG bytes
    - Region-of-interest capture (x, y, width, height)
    - Base64-encoded frames for WebSocket streaming
    - Async frame generator for continuous streaming
    """

    def __init__(self, fps: int = 5, quality: int = 75):
        """
        Args:
            fps: Frames per second for streaming (default 5)
            quality: JPEG quality 1-95 (default 75 — balance of speed/clarity)
        """
        self.fps = fps
        self.quality = quality
        self._streaming = False
        self._frame_interval = 1.0 / fps

    def capture_full(self) -> Optional[bytes]:
        """Capture the entire screen, return as JPEG bytes."""
        if MSS_AVAILABLE:
            return self._capture_mss()
        elif PIL_AVAILABLE:
            return self._capture_pil()
        elif PYAUTOGUI_AVAILABLE:
            return self._capture_pyautogui()
        else:
            logger.error("No screen capture library available. Install mss: pip install mss")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[bytes]:
        """Capture a specific region of the screen."""
        if MSS_AVAILABLE:
            return self._capture_mss_region(x, y, width, height)
        elif PIL_AVAILABLE:
            return self._capture_pil_region(x, y, width, height)
        return None

    def capture_as_base64(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        """Capture screen and return as base64-encoded JPEG string."""
        if region:
            data = self.capture_region(*region)
        else:
            data = self.capture_full()

        if data is None:
            return None
        return base64.b64encode(data).decode("utf-8")

    def get_screen_size(self) -> Tuple[int, int]:
        """Return (width, height) of primary monitor."""
        if MSS_AVAILABLE:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                return monitor["width"], monitor["height"]
        elif PYAUTOGUI_AVAILABLE:
            return pyautogui.size()
        return (1920, 1080)  # Safe default

    async def stream_frames(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        max_frames: Optional[int] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Async generator that yields screen frames for WebSocket streaming.

        Yields dicts with:
          - frame: base64-encoded JPEG string
          - timestamp: float epoch
          - width: int
          - height: int
          - fps: int
        """
        self._streaming = True
        frame_count = 0
        width, height = self.get_screen_size()

        try:
            while self._streaming:
                frame_start = time.monotonic()

                if region:
                    data = self.capture_region(*region)
                    frame_w, frame_h = region[2], region[3]
                else:
                    data = self.capture_full()
                    frame_w, frame_h = width, height

                if data:
                    yield {
                        "type": "frame",
                        "frame": base64.b64encode(data).decode("utf-8"),
                        "timestamp": time.time(),
                        "width": frame_w,
                        "height": frame_h,
                        "fps": self.fps,
                        "frame_number": frame_count,
                    }
                    frame_count += 1

                if max_frames and frame_count >= max_frames:
                    break

                # Throttle to target FPS
                elapsed = time.monotonic() - frame_start
                sleep_time = self._frame_interval - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(0)  # yield control

        finally:
            self._streaming = False

    def stop_streaming(self):
        """Stop an active stream_frames generator."""
        self._streaming = False

    # ─── Private capture methods ────────────────────────────────────────────

    def _capture_mss(self) -> bytes:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            return self._mss_to_jpeg(img)

    def _capture_mss_region(self, x: int, y: int, width: int, height: int) -> bytes:
        with mss.mss() as sct:
            region = {"top": y, "left": x, "width": width, "height": height}
            img = sct.grab(region)
            return self._mss_to_jpeg(img)

    def _mss_to_jpeg(self, img) -> bytes:
        """Convert mss screenshot to JPEG bytes."""
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        return buf.getvalue()

    def _capture_pil(self) -> bytes:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        return buf.getvalue()

    def _capture_pil_region(self, x: int, y: int, width: int, height: int) -> bytes:
        img = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        return buf.getvalue()

    def _capture_pyautogui(self) -> bytes:
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        return buf.getvalue()
