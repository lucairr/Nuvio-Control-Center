# Remove Nuvio Control Center for the current Windows user.
# Keeps %USERPROFILE%\.nuvio-control-center (config, password hash, history) and the TV SSH key.
# Add -RemoveData to delete the data folder too.
[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'NuvioControlCenter'),
    [switch]$RemoveData
)
$ErrorActionPreference = 'Continue'
$tasks = @('NuvioControlCenter_Dashboard', 'NuvioControlCenter_DailyCheck')
foreach ($task in $tasks) {
    Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 800
# The app may live in the folder this script runs from: leave it before deleting.
Set-Location $env:USERPROFILE
Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Nuvio Control Center.url') -ErrorAction SilentlyContinue
if (Get-NetFirewallRule -DisplayName 'Nuvio Control Center (LAN)' -ErrorAction SilentlyContinue) {
    Write-Host 'A firewall rule "Nuvio Control Center (LAN)" exists. Remove it from an admin PowerShell with:'
    Write-Host "  Remove-NetFirewallRule -DisplayName 'Nuvio Control Center (LAN)'"
}
$data = Join-Path $env:USERPROFILE '.nuvio-control-center'
if ($RemoveData) {
    Remove-Item -Path $data -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Removed scheduled tasks, application and data folder. The TV SSH key in .ssh is kept.'
} else {
    Write-Host 'Removed scheduled tasks and application. Configuration and TV pairing preserved.'
    Write-Host ('Data folder kept: ' + $data + '  (use -RemoveData to delete it)')
}
