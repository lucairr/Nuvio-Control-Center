# Shared helpers for the Windows scripts. Dot-source it: . (Join-Path $PSScriptRoot 'common.ps1')
# ASCII only: Windows PowerShell 5.1 reads BOM-less files with the ANSI code page.

$script:NuvioTasks = @('NuvioControlCenter_Dashboard', 'NuvioControlCenter_DailyCheck')
$script:NuvioDefaultInstallDir = Join-Path $env:LOCALAPPDATA 'NuvioControlCenter'
$script:NuvioHome = Join-Path $env:USERPROFILE '.nuvio-control-center'
$script:NuvioConfig = Join-Path $script:NuvioHome 'config.json'

function Write-Step([string]$Text) { Write-Host ''; Write-Host ('==> ' + $Text) -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host ('    [OK] ' + $Text) -ForegroundColor Green }

function Resolve-NuvioPython {
    # Returns @{ Exe = 'C:\...\python.exe'; Pyw = 'C:\...\pythonw.exe'; Version = 312 } or $null.
    # Tries the py launcher first, then python.exe. The Microsoft Store "python.exe"
    # stub prints nothing useful and is skipped automatically.
    $ErrorActionPreference = 'Continue'   # PS 5.1: redirected stderr must not abort
    $candidates = New-Object System.Collections.ArrayList
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) { [void]$candidates.Add(@($py.Source, '-3')) }
    foreach ($name in @('python.exe', 'python3.exe')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { [void]$candidates.Add(@($cmd.Source)) }
    }
    foreach ($c in $candidates) {
        $exe = $c[0]
        $pre = @()
        if ($c.Count -gt 1) { $pre = $c[1..($c.Count - 1)] }
        try {
            $out = & $exe @pre -c "import sys; print(sys.executable); print(sys.version_info[0]*100+sys.version_info[1])" 2>$null
        } catch { continue }
        if ($LASTEXITCODE -ne 0 -or -not $out -or @($out).Count -lt 2) { continue }
        $real = [string]@($out)[0]
        $ver = 0
        if (-not [int]::TryParse([string]@($out)[1], [ref]$ver)) { continue }
        if (-not (Test-Path $real)) { continue }
        $pyw = Join-Path (Split-Path -Parent $real) 'pythonw.exe'
        if (-not (Test-Path $pyw)) { $pyw = $real }
        return @{ Exe = $real; Pyw = $pyw; Version = $ver }
    }
    return $null
}

function Get-NpmPrefix {
    $ErrorActionPreference = 'Continue'
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { return $null }
    $prefix = (& $npm.Source prefix -g 2>$null | Select-Object -First 1)
    if ($prefix) { return ([string]$prefix).Trim() }
    return (Join-Path $env:APPDATA 'npm')
}

function Add-ToSessionPath([string]$Folder) {
    if ($Folder -and (Test-Path $Folder)) {
        $parts = $env:Path -split ';'
        if ($parts -notcontains $Folder) { $env:Path = $Folder + ';' + $env:Path }
    }
}

function Find-AresCommand([string]$Name) {
    $cmd = Get-Command ($Name + '.cmd') -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $prefix = Get-NpmPrefix
    if ($prefix) {
        $candidate = Join-Path $prefix ($Name + '.cmd')
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Read-NuvioConfig {
    if (Test-Path $script:NuvioConfig) { return (Get-Content $script:NuvioConfig -Raw | ConvertFrom-Json) }
    return $null
}

function Save-NuvioConfig($Config) {
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($script:NuvioConfig, ($Config | ConvertTo-Json) + "`n", $utf8)
}

function Set-NuvioConfigValue([string]$Name, $Value) {
    $cfg = Read-NuvioConfig
    if (-not $cfg) { return }
    $cfg | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    Save-NuvioConfig $cfg
}

function Test-TcpPort([string]$HostName, [int]$Port, [int]$TimeoutMs = 1500) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs)) { return $false }
        $client.EndConnect($async)
        return $true
    } catch { return $false } finally { $client.Close() }
}
