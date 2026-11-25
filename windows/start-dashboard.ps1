# Start the dashboard in this console (manual mode / troubleshooting). Close the window or Ctrl+C to stop.
[CmdletBinding()]
param([string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'NuvioControlCenter'))
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not (Test-Path (Join-Path $InstallDir 'nuvio\server.py'))) { throw 'Not installed. Run install-windows.ps1 first.' }
Add-ToSessionPath (Get-NpmPrefix)
$pyFile = Join-Path $InstallDir 'python-path.txt'
$python = $null
if (Test-Path $pyFile) { $python = (Get-Content $pyFile -Raw).Trim() }
if (-not $python -or -not (Test-Path $python)) { $p = Resolve-NuvioPython; if ($p) { $python = $p.Exe } }
if (-not $python) { throw 'Python not found.' }
Push-Location $InstallDir
try { & $python -m nuvio.server serve } finally { Pop-Location }
