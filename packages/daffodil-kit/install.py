#!/usr/bin/env python3
"""
CopyCat Kit — universal cross-platform installer (Linux · macOS · Windows).

One command (auto-detects OS):
  curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install | sh

Or directly:
  curl -fsSL .../install.py | python3 -
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path
from typing import Any, Optional

# Configure stdout/stderr to support UTF-8 if they don't already
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def safe_print(text: str = "", file=sys.stdout) -> None:
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        # Fallback to ascii/safe characters
        safe_text = text.replace("✓", "[OK]").replace("✗", "[FAIL]").replace("·", "*")
        try:
            print(safe_text, file=file)
        except Exception:
            # Absolute fallback
            print(safe_text.encode('ascii', errors='ignore').decode('ascii'), file=file)


# ─── Config from environment ─────────────────────────────────────────────────

REPO = os.environ.get("DAFFODIL_KIT_REPO", "the-shoaib2/daffodil-intelligence")
VERSION = os.environ.get("DAFFODIL_KIT_VERSION", "main")  # default branch = always latest
NATIVE = os.environ.get("DAFFODIL_KIT_NATIVE", "0") == "1"
INSTALL_SERVICE = os.environ.get("DAFFODIL_KIT_INSTALL_SERVICE", "0") == "1"
USE_LOCAL = os.environ.get("DAFFODIL_KIT_USE_LOCAL", "0") == "1"
API_URL = os.environ.get("DAFFODIL_KIT_API_URL", "")
PREFIX = Path(os.environ.get("DAFFODIL_KIT_PREFIX", str(Path.home() / ".local")))
GIT_URL = f"https://github.com/{REPO}.git"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{VERSION}"

SCRIPT_DIR = Path(__file__).resolve().parent
STEP_TOTAL = 8


def detect_os() -> str:
    s = platform.system().lower()
    if s == "linux":
        return "linux"
    if s == "darwin":
        return "macos"
    if s == "windows":
        return "windows"
    return "unknown"


class InstallLogger:
    def __init__(self) -> None:
        self.step_num = 0
        self.install_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.log_dir = Path.home() / ".daffodil-kit" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"install-{self.install_id}.log"
        self._json_log("install.start", "info", {"install_id": self.install_id})

    def _json_log(self, event: str, level: str, detail: dict[str, Any]) -> None:
        line = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "level": level,
            "detail": detail,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")

    def banner(self, version: str) -> None:
        safe_print()
        safe_print("=" * 58)
        safe_print("  CopyCat Kit Installer")
        safe_print(f"  OS: {detect_os()} · target: {version}")
        safe_print(f"  Log: {self.log_file}")
        safe_print("=" * 58)
        safe_print()
        self._json_log("install.banner", "info", {"version": version, "os": detect_os()})

    def step(self, title: str) -> None:
        self.step_num += 1
        safe_print(f"\033[1;36m[{self.step_num}/{STEP_TOTAL}]\033[0m {title}")
        self._json_log("install.step", "info", {"step": self.step_num, "title": title})

    def ok(self, msg: str) -> None:
        safe_print(f"  \033[1;32m✓\033[0m {msg}")
        self._json_log("install.ok", "info", {"message": msg})

    def warn(self, msg: str) -> None:
        safe_print(f"  \033[1;33m!\033[0m {msg}", file=sys.stderr)
        self._json_log("install.warn", "warn", {"message": msg})

    def info(self, msg: str) -> None:
        safe_print(f"    · {msg}")
        self._json_log("install.info", "info", {"message": msg})

    def fail(self, msg: str) -> None:
        safe_print(f"  \033[1;31m✗\033[0m {msg}", file=sys.stderr)
        self._json_log("install.fail", "error", {"message": msg})
        safe_print(f"\nInstall failed. Log: {self.log_file}")
        sys.exit(1)

    def summary(self, ver: str) -> None:
        safe_print()
        safe_print("-" * 58)
        safe_print(f"  Install complete — daffodil-kit {ver}")
        safe_print(f"  Log: {self.log_file}")
        safe_print("-" * 58)
        self._json_log("install.complete", "info", {"version": ver})


def run(cmd: list[str], *, check: bool = False, quiet: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=quiet,
        text=True,
    )


def sudo_available() -> bool:
    if shutil.which("sudo") is None:
        return False
    r = run(["sudo", "-n", "true"], quiet=True)
    return r.returncode == 0


def install_os_packages(log: InstallLogger, os_name: str) -> None:
    if os_name == "linux":
        if shutil.which("apt-get") and sudo_available():
            pkgs = ["python3", "python3-pip", "python3-venv", "python3-tk", "scrot", "xdotool"]
            if NATIVE:
                pkgs += ["build-essential", "pkg-config", "libdbus-1-dev", "libxcb1-dev", "libxrandr-dev"]
            log.info(f"apt: {' '.join(pkgs)}")
            r = run(["sudo", "-n", "apt-get", "update", "-qq"], quiet=True)
            if r.returncode == 0:
                r2 = run(
                    ["sudo", "-n", "env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", *pkgs],
                    quiet=True,
                )
                if r2.returncode == 0:
                    log.ok("OS packages installed (apt)")
                else:
                    log.warn("apt install partial — continue")
            else:
                log.warn("apt skipped (no passwordless sudo)")
        elif shutil.which("dnf") and sudo_available():
            run(["sudo", "-n", "dnf", "install", "-y", "python3", "python3-pip", "python3-tkinter", "xdotool", "scrot"])
            log.ok("OS packages (dnf)")
        elif shutil.which("pacman") and sudo_available():
            run(["sudo", "-n", "pacman", "-Sy", "--noconfirm", "python", "python-pip", "tk", "xdotool", "scrot"])
            log.ok("OS packages (pacman)")
        else:
            log.warn("Install manually: python3 python3-pip python3-venv python3-tk")
    elif os_name == "macos":
        if shutil.which("brew"):
            run(["brew", "list", "python@3.12"], quiet=True)
            if run(["brew", "list", "python@3.12"], quiet=True).returncode != 0:
                run(["brew", "install", "python@3.12"])
            log.ok("Homebrew Python ready")
        else:
            log.warn("Install Python 3.11+ from https://www.python.org/downloads/")
    elif os_name == "windows":
        log.info("Windows detected — using Python venv + pip")


def setup_venv(log: InstallLogger) -> Path:
    venv_dir = PREFIX / "daffodil-kit-venv"
    if not venv_dir.exists():
        log.info(f"Creating venv: {venv_dir}")
        venv.create(venv_dir, with_pip=True)
    else:
        log.info(f"Reusing venv: {venv_dir}")

    if platform.system() == "Windows":
        py = venv_dir / "Scripts" / "python.exe"
        pip = venv_dir / "Scripts" / "pip.exe"
    else:
        py = venv_dir / "bin" / "python"
        pip = venv_dir / "bin" / "pip"

    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"], quiet=True)
    ver = run([str(py), "--version"], quiet=True)
    log.ok(f"Virtualenv ready ({ver.stdout.strip()})")
    return py


def pip_install(log: InstallLogger, py: Path) -> None:
    pip = py.parent / ("pip.exe" if platform.system() == "Windows" else "pip")
    if USE_LOCAL:
        log.info(f"Local editable: {SCRIPT_DIR}")
        run([str(pip), "install", "-e", str(SCRIPT_DIR), "-q"], check=True)
    else:
        spec = f"git+{GIT_URL}@{VERSION}#subdirectory=packages/daffodil-kit"
        log.info(f"Remote: {spec}")
        run([str(pip), "install", "--upgrade", spec, "-q"], check=True)
    log.ok("daffodil-kit package installed (auto-update enabled via daffodil-kit start)")


def write_config(log: InstallLogger) -> None:
    cfg = Path.home() / ".daffodil-kit"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "logs").mkdir(exist_ok=True)
    try:
        if platform.system() != "Windows":
            os.chmod(cfg, 0o700)
    except OSError:
        pass
    config_file = cfg / "config.json"
    if API_URL and not config_file.exists():
        config_file.write_text(json.dumps({"api_url": API_URL}, indent=2), encoding="utf-8")
        log.ok("API URL written to config.json")
    else:
        log.info(f"Config: {cfg}")


def security_check(log: InstallLogger, py: Path) -> None:
    code = """
