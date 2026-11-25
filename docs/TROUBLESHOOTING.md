# Troubleshooting

## `No matched device <name>: nuvio-lg`

The LG CLI stores registered TVs **per OS user**. The Control Center on Linux runs as `nuvio-updater`, not `root`:

```bash
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-setup-device --list
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-install --device nuvio-lg --listfull
```

On Windows, pair and run the updater as the **same regular Windows user**. An administrator account may have a different device list.

## `Failed to get ssh private key`

1. Read the **current TV IP** in the LG Developer Mode app (not an older DHCP address).
2. Switch **Developer Mode** and **Key Server** ON.
3. Confirm initial key server reachability from a trusted LAN client (example Linux):

```bash
curl -sS --connect-timeout 5 --max-time 10 -o /dev/null -w '%{http_code}\n' http://192.168.1.50:9991/webos_rsa
```

4. Run `ares-novacom --device nuvio-lg --getkey` under the correct user. When the passphrase prompt appears, type the code **from the TV**. Do not paste another shell command into that prompt.
5. If the TV IP changed, update both the CLI registration (`ares-setup-device --modify ...`) and your `config.json`.

## No version detected / automatic update skipped

Check `ares-install --device nuvio-lg --listfull` and ensure `space.nuvio.webos` is listed. Some CLI variants don't report the version in listfull; the tool attempts to read the installed `appinfo.json`. When the installed version remains unknown, automatic installation is deliberately blocked. **Force reinstall** from the dashboard only after confirming that the app ID is correct and making a backup.

## Login page unavailable or port 8765 busy

Linux:

```bash
sudo systemctl status nuvio-dashboard.service --no-pager
sudo journalctl -u nuvio-dashboard.service -n 100 --no-pager
ss -lnt | grep 8765
```

Windows: run `doctor.ps1` from `%LOCALAPPDATA%\NuvioControlCenter` (shows task state and the last lines of `%USERPROFILE%\.nuvio-control-center\dashboard.log`), or `start-dashboard.ps1` to see the startup error live. Check if the port is already in use with `Get-NetTCPConnection -LocalPort 8765`.

## Windows: `python` opens the Microsoft Store / "Python was not found"

That is the Store alias, not a real Python. Install Python from python.org with **Add python.exe to PATH**, or disable *App execution aliases* for python in Windows Settings. The installer prefers the `py` launcher and skips the alias automatically.

## Windows: "running scripts is disabled on this system"

Use `install-windows.cmd` or start scripts with `powershell -NoProfile -ExecutionPolicy Bypass -File ...`. This bypasses the policy only for that one run.

## Node too old

`node -v` must be **20+**. Debian 11 ships old Node.js in its base repo; use NodeSource to install Node.js 22 according to `INSTALL_LINUX.md`. On Windows install Node LTS and reopen PowerShell to refresh PATH.

## GitHub API failure

Ensure DNS and HTTPS access to `api.github.com`, `github.com` and `*.githubusercontent.com`; the latest stable release must include a valid webOS `.ipk`. GitHub API rate limiting, network proxies or a temporary publication delay can cause errors. Auto-install is fail-closed.

## Auto-update isn't running

Linux: `systemctl list-timers --all | grep nuvio`, `timedatectl` and `journalctl -u nuvio-check.service`. Windows: `Get-ScheduledTask NuvioControlCenter*` and `Get-ScheduledTaskInfo NuvioControlCenter_DailyCheck` (LastTaskResult 0 = OK); scheduled jobs are configured for the logged-in user and will not run when logged out or the PC is off.

## Developer Mode expiration

The LG Developer Mode session expires unless renewed according to LG's instructions. This project **does not** promise automatic renewal. Re-enable it using the TV app when required.

## Reporting bugs safely

Provide sanitized logs from the dashboard plus OS/Python/Node versions, webOS CLI version and Nuvio app version. Do **not** share auth.json, raw SSH keys, passphrases, or sensitive local IP/network details unless you intentionally choose to disclose them.
