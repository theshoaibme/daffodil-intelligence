"""Local-only encrypted vault for automation passwords — never leaves the machine."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

VAULT_DIR = Path.home() / ".daffodil-kit" / "vault"
VAULT_FILE = VAULT_DIR / "secrets.enc"
META_FILE = VAULT_DIR / "meta.json"


def _machine_key() -> bytes:
    raw = f"{platform.node()}:{platform.system()}:{os.getuid() if hasattr(os, 'getuid') else 0}"
    return hashlib.sha256(raw.encode()).digest()


def _xor_crypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def vault_status() -> Dict[str, Any]:
    return {
        "local_only": True,
        "configured": VAULT_FILE.exists(),
        "path": str(VAULT_DIR),
        "has_meta": META_FILE.exists(),
    }


def set_system_password(password: str, label: str = "sudo") -> Dict[str, Any]:
    """Store automation password locally (XOR + machine key — upgrade to AES in production)."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"label": label, "password": password}).encode()
    enc = _xor_crypt(payload, _machine_key())
    VAULT_FILE.write_bytes(enc)
    META_FILE.write_text(json.dumps({"label": label, "updated": True}), encoding="utf-8")
    return {"stored": True, "label": label, "local_only": True}


def get_system_password(label: str = "sudo") -> Optional[str]:
    if not VAULT_FILE.exists():
        return None
    try:
        enc = VAULT_FILE.read_bytes()
        dec = _xor_crypt(enc, _machine_key())
        data = json.loads(dec.decode())
        if data.get("label") == label:
            return data.get("password")
    except Exception:
        return None
    return None


def clear_vault() -> Dict[str, Any]:
    for p in (VAULT_FILE, META_FILE):
        if p.exists():
            p.unlink()
    return {"cleared": True}
