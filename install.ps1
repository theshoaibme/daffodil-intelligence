# CopyCat — irm https://cdn.jsdelivr.net/gh/the-shoaib2/daffodil-intelligence/install.ps1 | iex
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$local = Join-Path $here "packages\daffodil-kit\install.ps1"
if (Test-Path $local) { & $local; exit }
$r = if ($env:DAFFODIL_KIT_REPO) { $env:DAFFODIL_KIT_REPO } else { "the-shoaib2/daffodil-intelligence" }
$v = if ($env:DAFFODIL_KIT_VERSION) { $env:DAFFODIL_KIT_VERSION } else { "main" }
iex (irm "https://raw.githubusercontent.com/$r/$v/packages/daffodil-kit/install.ps1")
