# CopyCat Kit — auto-installs Python on Windows if missing
#   irm https://cdn.jsdelivr.net/gh/the-shoaib2/daffodil-intelligence/install.ps1 | iex

$ErrorActionPreference = "Stop"
$Repo = if ($env:DAFFODIL_KIT_REPO) { $env:DAFFODIL_KIT_REPO } else { "the-shoaib2/daffodil-intelligence" }
$Ref = if ($env:DAFFODIL_KIT_VERSION) { $env:DAFFODIL_KIT_VERSION } else { "main" }
$Raw = "https://raw.githubusercontent.com/$Repo/$Ref/packages/daffodil-kit"

function Write-Log($m) { Write-Host "[copycat] $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[copycat] $m" -ForegroundColor Yellow }

function Test-Python($args) {
    try {
        $ver = & $args[0] $args[1..($args.Length-1)] -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" 2>$null
        return $true
    } catch { return $false }
}

function Find-Python {
    foreach ($a in @(@("py","-3.12"), @("py","-3.11"), @("py","-3"), @("python3"), @("python"))) {
        if (Test-Python $a) { return $a }
    }
    return $null
}

function Install-PythonWindows {
    Write-Log "No Python 3.11+ — installing..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path", "User")
        return
    }
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install python312 -y
        refreshenv 2>$null
        return
    }
    Write-Warn "Install manually: winget install Python.Python.3.12"
    Write-Warn "Or download: https://www.python.org/downloads/"
    throw "Python 3.11+ required"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallPy = Join-Path $ScriptDir "install.py"
if (-not (Test-Path $InstallPy)) {
    $InstallPy = Join-Path $env:TEMP "copycat-install.py"
    Invoke-WebRequest -Uri "$Raw/install.py" -OutFile $InstallPy -UseBasicParsing
}

$py = Find-Python
if (-not $py) {
    Install-PythonWindows
    $py = Find-Python
}
if (-not $py) { throw "Python still not found after install — restart terminal and re-run" }

Write-Log "Using Python: $($py -join ' ')"
& $py[0] $py[1..($py.Length-1)] $InstallPy
