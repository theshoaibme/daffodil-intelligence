"""Shared thread pool for blocking desktop I/O."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="computer-use")


async def run_blocking(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = asyncio.get_running_loop()
    if kwargs:
        fn = partial(fn, **kwargs)
    return await loop.run_in_executor(_EXECUTOR, fn, *args)
