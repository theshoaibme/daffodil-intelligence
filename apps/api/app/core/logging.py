"""Dev-friendly colored console logging (Next.js-inspired)."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"
_WHITE = "\033[37m"

_QUIET_LOGGERS = (
    "telegram",
    "telegram.ext",
    "telegram.ext.ExtBot",
    "telegram.ext.Application",
    "telegram.ext.Updater",
    "httpx",
    "httpcore",
    "httpcore.connection",
    "httpcore.http11",
    "urllib3",
    "asyncio",
    "watchfiles",
    "multipart",
    "sqlalchemy.engine",
    "langchain",
    "openai",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


class _DevLogFilter(logging.Filter):
    """Hide noisy framework logs in local dev."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name in _QUIET_LOGGERS:
            return False
        if record.name.startswith("uvicorn"):
            return False
        return True


class _ColorFormatter(logging.Formatter):
    _LEVEL_STYLES = {
        logging.DEBUG: (_DIM, "dbg"),
        logging.INFO: (_CYAN, "inf"),
        logging.WARNING: (_YELLOW, "wrn"),
        logging.ERROR: (_RED, "err"),
        logging.CRITICAL: (_RED + _BOLD, "crt"),
    }

    def format(self, record: logging.LogRecord) -> str:
        if record.name == "app.http":
            return record.getMessage()

        color, tag = self._LEVEL_STYLES.get(record.levelno, (_WHITE, "???"))
        name = record.name.removeprefix("app.")
        msg = record.getMessage()
        return f"{_DIM}{tag}{_RESET} {_MAGENTA}{name}{_RESET} {msg}"


def _println(*lines: str) -> None:
    for line in lines:
        print(line, flush=True)


def _level_from_name(name: str) -> int:
    return getattr(logging, name.upper(), logging.INFO)


def configure_logging(level: str = "INFO", *, quiet_libs: bool = True) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(_level_from_name(level))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ColorFormatter())
    handler.addFilter(_DevLogFilter())
    root.addHandler(handler)

    if quiet_libs:
        for name in _QUIET_LOGGERS:
            logging.getLogger(name).setLevel(logging.CRITICAL)

    logging.getLogger("app").setLevel(_level_from_name(level))


def log_startup_banner(
    *,
    port: int = 8000,
    telegram_enabled: bool = False,
    telegram_username: Optional[str] = None,
    db_url: str = "",
) -> None:
    local = f"http://localhost:{port}"
    _println(
        f"{_BOLD}▲ Daffodil Intelligence API{_RESET}",
        f"{_DIM}Local:{_RESET}    {_CYAN}{local}{_RESET}",
        f"{_DIM}Docs:{_RESET}     {_CYAN}{local}/docs{_RESET}",
        f"{_DIM}Health:{_RESET}   {_CYAN}{local}/health{_RESET}",
    )
    if telegram_enabled:
        handle = f"@{telegram_username}" if telegram_username else "polling"
        _println(f"{_DIM}Telegram:{_RESET} {_GREEN}{handle}{_RESET}")
    if db_url:
        safe = db_url.split("@")[-1] if "@" in db_url else db_url
        _println(f"{_DIM}Database:{_RESET} {safe}")


def log_http(method: str, path: str, status: int, duration_ms: float) -> None:
    if status >= 500:
        sc = f"{_RED}{status}{_RESET}"
    elif status >= 400:
        sc = f"{_YELLOW}{status}{_RESET}"
    else:
        sc = f"{_GREEN}{status}{_RESET}"
    _println(f"{_GREEN}{method:7}{_RESET} {path} {sc} {_DIM}in {duration_ms:.0f}ms{_RESET}")


_startup_t0: float | None = None


def mark_startup_begin() -> None:
    global _startup_t0
    _startup_t0 = time.perf_counter()


def log_startup_ready() -> None:
    elapsed = ""
    if _startup_t0 is not None:
        elapsed = f" {_DIM}in {time.perf_counter() - _startup_t0:.1f}s{_RESET}"
    _println(f"{_GREEN}✓{_RESET} {_BOLD}Ready{_RESET}{elapsed}")


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    return logging.getLogger(name)


app_logger = logging.getLogger("app")
agent_logger = logging.getLogger("app.agents")
api_logger = logging.getLogger("app.api")
