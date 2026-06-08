# CopyCat Kit (daffodil-kit) — Windows PowerShell installer
# Run:
#   irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.ps1 | iex
# Pin version:
#   $env:DAFFODIL_KIT_VERSION = "copycat-v0.1.0"; irm ... | iex

$ErrorActionPreference = "Stop"

$Repo = if ($env:DAFFODIL_KIT_REPO) { $env:DAFFODIL_KIT_REPO } else { "the-shoaib2/daffodil-intelligence" }
$Version = if ($env:DAFFODIL_KIT_VERSION) { $env:DAFFODIL_KIT_VERSION } else { "main" }
$Prefix = if ($env:DAFFODIL_KIT_PREFIX) { $env:DAFFODIL_KIT_PREFIX } else { "$env:USERPROFILE\.local" }
$GitUrl = "https://github.com/$Repo.git"
$PipSpec = "git+${GitUrl}@${Version}#subdirectory=packages/daffodil-kit"

function Write-Log($msg) { Write-Host "[copycat] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[copycat] $msg" -ForegroundColor Yellow }

function Find-Python {
    $candidates = @("py -3.12", "py -3.11", "python3", "python")
    foreach ($c in $candidates) {
        try {
            $parts = $c -split " "
            if ($parts[0] -eq "py") {
                $ver = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            } else {
                $ver = & $parts[0] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            }
            if ($ver -match "^3\.(1[1-9]|[2-9][0-9])") {
                if ($parts[0] -eq "py") { return @("py", "-3") }
                return @($parts[0])
            }
        } catch { continue }
    }
    throw "Python 3.11+ required. Install from https://www.python.org/downloads/"
}

function Ensure-Venv($pyArgs) {
    $venv = Join-Path $Prefix "daffodil-kit-venv"
    if (-not (Test-Path $venv)) {
        Write-Log "Creating virtualenv at $venv"
        & $pyArgs[0] $pyArgs[1..($pyArgs.Length-1)] -m venv $venv
    }
    $activate = Join-Path $venv "Scripts\Activate.ps1"
    if (-not (Test-Path $activate)) { throw "venv activation script missing: $activate" }
    . $activate
    python -m pip install --upgrade pip wheel setuptools
    return $venv
}

function Install-Kit {
    Write-Log "Installing daffodil-kit from $GitUrl@$Version"
    pip install $PipSpec
}

function Write-Config {
    $cfgDir = Join-Path $env:USERPROFILE ".daffodil-kit"
    New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $cfgDir "logs") | Out-Null
    if ($env:DAFFODIL_KIT_API_URL -and -not (Test-Path (Join-Path $cfgDir "config.json"))) {
        @{ api_url = $env:DAFFODIL_KIT_API_URL } | ConvertTo-Json | Set-Content (Join-Path $cfgDir "config.json")
    }
}

function Install-ScheduledTask {
    if ($env:DAFFODIL_KIT_INSTALL_SERVICE -ne "1") { return }
    $venv = Join-Path $Prefix "daffodil-kit-venv"
    $exe = Join-Path $venv "Scripts\daffodil-kit.exe"
    if (-not (Test-Path $exe)) { Write-Warn "daffodil-kit.exe not found — skip scheduled task"; return }
    $action = New-ScheduledTaskAction -Execute $exe -Argument "start"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName "DaffodilCopyCatKit" -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    Write-Log "Registered logon task: DaffodilCopyCatKit"
}

Write-Log "CopyCat Kit installer — Windows · ref: $Version"
$py = Find-Python
$venv = Ensure-Venv $py
Install-Kit
Write-Config
Install-ScheduledTask

$bin = Join-Path $venv "Scripts"
Write-Log "CopyCat Kit installed"
Write-Host @"

Add to PATH (current session):
  `$env:PATH = "$bin;" + `$env:PATH

Next steps:
  1. Pair:   daffodil-kit pair --api http://localhost:8000 --code <6-digit>
  2. Vault:  daffodil-kit vault set '<password>'
  3. Start:  daffodil-kit start

"@