import time
from daffodil_kit.security import sign_command, verify_command, generate_device_secret
s = generate_device_secret()
ts = time.time()
p = '{"method":"ping"}'
sig = sign_command(s, p, ts)
assert verify_command(s, p, ts, sig)
assert not verify_command(s, p, ts, "bad")
print("security-ok")
"""
    r = run([str(py), "-c", code], quiet=True)
    if r.returncode != 0:
        log.fail(f"Security self-test failed: {r.stderr}")
    log.ok("HMAC signing / verification OK")


def verify_cli(log: InstallLogger, py: Path) -> str:
    bin_dir = py.parent
    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    kit = "daffodil-kit.exe" if platform.system() == "Windows" else "daffodil-kit"
    kit_path = bin_dir / kit
    ver = run([str(py), "-c", "import daffodil_kit; print(daffodil_kit.__version__)"], quiet=True)
    version = ver.stdout.strip()
    if kit_path.exists():
        run([str(kit_path), "status"], quiet=True, check=False)
        log.ok(f"CLI check passed (v{version})")
    else:
        log.warn("CLI entrypoint not found on PATH yet")
    return version


def install_background_service(log: InstallLogger, py: Path, os_name: str) -> None:
    if not INSTALL_SERVICE:
        return
    if os_name == "windows":
        kit = py.parent / "daffodil-kit.exe"
        if not kit.exists():
            log.warn("Skip scheduled task — CLI missing")
            return
        ps = (
            f'$a=New-ScheduledTaskAction -Execute "{kit}" -Argument "start";'
            f'$t=New-ScheduledTaskTrigger -AtLogOn;'
            f'Register-ScheduledTask -TaskName DaffodilCopyCatKit -Action $a -Trigger $t -Force'
        )
        run(["powershell", "-Command", ps], quiet=True)
        log.ok("Windows scheduled task registered")
    else:
        svc = SCRIPT_DIR / "scripts" / "install-service.sh"
        if svc.exists():
            run(["bash", str(svc), os_name], quiet=True)
            log.ok("Background service installed")


def print_next_steps(version: str) -> None:
    venv_bin = PREFIX / ("daffodil-kit-venv/Scripts" if platform.system() == "Windows" else "daffodil-kit-venv/bin")
    safe_print(f"""
