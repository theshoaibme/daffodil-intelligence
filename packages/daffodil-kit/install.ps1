# CopyCat Kit (daffodil-kit) — Windows PowerShell installer
#   irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.ps1 | iex
# Pin: $env:DAFFODIL_KIT_VERSION = "copycat-v0.1.0"

$ErrorActionPreference = "Stop"

$Repo = if ($env:DAFFODIL_KIT_REPO) { $env:DAFFODIL_KIT_REPO } else { "the-shoaib2/daffodil-intelligence" }
$Version = if ($env:DAFFODIL_KIT_VERSION) { $env:DAFFODIL_KIT_VERSION } else { "main" }
$Prefix = if ($env:DAFFODIL_KIT_PREFIX) { $env:DAFFODIL_KIT_PREFIX } else { "$env:USERPROFILE\.local" }
$UseLocal = $env:DAFFODIL_KIT_USE_LOCAL -eq "1"
$GitUrl = "https://github.com/$Repo.git"
$LogDir = Join-Path $env:USERPROFILE ".daffodil-kit\logs"
$InstallId = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$LogFile = Join-Path $LogDir "install-$InstallId.log"
$Step = 0
$StepTotal = 7

function Write-JsonLog($event, $level, $detail) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $line = @{ ts = (Get-Date).ToUniversalTime().ToString("o"); event = $event; level = $level; detail = $detail } | ConvertTo-Json -Compress
    Add-Content -Path $LogFile -Value $line
}

function Write-Banner {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    Write-Host ""
    Write-Host "=========================================================="
    Write-Host "  CopyCat Kit Installer (Windows)"
    Write-Host "  Version target: $Version"
    Write-Host "  Log: $LogFile"
    Write-Host "=========================================================="
    Write-Host ""
    Write-JsonLog "install.banner" "info" @{ version = $Version }
}

function Write-Step($title) {
    $script:Step++
    Write-Host "[$Step/$StepTotal] $title" -ForegroundColor Cyan
    Write-JsonLog "install.step" "info" @{ step = $Step; title = $title }
}

function Write-Ok($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
    Write-JsonLog "install.ok" "info" @{ message = $msg }
}

function Write-WarnMsg($msg) {
    Write-Host "  [!] $msg" -ForegroundColor Yellow
    Write-JsonLog "install.warn" "warn" @{ message = $msg }
}

function Write-Fail($msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    Write-JsonLog "install.fail" "error" @{ message = $msg }
    Write-Host "Install failed. Log: $LogFile"
    exit 1
}

function Find-Python {
    foreach ($c in @(@("py", "-3.12"), @("py", "-3.11"), @("py", "-3"), @("python3"), @("python"))) {
        try {
            $ver = & $c[0] $c[1..($c.Length-1)] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver -match "^3\.(1[1-9]|[2-9][0-9])") { return $c }
        } catch { continue }
    }
    Write-Fail "Python 3.11+ required — https://www.python.org/downloads/"
}

function Ensure-Venv($pyArgs) {
    $venv = Join-Path $Prefix "daffodil-kit-venv"
    if (-not (Test-Path $venv)) {
        & $pyArgs[0] $pyArgs[1..($pyArgs.Length-1)] -m venv $venv
    }
    $activate = Join-Path $venv "Scripts\Activate.ps1"
    . $activate
    python -m pip install --upgrade pip wheel setuptools -q
    return $venv
}

function Install-Kit($venv) {
    if ($UseLocal) {
        $root = Split-Path -Parent $MyInvocation.MyCommand.Path
        pip install -e $root -q
    } else {
        pip install "git+${GitUrl}@${Version}#subdirectory=packages/daffodil-kit" -q
    }
}

function Test-Security {
    python -c @"
import time
from daffodil_kit.security import sign_command, verify_command, generate_device_secret
s = generate_device_secret()
ts = time.time()
sig = sign_command(s, '{}', ts)
assert verify_command(s, '{}', ts, sig)
"@
}

function Install-ScheduledTask {
    if ($env:DAFFODIL_KIT_INSTALL_SERVICE -ne "1") { return }
    $exe = Join-Path $Prefix "daffodil-kit-venv\Scripts\daffodil-kit.exe"
    if (-not (Test-Path $exe)) { Write-WarnMsg "daffodil-kit.exe missing — skip task"; return }
    $action = New-ScheduledTaskAction -Execute $exe -Argument "start"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName "DaffodilCopyCatKit" -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    Write-Ok "Scheduled task: DaffodilCopyCatKit"
}

Write-Banner

Write-Step "Detect environment"
$py = Find-Python
Write-Ok "Python found: $($py -join ' ')"

Write-Step "Create virtualenv"
$venv = Ensure-Venv $py
Write-Ok "Virtualenv: $venv"

Write-Step "Install daffodil-kit"
Install-Kit $venv
Write-Ok "Package installed"

Write-Step "Configure directories"
$cfg = Join-Path $env:USERPROFILE ".daffodil-kit"
New-Item -ItemType Directory -Force -Path $cfg, (Join-Path $cfg "logs") | Out-Null
if ($env:DAFFODIL_KIT_API_URL -and -not (Test-Path (Join-Path $cfg "config.json"))) {
    @{ api_url = $env:DAFFODIL_KIT_API_URL } | ConvertTo-Json | Set-Content (Join-Path $cfg "config.json")
}
Write-Ok "Config: $cfg"

Write-Step "Security self-test"
Test-Security
Write-Ok "HMAC signing OK"

Write-Step "Verify CLI"
$ver = daffodil-kit version
daffodil-kit status | Out-Null
Write-Ok "CLI v$ver"

Write-Step "Optional background service"
Install-ScheduledTask

Write-Host ""
Write-Host "----------------------------------------------------------"
Write-Host "  Install complete — daffodil-kit $ver"
Write-Host "  Log: $LogFile"
Write-Host "----------------------------------------------------------"
Write-JsonLog "install.complete" "info" @{ version = $ver }

$bin = Join-Path $venv "Scripts"
Write-Host @"

Next steps:
  1. Pair:   daffodil-kit pair --api http://localhost:8000 --code <6-digit>
  2. Vault:  daffodil-kit vault set '<password>'
  3. Start:  daffodil-kit start

PATH (this session):
  `$env:PATH = "$bin;" + `$env:PATH
"@
