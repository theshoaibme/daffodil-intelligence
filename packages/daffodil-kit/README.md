# daffodil-kit

Cross-platform desktop daemon (macOS / Linux / Windows) for Daffodil CopyCat — ultra-fast screen capture, mouse/keyboard, macro record/replay, focus-window capture, and **local-only** credential vault.

## Install

### One-line (Linux / macOS / Git Bash)

Latest from `main`:

```bash
curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.sh | bash
```

Pinned release:

```bash
DAFFODIL_KIT_VERSION=copycat-v0.1.0 curl -fsSL \
  https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/copycat-v0.1.0/packages/daffodil-kit/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.ps1 | iex
```

### From source (developers)

```bash
pip install -e packages/daffodil-kit
```

### Environment options

| Variable | Default | Purpose |
|----------|---------|---------|
| `DAFFODIL_KIT_REPO` | `the-shoaib2/daffodil-intelligence` | GitHub repo |
| `DAFFODIL_KIT_VERSION` | `main` | Branch or tag (`copycat-v0.1.0`) |
| `DAFFODIL_KIT_NATIVE` | `0` | Build Rust capture backend |
| `DAFFODIL_KIT_INSTALL_SERVICE` | `0` | systemd (Linux) / launchd (macOS) / Task (Windows) |
| `DAFFODIL_KIT_API_URL` | — | Pre-fill API URL in `~/.daffodil-kit/config.json` |
| `DAFFODIL_KIT_USE_LOCAL` | `0` | Install from current checkout (`1` = CI/dev) |

Install writes a structured log to `~/.daffodil-kit/logs/install-<timestamp>.log` (human output + JSON-lines for audit).

Post-install verify:

```bash
bash packages/daffodil-kit/scripts/verify-install.sh
```

### Optional: Rust capture backend (~3× faster JPEG)

```bash
# Linux (Kali/Debian) — one-time system deps:
sudo apt install libdbus-1-dev libxcb1-dev libxrandr-dev pkg-config

bash packages/daffodil-kit/scripts/build-native.sh
```

## Pair & run

```bash
daffodil-kit pair --api http://localhost:8000 --code 123456
daffodil-kit start          # connects to API (cloud mode)
daffodil-kit start --mode local   # standalone WS on :9477
```

## Permissions (all OS)

| OS | Screen | Input | Focus window |
|----|--------|-------|----------------|
| macOS | Privacy → Screen Recording | Privacy → Accessibility | osascript (built-in) |
| Linux X11 | DISPLAY + mss/xcap | pyautogui / input group | xdotool |
| Linux Wayland | portal ScreenCast dialog | same | portal |
| Windows | interactive session | pyautogui | — |

Check: `daffodil-kit status` or API `GET /api/kit/permissions`

## Local automation password (never leaves machine)

```bash
daffodil-kit vault set 'your-sudo-password' --label sudo
daffodil-kit vault status
```

Used by CopyCat replay when sudo/UAC prompts appear. Encrypted with machine-bound key in `~/.daffodil-kit/vault/`.

## Adaptive streaming (not hardcoded)

Stream FPS/quality/scale adapt to measured frame latency. Configure from UI toolbar or:

```json
POST /api/kit/stream/configure
{"max_fps": 30, "focus_mode": true, "target_latency_ms": 80}
```

## Security model

- Pairing: 6-digit one-time code, per-device HMAC-signed RPC
- Data: recordings + vault **local only**; API relays commands when kit is online
- Remote access: only through authenticated API + paired device

## Versioning, CI/CD & releases

| Item | Path / command |
|------|----------------|
| Version source | `packages/daffodil-kit/VERSION` |
| Sync manifests | `bash packages/daffodil-kit/scripts/sync-version.sh` |
| Bump + tag helper | `bash packages/daffodil-kit/scripts/release.sh 0.1.1` |
| Local full CI | `bash packages/daffodil-kit/scripts/ci-local.sh` |
| GitHub workflow | `.github/workflows/copycat-kit.yml` |

**CI pipeline** (on push/PR to `packages/daffodil-kit/`):

1. Version sync check (`VERSION` = `pyproject.toml` = `__init__.py` = `Cargo.toml`)
2. Ruff lint + format
3. Tests on Ubuntu / macOS / Windows × Python 3.11 & 3.12 (security, audit, copycat guard, coverage)
4. End-to-end `install.sh` / `install.ps1` + `verify-install.sh`
5. On tag `copycat-v*`: build wheel/sdist, SHA256 checksums, GitHub Release with install scripts

```bash
git tag copycat-v0.1.0 && git push origin copycat-v0.1.0
```

Check installed version: `daffodil-kit version`

## Security features (tested in CI)

- **HMAC-signed RPC** — per-device secret, 60s timestamp window (`daffodil_kit.security`)
- **CopyCat input lock** — blocks mouse/keyboard during replay (`copycat_guard`, `input_lock`)
- **Local audit log** — `~/.daffodil-kit/logs/copycat_audit.jsonl` + `kit.log`
- **Encrypted vault** — machine-bound password storage, never sent to cloud (`vault.py`)
- **Config permissions** — `~/.daffodil-kit` created mode `700` on install

## Performance

- Persistent MSS / Rust xcap capture
- `pyautogui.PAUSE = 0`, concurrent RPC (8 in-flight)
- Adaptive stream targets ~80ms latency
- Replay defaults: 2× speed, skip mouse moves
