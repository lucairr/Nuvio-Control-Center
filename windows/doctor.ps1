# Read-only diagnostics: Python, Node, LG CLI, config, TV reachability, dashboard port.
# Nothing is installed or changed on the TV. Sanitize the output before posting it publicly.
[CmdletBinding()]
param([string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'NuvioControlCenter'))
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Add-ToSessionPath (Get-NpmPrefix)
$appDir = $InstallDir
if (-not (Test-Path (Join-Path $appDir 'nuvio\server.py'))) { $appDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
$pyFile = Join-Path $InstallDir 'python-path.txt'
$python = $null
if (Test-Path $pyFile) { $python = (Get-Content $pyFile -Raw).Trim() }
if (-not $python -or -not (Test-Path $python)) { $p = Resolve-NuvioPython; if ($p) { $python = $p.Exe } }
if (-not $python) { Write-Host '[!!] Python not found'; exit 1 }
Write-Host ('PowerShell ' + $PSVersionTable.PSVersion.ToString())
foreach ($t in $script:NuvioTasks) {
    $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if ($task) { Write-Host ('[OK] Task ' + $t + ': ' + $task.State) } else { Write-Host ('[!!] Task ' + $t + ': not registered') }
}
Push-Location $appDir
try { & $python -m nuvio.server doctor } finally { Pop-Location }
$log = Join-Path $script:NuvioHome 'dashboard.log'
if (Test-Path $log) { Write-Host ''; Write-Host ('Last lines of ' + $log + ':'); Get-Content $log -Tail 15 }
Write-Host ''
Read-Host 'Press Enter to close' | Out-Null
