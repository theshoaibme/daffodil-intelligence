from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

from .logging import log_http


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        # Skip noisy health checks in dev
        if request.url.path not in ("/health", "/favicon.ico"):
            log_http(request.method, request.url.path, response.status_code, duration_ms)
        return response