# daffodil-kit

CopyCat desktop daemon for **macOS · Linux · Windows** — screen capture, mouse/keyboard, record/replay, and a local-only credential vault.

**Install:** [install.html](install.html) (copy buttons) · [INSTALL.md](INSTALL.md)

## Quick start

```bash
daffodil-kit pair --api http://localhost:8000 --code 123456
daffodil-kit start
daffodil-kit status
```

Local-only: `daffodil-kit start --mode local` (WS on `:9477`).

## Features

- **Capture** — full screen or focus window; adaptive FPS/quality from latency
- **Input** — mouse, keyboard, macro record/replay (2× default speed)
- **Vault** — `daffodil-kit vault set` for local sudo/UAC passwords (encrypted, never uploaded)
- **Security** — pairing code + HMAC RPC; input lock during replay; audit log in `~/.daffodil-kit/logs/`
- **Auto-update** — `daffodil-kit update` or automatic on `start` (latest from GitHub)

Logs: `~/.daffodil-kit/logs/` · Version: `daffodil-kit version`
