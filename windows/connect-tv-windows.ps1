# Pair the LG webOS TV with the LG CLI for the CURRENT Windows user.
# Run as the same (non-admin) user that runs the dashboard:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\connect-tv-windows.ps1 [-TvIp 192.168.1.50]
# Safe to run again: it updates the existing device profile (e.g. after an IP change).
[CmdletBinding()]
param(
    [string]$TvIp = '',
    [string]$Alias = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Add-ToSessionPath (Get-NpmPrefix)

$cfg = Read-NuvioConfig
if (-not $Alias) { if ($cfg -and $cfg.tv_device) { $Alias = [string]$cfg.tv_device } else { $Alias = 'nuvio-lg' } }
if ($Alias -notmatch '^[A-Za-z0-9_-]{1,64}$') { throw 'Invalid device alias.' }
if (-not $TvIp -and $cfg) { $TvIp = [string]$cfg.tv_ip }
$suggest = $TvIp
$typed = (Read-Host ('TV IP address shown in the Developer Mode app [' + $suggest + ']')).Trim()
if ($typed) { $TvIp = $typed }
$parsed = $null
if (-not $TvIp -or -not [System.Net.IPAddress]::TryParse($TvIp, [ref]$parsed)) { throw ('Not a valid IP address: ' + $TvIp) }

$setup = Find-AresCommand 'ares-setup-device'
$novacom = Find-AresCommand 'ares-novacom'
$install = Find-AresCommand 'ares-install'
$config = Find-AresCommand 'ares-config'
if (-not $setup -or -not $novacom -or -not $install) {
    throw 'LG CLI not found. Run install-windows.ps1 first (or: npm install -g @webos-tools/cli).'
}

Write-Step 'On the TV'
Write-Host '    1. Open the "Developer Mode" app.'
Write-Host '    2. Dev Mode Status = ON, Key Server = ON.'
Write-Host '    3. Keep the TV on this screen: you will need the passphrase it shows.'
if (-not (Test-TcpPort $TvIp 9922 2500)) {
    Write-Warning ('Cannot reach ' + $TvIp + ':9922. Check the TV IP, Developer Mode, and that PC and TV are on the same network.')
    if ((Read-Host 'Continue anyway? [y/N]') -notmatch '^(y|yes|s|si)$') { exit 1 }
}
[void](Read-Host 'Press Enter when ready')

Write-Step ('Configuring device profile "' + $Alias + '" -> prisoner@' + $TvIp + ':9922')
if ($config) { & $config --profile tv | Out-Null }
$list = (& $setup --list | Out-String)
if ($list -match ('(?m)^\s*' + [regex]::Escape($Alias) + '\s')) {
    & $setup --modify $Alias --info ('host=' + $TvIp) --info 'port=9922' --info 'username=prisoner' | Out-Null
} else {
    & $setup --add $Alias --info ('host=' + $TvIp) --info 'port=9922' --info 'username=prisoner' | Out-Null
}
if ($LASTEXITCODE -ne 0) { throw 'ares-setup-device failed.' }
Write-Ok 'Device profile saved'

Write-Step 'Downloading the SSH key from the TV'
Write-Host '    At "input passphrase:" type the passphrase shown ON THE TV (6 characters, case-sensitive).'
Write-Host '    Never share it, and never paste other commands there.'
& $novacom --device $Alias --getkey
if ($LASTEXITCODE -ne 0) { throw 'Key download failed. Check Key Server is ON and the passphrase is correct, then retry.' }
Write-Ok 'Key saved in your user profile (.ssh)'

Write-Step 'Testing: reading installed apps'
$ErrorActionPreference = 'Continue'   # PS 5.1: 2>&1 on native commands must not abort
$apps = (& $install --device $Alias --listfull 2>&1 | Out-String)
$listExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($listExit -ne 0) { Write-Host $apps; throw 'Pairing done but the TV did not answer ares-install. Retry in a minute.' }
if ($apps -match 'space\.nuvio\.webos') { Write-Ok 'Nuvio (space.nuvio.webos) found on the TV' }
else { Write-Warning 'Connected, but Nuvio is not installed. Install it once with the official Nuvio installer, then use the dashboard.' }

if ($cfg -and ([string]$cfg.tv_ip -ne $TvIp -or [string]$cfg.tv_device -ne $Alias)) {
    Set-NuvioConfigValue 'tv_ip' $TvIp
    Set-NuvioConfigValue 'tv_device' $Alias
    Write-Ok 'Dashboard configuration updated with the new TV address'
}
Write-Host ''
Write-Host 'Done. Open the dashboard and press "Verifica aggiornamenti".' -ForegroundColor Green
