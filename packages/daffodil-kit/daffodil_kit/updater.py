"""Check for and install the latest CopyCat Kit from the default branch."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Optional

import httpx

from . import __version__
from .security import load_config, save_config

DEFAULT_REPO = os.environ.get("DAFFODIL_KIT_REPO", "the-shoaib2/daffodil-intelligence")
DEFAULT_REF = os.environ.get("DAFFODIL_KIT_REF", "main")
CHECK_INTERVAL_SEC = int(os.environ.get("DAFFODIL_KIT_UPDATE_INTERVAL", str(6 * 3600)))


def parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.strip().split("."):
        digits = "".join(c for c in piece if c.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else (0,)


def is_newer(latest: str, installed: str) -> bool:
    return parse_version(latest) > parse_version(installed)


def version_url(repo: str = DEFAULT_REPO, ref: str = DEFAULT_REF) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{ref}/packages/daffodil-kit/VERSION"


def fetch_latest_version(repo: str = DEFAULT_REPO) -> str:
    resp = httpx.get(version_url(repo), timeout=20, follow_redirects=True)
    resp.raise_for_status()
    return resp.text.strip()


def is_editable_install() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in proc.stdout.splitlines():
        low = line.lower()
        if "daffodil-kit" in low and line.startswith("-e"):
            return True
    return False


def auto_update_enabled() -> bool:
    if os.environ.get("DAFFODIL_KIT_AUTO_UPDATE", "1") == "0":
        return False
    cfg = load_config()
    return cfg.get("auto_update", True) is not False


def pip_git_spec(repo: str = DEFAULT_REPO, ref: str = DEFAULT_REF) -> str:
    return f"git+https://github.com/{repo}.git@{ref}#subdirectory=packages/daffodil-kit"


def upgrade_package(repo: str = DEFAULT_REPO, ref: str = DEFAULT_REF) -> str:
    spec = pip_git_spec(repo, ref)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", spec],
        check=True,
    )
    return fetch_latest_version(repo)


def check_for_update(repo: str = DEFAULT_REPO) -> Optional[str]:
    latest = fetch_latest_version(repo)
    if is_newer(latest, __version__):
        return latest
    return None


def record_update_check() -> None:
    cfg = load_config()
    cfg["last_update_check"] = time.time()
    save_config(cfg)


def should_check_now() -> bool:
    cfg = load_config()
    last = float(cfg.get("last_update_check", 0))
    return time.time() - last >= CHECK_INTERVAL_SEC


def run_update(*, force_check: bool = False, quiet: bool = False) -> dict:
    """Return {updated, latest, installed, message}."""
    installed = __version__
    if is_editable_install():
        return {
            "updated": False,
            "latest": installed,
            "installed": installed,
            "message": "Editable install — skip auto-update",
        }

    if not force_check and not should_check_now():
        return {
            "updated": False,
            "latest": installed,
            "installed": installed,
            "message": "Update check skipped (recently checked)",
        }

    record_update_check()
    try:
        latest = fetch_latest_version()
    except httpx.HTTPError as exc:
        return {
            "updated": False,
            "latest": None,
            "installed": installed,
            "message": f"Could not fetch latest version: {exc}",
        }

    if not is_newer(latest, installed):
        return {
            "updated": False,
            "latest": latest,
            "installed": installed,
            "message": f"Already on latest ({installed})",
        }

    if not quiet:
        print(f"Updating daffodil-kit {installed} → {latest}…")
    try:
        upgrade_package()
    except subprocess.CalledProcessError as exc:
        return {
            "updated": False,
            "latest": latest,
            "installed": installed,
            "message": f"Upgrade failed: {exc}",
        }

    new_ver = fetch_latest_version()
    return {
        "updated": True,
        "latest": new_ver,
        "installed": installed,
        "message": f"Updated {installed} → {new_ver}",
    }


def maybe_auto_update() -> bool:
    """If an upgrade ran, return True so the CLI can re-exec."""
    if not auto_update_enabled():
        return False
    result = run_update(force_check=False, quiet=False)
    if result["updated"]:
        print(result["message"])
        return True
    return False


def _cli_args() -> list[str]:
    argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] == "-m" and argv[1] == "daffodil_kit.cli":
        return argv[2:]
    return argv


def reexec_cli() -> None:
    os.execv(sys.executable, [sys.executable, "-m", "daffodil_kit.cli", *_cli_args()])
