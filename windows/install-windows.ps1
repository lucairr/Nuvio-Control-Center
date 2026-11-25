# Nuvio Control Center - installer for the CURRENT Windows user.
# No admin rights needed (only the optional LAN firewall rule asks for UAC).
#
# Easiest: double-click install-windows.cmd in the repository root.
# Or from PowerShell, in the extracted repository folder:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install-windows.ps1 -TvIp 192.168.1.50
#
# Re-running the installer upgrades the app and keeps config, password and TV pairing.
[CmdletBinding()]
param(
    [string]$TvIp = '',
    [string]$TvName = 'LG webOS TV',
    [int]$Port = 8765,
    [string]$InstallDir = '',
    [switch]$AllowLan,      # dashboard reachable from phone/other PCs on the LAN
    [switch]$SkipTasks,     # no Task Scheduler jobs (manual start only)
    [switch]$Pair,          # pair the TV right after installing, without asking
    [switch]$NoPair,        # never ask to pair
    [string]$Language = ''  # dashboard/log language; default: Windows display language (it) or English
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not $InstallDir) { $InstallDir = $script:NuvioDefaultInstallDir }
if ($Language -and $Language -notin @('it', 'en')) { throw 'Language must be it or en.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path (Join-Path $repo 'nuvio\server.py'))) {
    throw 'Run the installer from an extracted copy of the complete repository (folder with nuvio\, web\, windows\).'
}

Write-Host 'Nuvio Control Center - Windows installer' -ForegroundColor Magenta
Write-Host 'Community project, not affiliated with NuvioMedia or LG.'

# Files extracted from a ZIP downloaded from the Internet carry Mark-of-the-Web.
Get-ChildItem -Path $repo -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- prerequisites
Write-Step 'Checking prerequisites'
$py = Resolve-NuvioPython
if (-not $py) {
    throw 'Python 3.9+ not found. Install it from https://www.python.org/downloads/windows/ (tick "Add python.exe to PATH"), then open a NEW PowerShell window and run the installer again.'
}
if ($py.Version -lt 309) { throw ('Python 3.9+ required, found ' + $py.Version + '.') }
Write-Ok ('Python: ' + $py.Exe)

$node = Get-Command node.exe -ErrorAction SilentlyContinue
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) {
    throw 'Node.js 20+ with npm not found. Install Node.js LTS from https://nodejs.org/, then open a NEW PowerShell window and run the installer again.'
}
# Note: no double quotes inside the JS expression (Windows PowerShell 5.1 strips them).
$nodeMajor = 0
[void][int]::TryParse(([string](& $node.Source -p "process.versions.node.split('.')[0]")).Trim(), [ref]$nodeMajor)
if ($nodeMajor -lt 20) { throw ('Node.js 20+ required (22 LTS recommended), found major version ' + $nodeMajor + '.') }
Write-Ok ('Node.js: v' + $nodeMajor + ' (' + $node.Source + ')')

$npmPrefix = Get-NpmPrefix
Add-ToSessionPath $npmPrefix
if (-not (Find-AresCommand 'ares-install') -or -not (Find-AresCommand 'ares-novacom') -or -not (Find-AresCommand 'ares-setup-device')) {
    Write-Host '    Installing the official LG webOS CLI (@webos-tools/cli) for this user...'
    & $npm.Source install -g '@webos-tools/cli'
    if ($LASTEXITCODE -ne 0) { throw 'npm could not install @webos-tools/cli. Check your Internet connection / proxy and retry.' }
    $npmPrefix = Get-NpmPrefix
    Add-ToSessionPath $npmPrefix
}
$ares = Find-AresCommand 'ares-install'
if (-not $ares) { throw ('LG CLI installed but ares-install.cmd not found in ' + $npmPrefix + '. Open a new PowerShell window and retry.') }
$cliDir = Split-Path -Parent $ares
Write-Ok ('LG webOS CLI: ' + $cliDir)

