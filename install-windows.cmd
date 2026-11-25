@echo off
rem Nuvio Control Center - double-click installer for Windows 10/11.
rem Runs windows\install-windows.ps1 for the current user (no admin needed).
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\install-windows.ps1" %*
echo.
if errorlevel 1 (
  echo Installation NOT completed. Read the red message above.
) else (
  echo Installation finished.
)
pause
