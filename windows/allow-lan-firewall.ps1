# Optional: allow other devices on your PRIVATE home network to open the dashboard.
# Requires admin (the installer launches it with a UAC prompt). Never use on public networks.
#   -Remove  deletes the rule.
[CmdletBinding()]
param(
    [int]$Port = 8765,
    [string]$Program = '',
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$name = 'Nuvio Control Center (LAN)'
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Run this script from an administrator PowerShell.' }
Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
if ($Remove) { Write-Host 'Firewall rule removed.'; exit 0 }
$params = @{
    DisplayName = $name; Direction = 'Inbound'; Action = 'Allow'; Protocol = 'TCP'
    LocalPort = $Port; Profile = 'Private'; RemoteAddress = 'LocalSubnet'
    Description = 'Nuvio Control Center dashboard - private LAN only'
}
if ($Program -and (Test-Path $Program)) { $params.Program = $Program }
New-NetFirewallRule @params | Out-Null
Write-Host ('Firewall rule created: TCP ' + $Port + ', Private profile, local subnet only.')
Write-Host 'If your network is marked "Public" in Windows settings, switch it to "Private" first.'
Start-Sleep -Seconds 3
