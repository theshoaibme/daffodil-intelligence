# CopyCat Kit — auto-installs Python on Windows if missing
#   irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$Repo = if ($env:DAFFODIL_KIT_REPO) { $env:DAFFODIL_KIT_REPO } else { "the-shoaib2/daffodil-intelligence" }
$Ref = if ($env:DAFFODIL_KIT_VERSION) { $env:DAFFODIL_KIT_VERSION } else { "main" }
$Raw = "https://raw.githubusercontent.com/$Repo/$Ref/packages/daffodil-kit"

function Write-Log($m) { Write-Host "[copycat] $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[copycat] $m" -ForegroundColor Yellow }

function Test-PythonCommand([string[]]$PyCommand) {
    if (-not $PyCommand -or -not $PyCommand[0]) { return $false }
    $exe = $PyCommand[0]
    if ($exe -match '[\\/]') {
        if (-not (Test-Path -LiteralPath $exe)) { return $false }
    } elseif (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        return $false
    }
    $prefix = @()
    if ($PyCommand.Length -gt 1) { $prefix = $PyCommand[1..($PyCommand.Length - 1)] }
    & $exe @($prefix + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)")) 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Get-PythonCandidates {
    $candidates = [System.Collections.Generic.List[string[]]]::new()

    foreach ($root in @($env:pythonLocation, $env:Python_ROOT_DIR, $env:Python3_ROOT_DIR)) {
        if ($root) {
            $exe = Join-Path $root "python.exe"
            if (Test-Path -LiteralPath $exe) { $candidates.Add(@($exe)) }
        }
    }

    foreach ($cmd in @(@("py", "-3.12"), @("py", "-3.11"), @("py", "-3"), @("python3"), @("python"))) {
        $candidates.Add($cmd)
    }

    foreach ($base in @(
            "$env:LOCALAPPDATA\Programs\Python",
            "$env:ProgramFiles\Python312",
            "${env:ProgramFiles(x86)}\Python312-32"
        )) {
        if (-not (Test-Path -LiteralPath $base)) { continue }
        Get-ChildItem -Path $base -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates.Add(@($_.FullName)) }
    }

    return $candidates
}

function Find-Python {
    foreach ($cmd in Get-PythonCandidates) {
        if (Test-PythonCommand $cmd) { return $cmd }
    }
    return $null
}

function Refresh-PythonPath {
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
    foreach ($base in @(
            "$env:LOCALAPPDATA\Programs\Python\Python312",
            "$env:LOCALAPPDATA\Programs\Python\Python311",
            "$env:ProgramFiles\Python312"
        )) {
        if (Test-Path -LiteralPath $base) {
            $env:PATH = "$base;$base\Scripts;" + $env:PATH
        }
    }
}

function Install-PythonWindows {
    Write-Log "No Python 3.11+ — installing..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
        Start-Sleep -Seconds 5
        Refresh-PythonPath
        return
    }
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install python312 -y
        refreshenv 2>$null
        Refresh-PythonPath
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
    foreach ($i in 1..6) {
        $py = Find-Python
        if ($py) { break }
        Start-Sleep -Seconds 5
        Refresh-PythonPath
    }
}
if (-not $py) { throw "Python still not found after install — restart terminal and re-run" }

Write-Log "Using Python: $($py -join ' ')"
$pythonExe = $py[0]
$pythonArgs = @()
if ($py.Length -gt 1) { $pythonArgs = $py[1..($py.Length - 1)] }
& "$pythonExe" @pythonArgs "$InstallPy"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
