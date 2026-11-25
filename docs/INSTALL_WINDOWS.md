# Windows 10/11 installation

Nuvio Control Center runs a local **web dashboard** on your Windows PC and updates Nuvio on the LG TV over the LAN. It is a **script-based installer** (no `.exe`, no admin rights). The PC must be on and your Windows user signed in for the scheduled check to run; missed checks run as soon as you sign in again.

> Status: **beta, software-tested on Windows CI; real Windows-to-LG installs still need community confirmation.** Please report your results.

## 1. Prerequisites (one time)

| What | Where | Note |
| --- | --- | --- |
| Python 3.9+ | [python.org/downloads/windows](https://www.python.org/downloads/windows/) | Tick **"Add python.exe to PATH"** in the installer |
| Node.js 20+ LTS (22 recommended) | [nodejs.org](https://nodejs.org/) | Default options are fine (includes npm) |
| LG TV | Developer Mode app | **Dev Mode ON** and **Key Server ON**, Nuvio already installed |

After installing Python and Node, **close and reopen** any PowerShell/Explorer window so the new PATH is picked up. The official LG CLI (`@webos-tools/cli`) is installed automatically by the installer.

## 2. Install

1. Download the repository ZIP (green **Code → Download ZIP** button, or the ZIP from **Releases**) and **extract it** (right click → *Extract All*). Do not run it from inside the ZIP.
2. Open the extracted folder and **double-click `install-windows.cmd`**.
3. Answer the questions:
   - **TV IP** shown in the LG Developer Mode app (e.g. `192.168.1.50`);
   - **dashboard password** (at least 12 characters, typing is hidden);
   - **Pair the LG TV now? [Y/n]** - press Enter, then type the **passphrase shown on the TV** at `input passphrase:`.

Prefer the command line? From PowerShell in the extracted folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install-windows.ps1 -TvIp 192.168.1.50 -Pair
```

What the installer does:

- checks Python/Node, installs the LG CLI for your user if missing;
- copies the app to `%LOCALAPPDATA%\NuvioControlCenter`;
- stores config, password hash and history in `%USERPROFILE%\.nuvio-control-center` (automatic installation **OFF**);
- creates two Task Scheduler jobs for your user: **dashboard at logon** and **release check every day at 19:30** (laptops: also on battery);
- creates the desktop shortcut **Nuvio Control Center** → `http://localhost:8765`;
- optionally pairs the TV (`connect-tv-windows.ps1`).

Open the shortcut, sign in and press **Verifica aggiornamenti**. Enable **Installazione automatica** only after the first check shows the installed Nuvio version.

### Options

| Option | Effect |
| --- | --- |
| `-TvIp 192.168.1.50` | Skip the IP question |
| `-Pair` / `-NoPair` | Pair the TV without asking / never ask |
| `-AllowLan` | Dashboard reachable from phone/other PCs (`0.0.0.0`). Offers to create a firewall rule limited to **Private** networks and the **local subnet** (UAC prompt) |
| `-Port 8765` | Different dashboard port (first install only) |
| `-SkipTasks` | No scheduled tasks; start manually with `start-dashboard.ps1` |

Never port-forward the dashboard to the Internet: it is plain HTTP. Use a VPN (WireGuard/Tailscale) for remote access.

## 3. Pair the TV again (IP change, new key, new TV)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\NuvioControlCenter\connect-tv-windows.ps1"
```

It updates both the LG CLI device profile **and** `tv_ip` in the dashboard config. Pair with **the same Windows user** that runs the dashboard: CLI profiles and SSH keys are per user. A DHCP reservation for the TV on your router avoids most problems.

## 4. Diagnostics

Double-click/run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\NuvioControlCenter\doctor.ps1"
```

It shows scheduled-task state, Python/Node/CLI paths, configuration, TV reachability on port 9922, dashboard port, the Nuvio version on the TV and the last lines of `dashboard.log`. Nothing is changed on the TV. **Sanitize** the output before posting it in an issue.

Manual dashboard in a console window (shows errors live):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\NuvioControlCenter\start-dashboard.ps1"
```

Files: `%USERPROFILE%\.nuvio-control-center\` → `config.json`, `state.json` (history/logs), `auth.json` (password hash), `dashboard.log`. Never share `auth.json` or `%USERPROFILE%\.ssh`.

Change the dashboard password:

```powershell
Set-Location "$env:LOCALAPPDATA\NuvioControlCenter"; python -m nuvio.server set-password
```

then restart the task (`Stop-ScheduledTask NuvioControlCenter_Dashboard; Start-ScheduledTask NuvioControlCenter_Dashboard`) or sign out/in.

## 5. Update / uninstall

**Update:** download the new ZIP, extract, double-click `install-windows.cmd` again. Config, password, history and pairing are kept; the running dashboard is restarted with the new code.

**Uninstall:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\NuvioControlCenter\uninstall-windows.ps1"            # keeps data
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\NuvioControlCenter\uninstall-windows.ps1" -RemoveData # deletes data too
```

The TV SSH key in `%USERPROFILE%\.ssh` is never deleted automatically.

## Limitations

- Runs only while your user is signed in (Task Scheduler "run only when user is logged on": no stored Windows password). For 24/7 operation use a Linux mini PC or VM instead.
- No Windows Service, no `.exe`, no automatic firewall change unless you accept the `-AllowLan` prompt.
- The LG Developer Mode session still expires and must be renewed on the TV.
