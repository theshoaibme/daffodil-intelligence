"""Outbound WebSocket client — concurrent command handling, fast reconnect."""

from __future__ import annotations

import asyncio
import json
import logging

import websockets

from .daemon import _handle_method, _verify_signed
from .protocol import make_response, parse_message
from .security import load_config

logger = logging.getLogger(__name__)

# Cap parallel agent commands (screenshot + click simultaneously)
_MAX_INFLIGHT = 8
_inflight = asyncio.Semaphore(_MAX_INFLIGHT)


async def _process_command(ws, raw: str) -> None:
    async with _inflight:
        try:
            msg = parse_message(raw)
            if "method" not in msg:
                return
            req_id = msg.get("id", "0")
            params = dict(msg.get("params") or {})
            if not _verify_signed(params):
                await ws.send(make_response(req_id, error={"code": 401, "message": "Invalid signature"}))
                return
            result = await _handle_method(msg["method"], params)
            await ws.send(make_response(req_id, result=result))
        except Exception as e:
            logger.exception("Command error")
            await ws.send(make_response("0", error={"code": -32603, "message": str(e)}))


async def connect_to_api() -> None:
    cfg = load_config()
    api_url = cfg.get("api_url", "").rstrip("/")
    device_id = cfg.get("device_id")
    if not api_url or not device_id:
        raise RuntimeError("Not paired. Run: daffodil-kit pair")

    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
    uri = f"{ws_url}/api/kit/ws/{device_id}"

    while True:
        try:
            logger.info("Connecting to %s", uri)
            async with websockets.connect(
                uri,
                compression=None,
                max_size=16 * 1024 * 1024,
                ping_interval=20,
                ping_timeout=10,
            ) as ws:
                await ws.send(json.dumps({"type": "hello", "device_id": device_id}))
                pending: set[asyncio.Task] = set()
                async for raw in ws:
                    task = asyncio.create_task(_process_command(ws, raw))
                    pending.add(task)
                    task.add_done_callback(pending.discard)
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
        except Exception as e:
            logger.warning("Connection lost: %s — retry in 2s", e)
            await asyncio.sleep(2)