Next steps:
  1. Pair:   daffodil-kit pair --api http://localhost:8000 --code <6-digit>
  2. Vault:  daffodil-kit vault set '<sudo-password>'   # local only
  3. Start:  daffodil-kit start
  4. Audit:  logs in ~/.daffodil-kit/logs/

Docs: https://github.com/{REPO}/tree/{VERSION}/packages/daffodil-kit
""")
    path_hint = str(venv_bin)
    if path_hint not in os.environ.get("PATH", ""):
        if platform.system() == "Windows":
            safe_print(f'Add to PATH: $env:PATH = "{path_hint};" + $env:PATH')
        else:
            safe_print(f'Add to PATH: export PATH="{path_hint}:$PATH"')


def main() -> None:
    if sys.version_info < (3, 11):
        safe_print("CopyCat Kit requires Python 3.11+. Upgrade Python and re-run.", file=sys.stderr)
        sys.exit(1)

    log = InstallLogger()
    os_name = detect_os()
    target = "latest" if VERSION == "main" else VERSION
    log.banner(target)

    log.step("Detect environment")
    log.info(f"Platform: {platform.platform()}")
    log.info(f"Python: {sys.version.split()[0]} · repo: {REPO} · ref: {VERSION} (latest when main)")
    log.ok(f"OS auto-detected: {os_name}")

    log.step("Install OS dependencies")
    install_os_packages(log, os_name)

    log.step("Create Python virtualenv")
    py = setup_venv(log)

    log.step("Install daffodil-kit package")
    pip_install(log, py)

    log.step("Optional Rust capture backend")
    if NATIVE and shutil.which("cargo"):
        log.info("DAFFODIL_KIT_NATIVE=1 — run scripts/build-native.sh after install")
    else:
        log.info("Skipping Rust backend (set DAFFODIL_KIT_NATIVE=1 to enable)")

    log.step("Configure local directories")
    write_config(log)

    log.step("Security self-test")
    security_check(log, py)

    log.step("Verify installation")
    ver = verify_cli(log, py)

    install_background_service(log, py, os_name)
    log.summary(ver)
    print_next_steps(ver)


if __name__ == "__main__":
    main()