# ------------------------------------------------------- stop a running version
if (-not $SkipTasks) {
    foreach ($t in $script:NuvioTasks) { Stop-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue }
}

# ----------------------------------------------------------------- copy files
Write-Step ('Copying application to ' + $InstallDir)
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
foreach ($folder in @('nuvio', 'web')) {
    $dest = Join-Path $InstallDir $folder
    if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
    Copy-Item -Path (Join-Path $repo $folder) -Destination $dest -Recurse -Force
}
foreach ($f in @('common.ps1', 'start-dashboard.ps1', 'connect-tv-windows.ps1', 'doctor.ps1', 'uninstall-windows.ps1', 'allow-lan-firewall.ps1')) {
    Copy-Item -Path (Join-Path $PSScriptRoot $f) -Destination (Join-Path $InstallDir $f) -Force
}
Get-ChildItem -Path $InstallDir -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $InstallDir 'python-path.txt'), $py.Exe, $utf8)
Write-Ok 'Files copied'

# -------------------------------------------------------------- configuration
Write-Step 'Configuration'
if (-not (Test-Path $script:NuvioHome)) { New-Item -ItemType Directory -Force -Path $script:NuvioHome | Out-Null }
if (-not (Test-Path $script:NuvioConfig)) {
    while (-not $TvIp) { $TvIp = (Read-Host 'TV IP address shown in the LG Developer Mode app (e.g. 192.168.1.50)').Trim() }
    $parsed = $null
    if (-not [System.Net.IPAddress]::TryParse($TvIp, [ref]$parsed)) { throw ('Not a valid IP address: ' + $TvIp) }
    if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Port must be between 1024 and 65535.' }
    $bind = '127.0.0.1'
    $lang = $Language
    if (-not $lang) { if ((Get-UICulture).TwoLetterISOLanguageName -eq 'it') { $lang = 'it' } else { $lang = 'en' } }
    if ($AllowLan) { $bind = '0.0.0.0' }
    $config = [ordered]@{
        tv_ip = $TvIp; tv_device = 'nuvio-lg'; tv_name = $TvName; auto_update = $false
        web_port = $Port; web_bind = $bind; cli_dir = $cliDir; language = $lang
    }
    Save-NuvioConfig $config
    Write-Ok ('Created ' + $script:NuvioConfig + ' (automatic installation OFF)')
} else {
    Set-NuvioConfigValue 'cli_dir' $cliDir
    if ($AllowLan) { Set-NuvioConfigValue 'web_bind' '0.0.0.0' }
    if ($Language) { Set-NuvioConfigValue 'language' $Language }
    Write-Ok 'Existing configuration, password and TV pairing preserved'
}
$cfg = Read-NuvioConfig

$authFile = Join-Path $script:NuvioHome 'auth.json'
if (-not (Test-Path $authFile)) {
    Write-Host '    Choose the dashboard password (at least 12 characters). Typing is hidden.'
    Push-Location $InstallDir
    try {
        & $py.Exe -m nuvio.server set-password
        if ($LASTEXITCODE -ne 0) { throw 'Password setup failed.' }
    } finally { Pop-Location }
}

