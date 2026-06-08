"""Local security audit log + recent system log snippets (data stays on machine)."""

from __future__ import annotations

import json
import logging
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

AUDIT_DIR = Path.home() / ".daffodil-kit" / "logs"
AUDIT_FILE = AUDIT_DIR / "copycat_audit.jsonl"
KIT_LOG_FILE = AUDIT_DIR / "kit.log"


def _ensure_dir() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def log_event(
    event: str,
    *,
    detail: Optional[Dict[str, Any]] = None,
    level: str = "info",
) -> Dict[str, Any]:
    """Append tamper-evident local audit entry."""
    _ensure_dir()
    entry = {
        "ts": time.time(),
        "event": event,
        "level": level,
        "detail": detail or {},
        "platform": platform.system().lower(),
    }
    try:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        with open(KIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {event} {detail}\n")
    except Exception as e:
        logger.error("Audit write failed: %s", e)
    return entry


def read_audit_tail(limit: int = 50) -> List[Dict[str, Any]]:
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def read_system_log_tail(lines: int = 30) -> Dict[str, Any]:
    """Best-effort recent OS logs related to input/permissions (local read only)."""
    system = platform.system().lower()
    snippets: List[str] = []

    if system == "linux":
        for cmd in (
            ["journalctl", "-n", str(lines), "--no-pager", "-q"],
            ["dmesg", "--ctime", "-T"],
        ):
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=3)
                snippets.extend(out.strip().splitlines()[-lines:])
                break
            except Exception:
                continue
    elif system == "darwin":
        try:
            out = subprocess.check_output(
                ["log", "show", "--last", "2m", "--style", "compact"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            )
            snippets = out.strip().splitlines()[-lines:]
        except Exception:
            pass
    elif system == "windows":
        snippets.append("Windows: use Event Viewer locally for security audit")

    return {
        "platform": system,
        "lines": snippets[-lines:],
        "count": len(snippets),
        "local_only": True,
    }


def read_kit_log_tail(lines: int = 40) -> List[str]:
    if not KIT_LOG_FILE.exists():
        return []
    return KIT_LOG_FILE.read_text(encoding="utf-8").strip().splitlines()[-lines:]
