# Install

Always installs the **latest** from the default branch. CopyCat Kit **auto-updates** on `daffodil-kit start` (every 6h) or run `daffodil-kit update` manually.

**Copy buttons:** [install.html](install.html) · on GitHub, hover a code block → **Copy**

## One command

**Unix · macOS · WSL · Git Bash**

```bash
curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install | sh
```

**Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install.ps1 | iex
```

## From source

```bash
pip install -e packages/daffodil-kit
```

Editable installs skip auto-update.

## Auto-update

```bash
daffodil-kit update          # check now and upgrade if needed
daffodil-kit start           # checks every 6h, then starts daemon
daffodil-kit start --no-update
```

Disable: `DAFFODIL_KIT_AUTO_UPDATE=0` or `"auto_update": false` in `~/.daffodil-kit/config.json`

## Environment

| Variable | Purpose |
|----------|---------|
| `DAFFODIL_KIT_API_URL` | API URL in `~/.daffodil-kit/config.json` |
| `DAFFODIL_KIT_NATIVE` | `1` = build Rust capture backend |
| `DAFFODIL_KIT_INSTALL_SERVICE` | `1` = systemd / launchd / Task Scheduler |
| `DAFFODIL_KIT_AUTO_UPDATE` | `0` = disable auto-update on start |

## Verify

```bash
daffodil-kit version
daffodil-kit status
```