# ------------------------------------------------------------ scheduled tasks
if (-not $SkipTasks) {
    Write-Step 'Creating Task Scheduler jobs'
    try {
        $who = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $principal = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
        # Laptops: by default Task Scheduler does not start / stops tasks on battery.
        $dashboardSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
            -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1)
        $checkSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
        $dashAct = New-ScheduledTaskAction -Execute $py.Pyw -Argument '-m nuvio.server serve' -WorkingDirectory $InstallDir
        $checkAct = New-ScheduledTaskAction -Execute $py.Pyw -Argument '-m nuvio.server run auto' -WorkingDirectory $InstallDir
        Register-ScheduledTask -TaskName $script:NuvioTasks[0] -Description 'Nuvio Control Center web dashboard' `
            -Action $dashAct -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $who) -Principal $principal -Settings $dashboardSettings -Force | Out-Null
        Register-ScheduledTask -TaskName $script:NuvioTasks[1] -Description 'Nuvio Control Center daily release check (19:30)' `
            -Action $checkAct -Trigger (New-ScheduledTaskTrigger -Daily -At '19:30') -Principal $principal -Settings $checkSettings -Force | Out-Null
        Start-ScheduledTask -TaskName $script:NuvioTasks[0]
        Write-Ok 'Dashboard starts at logon; release check every day at 19:30 (missed runs start later)'
    } catch {
        Write-Warning ('Could not create scheduled tasks: ' + $_.Exception.Message)
        Write-Warning ('Start the dashboard manually with: ' + (Join-Path $InstallDir 'start-dashboard.ps1'))
        $SkipTasks = $true
    }
}

# --------------------------------------------------------------- shortcuts
$site = 'http://localhost:' + $cfg.web_port
$desktop = [Environment]::GetFolderPath('Desktop')
[System.IO.File]::WriteAllText((Join-Path $desktop 'Nuvio Control Center.url'), "[InternetShortcut]`r`nURL=$site`r`n", $utf8)

if (-not $SkipTasks) {
    $up = $false
    for ($i = 0; $i -lt 20 -and -not $up; $i++) { Start-Sleep -Milliseconds 500; $up = Test-TcpPort '127.0.0.1' ([int]$cfg.web_port) }
    if ($up) { Write-Ok ('Dashboard running at ' + $site) }
    else { Write-Warning ('Dashboard not answering yet. Check ' + (Join-Path $script:NuvioHome 'dashboard.log') + ' or run doctor.ps1.') }
}

if ($cfg.web_bind -eq '0.0.0.0') {
    Write-Host ''
    Write-Host 'LAN access is enabled. Windows Firewall needs an inbound rule (private networks only).'
    $answer = Read-Host 'Create the firewall rule now? A UAC prompt will appear. [Y/n]'
    if ($answer -notmatch '^(n|no)$') {
        $fw = Join-Path $InstallDir 'allow-lan-firewall.ps1'
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $fw + '"'), '-Port', $cfg.web_port, '-Program', ('"' + $py.Pyw + '"'))
    }
}

# ---------------------------------------------------------------- pairing
$sshKey = Join-Path $env:USERPROFILE ('.ssh\' + $cfg.tv_device + '_webos')
$paired = Test-Path $sshKey
if (-not $NoPair -and ($Pair -or -not $paired)) {
    Write-Host ''
    $doPair = $Pair
    if (-not $doPair) { $doPair = ((Read-Host 'Pair the LG TV now? (TV on, Developer Mode + Key Server ON) [Y/n]') -notmatch '^(n|no)$') }
    if ($doPair) {
        try { & (Join-Path $InstallDir 'connect-tv-windows.ps1') }
        catch { Write-Warning ('Pairing not completed: ' + $_.Exception.Message + ' - you can retry later with connect-tv-windows.ps1.') }
    }
}

Write-Host ''
Write-Host '------------------------------------------------------------' -ForegroundColor Magenta
Write-Host ('Installed to : ' + $InstallDir)
Write-Host ('Data folder  : ' + $script:NuvioHome)
Write-Host ('Dashboard    : ' + $site + '  (desktop shortcut created)')
Write-Host 'Diagnostics  : powershell -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\NuvioControlCenter\doctor.ps1"'
Write-Host 'Pair the TV  : powershell -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\NuvioControlCenter\connect-tv-windows.ps1"'
Write-Host 'Automatic installation starts DISABLED. Nothing was changed on the TV.'
Write-Host ''
Write-Host 'Nuvio Control Center is free. If it saves you time: https://ko-fi.com/lucairr' -ForegroundColor Magenta
