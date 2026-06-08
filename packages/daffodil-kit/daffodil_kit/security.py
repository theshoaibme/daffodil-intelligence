"""Device pairing, command signing, and local config storage."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".daffodil-kit"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: Dict[str, Any]) -> None:
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate_device_secret() -> str:
    return secrets.token_hex(32)


def sign_command(secret: str, payload: str, timestamp: float) -> str:
    msg = f"{int(timestamp)}.{payload}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_command(secret: str, payload: str, timestamp: float, signature: str, max_age: int = 60) -> bool:
    if abs(time.time() - timestamp) > max_age:
        return False
    expected = sign_command(secret, payload, timestamp)
    return hmac.compare_digest(expected, signature)


def get_or_create_device_id() -> str:
    cfg = load_config()
    if "device_id" not in cfg:
        cfg["device_id"] = secrets.token_hex(16)
        save_config(cfg)
    return cfg["device_id"]


def store_pairing(device_secret: str, api_url: str, user_id: int, allowed_roots: Optional[list] = None) -> None:
    cfg = load_config()
    cfg.update({
        "device_secret": device_secret,
        "api_url": api_url.rstrip("/"),
        "user_id": user_id,
        "allowed_roots": allowed_roots or [str(Path.home())],
        "paired_at": time.time(),
    })
    save_config(cfg)


def get_device_secret() -> Optional[str]:
    return load_config().get("device_secret")


def get_allowed_roots() -> list[str]:
    return load_config().get("allowed_roots", [str(Path.home())])
