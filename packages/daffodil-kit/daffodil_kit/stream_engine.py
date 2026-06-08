"""Adaptive streaming — dynamic FPS/quality from measured latency (not hardcoded)."""

from __future__ import annotations

import asyncio
import base64
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from .permissions import request_focus_region as get_focus_region
from .rust_backend import capture_frame, is_rust_available
from .runtime import run_blocking


@dataclass
class StreamConfig:
    min_fps: int = 5
    max_fps: int = 30
    min_quality: int = 35
    max_quality: int = 75
    min_scale: float = 0.4
    max_scale: float = 1.0
    focus_mode: bool = False
    target_latency_ms: float = 80.0

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "StreamConfig":
        if not d:
            return cls()
        return cls(
            min_fps=int(d.get("min_fps", 5)),
            max_fps=int(d.get("max_fps", 30)),
            min_quality=int(d.get("min_quality", 35)),
            max_quality=int(d.get("max_quality", 75)),
            min_scale=float(d.get("min_scale", 0.4)),
            max_scale=float(d.get("max_scale", 1.0)),
            focus_mode=bool(d.get("focus_mode", False)),
            target_latency_ms=float(d.get("target_latency_ms", 80)),
        )


@dataclass
class StreamState:
    fps: float = 12.0
    quality: int = 55
    scale: float = 0.75
    region: Optional[Tuple[int, int, int, int]] = None
    frame_count: int = 0
    avg_latency_ms: float = 50.0
    backend: str = "python"


class AdaptiveStreamEngine:
    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.state = StreamState(backend="rust" if is_rust_available() else "python")
        self._running = False

    def _adapt(self, latency_ms: float) -> None:
        c = self.config
        s = self.state
        s.avg_latency_ms = s.avg_latency_ms * 0.8 + latency_ms * 0.2
        target = c.target_latency_ms

        if s.avg_latency_ms > target * 1.3:
            s.fps = max(c.min_fps, s.fps - 2)
            s.quality = max(c.min_quality, s.quality - 5)
            s.scale = max(c.min_scale, s.scale - 0.05)
        elif s.avg_latency_ms < target * 0.7:
            s.fps = min(c.max_fps, s.fps + 1)
            s.quality = min(c.max_quality, s.quality + 2)
            s.scale = min(c.max_scale, s.scale + 0.02)

    async def frames(self) -> AsyncGenerator[Dict[str, Any], None]:
        self._running = True
        if self.config.focus_mode:
            focus = await run_blocking(get_focus_region)
            reg = focus.get("region")
            if reg:
                self.state.region = tuple(reg)

        while self._running:
            t0 = time.monotonic()
            region = self.state.region
            frame = await run_blocking(
                capture_frame,
                self.state.quality,
                self.state.scale,
                region,
            )
            elapsed_ms = (time.monotonic() - t0) * 1000
            self._adapt(elapsed_ms)

            if frame:
                self.state.frame_count += 1
                yield {
                    "type": "frame",
                    "frame": base64.b64encode(frame["jpeg"]).decode("ascii"),
                    "width": frame["width"],
                    "height": frame["height"],
                    "timestamp": time.time(),
                    "frame_number": self.state.frame_count,
                    "fps": round(self.state.fps, 1),
                    "quality": self.state.quality,
                    "scale": round(self.state.scale, 2),
                    "latency_ms": round(elapsed_ms, 1),
                    "backend": frame.get("backend", self.state.backend),
                    "focus_mode": self.config.focus_mode,
                }

            interval = 1.0 / max(self.state.fps, 1)
            sleep_for = interval - (time.monotonic() - t0)
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)

    def stop(self) -> None:
        self._running = False

    def update_config(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        self.config = StreamConfig.from_dict({**self.config.__dict__, **patch})
        if patch.get("focus_mode") is True:
            focus = get_focus_region()
            if focus.get("region"):
                self.state.region = tuple(focus["region"])
        elif patch.get("focus_mode") is False:
            self.state.region = None
        return self.status()

    def status(self) -> Dict[str, Any]:
        return {
            "fps": round(self.state.fps, 1),
            "quality": self.state.quality,
            "scale": round(self.state.scale, 2),
            "region": list(self.state.region) if self.state.region else None,
            "backend": self.state.backend,
            "frames": self.state.frame_count,
            "avg_latency_ms": round(self.state.avg_latency_ms, 1),
            "config": self.config.__dict__,
        }
