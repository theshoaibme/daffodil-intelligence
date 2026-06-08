"""Adaptive screen streaming for API — uses daffodil-kit engine when available."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

logger = logging.getLogger(__name__)

_engine_cls = None


def _load_engine():
    global _engine_cls
    if _engine_cls is not None:
        return _engine_cls
    try:
        kit_root = Path(__file__).resolve().parents[4] / "packages" / "daffodil-kit"
        if kit_root.exists() and str(kit_root) not in sys.path:
            sys.path.insert(0, str(kit_root))
        from daffodil_kit.stream_engine import AdaptiveStreamEngine, StreamConfig
        _engine_cls = (AdaptiveStreamEngine, StreamConfig)
        return _engine_cls
    except Exception as e:
        logger.warning("Kit stream engine unavailable: %s", e)
        _engine_cls = (None, None)
        return _engine_cls


async def adaptive_frames(config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
    loaded = _load_engine()
    Engine, Config = loaded
    if Engine and Config:
        engine = Engine(Config.from_dict(config))
        async for frame in engine.frames():
            yield frame
        return

    # Minimal fallback adaptive loop
    from ..computer_use.fast_capture import get_fast_capture
    from ..computer_use.runtime import run_blocking

    quality = 55
    scale = 0.75
    fps = 12.0
    cap = get_fast_capture(quality=quality, scale=scale)
    n = 0
    while True:
        t0 = asyncio.get_event_loop().time()
        b64 = await run_blocking(cap.capture_base64)
        w, h = cap.get_screen_size()
        if b64:
            n += 1
            yield {
                "type": "frame",
                "frame": b64,
                "width": w,
                "height": h,
                "timestamp": t0,
                "frame_number": n,
                "fps": fps,
                "backend": "python",
            }
        elapsed = asyncio.get_event_loop().time() - t0
        await asyncio.sleep(max(0, 1.0 / fps - elapsed))
