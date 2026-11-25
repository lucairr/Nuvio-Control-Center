# Linux / Debian / Ubuntu installation

This installs the Control Center on a systemd server or VM, suitable for an always-on Raspberry Pi-class host, mini PC or server. The Debian/ESXi prototype and manual downgrade were **reported working by the project's original tester**. Other Linux distributions and TV hardware still need validation.

## Prerequisites

- A Debian 11+ / Ubuntu 22.04+ machine with systemd, internet/DNS and LAN reachability to your LG TV.
- Python 3.9+, Node.js 20+ and npm (Node.js 22 recommended).
- LG webOS **Developer Mode ON**, **Key Server ON** (both shown in the TV Developer Mode app).
- Nuvio TV already installed through the official installer; this tool is intended for updates, not the first install.
- TV SSH (TCP **9922**) reachable from Linux; the Key Server typically uses TCP **9991** for initial key retrieval.

Check prerequisites:

```bash
python3 --version
node -v
npm -v
```

### Debian 11: upgrade an old Node.js 12 install

Use the official [NodeSource instructions](https://github.com/nodesource/distributions) for your OS. For Debian/Ubuntu with apt:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates gnupg python3
curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup_22.sh
# Review the downloaded setup script before running it.
sudo bash /tmp/nodesource_setup_22.sh
sudo apt-get install -y nodejs
node -v
```

If the computer runs other apps relying on an old Node.js version, evaluate the impact of replacing the system-wide Node version first.

## Install

Download and extract this repository to a temporary directory. In its root:

```bash
sudo TV_IP=192.168.1.50 TV_NAME='Living Room LG' bash install.sh
```

Replace `192.168.1.50` with the IP **shown in the Developer Mode app**. For LAN access the installer binds to all local interfaces on port 8765 by default. For localhost-only access instead:

```bash
sudo TV_IP=192.168.1.50 WEB_BIND=127.0.0.1 WEB_PORT=8765 bash install.sh
```

Language of the dashboard, logs and history: `NUVIO_LANG=it` or `NUVIO_LANG=en` (default: the system language, English if it is not Italian). You can change it later with the IT / EN buttons in the dashboard.

```bash
sudo TV_IP=192.168.1.50 NUVIO_LANG=en bash install.sh
```

The installer creates:

- `/opt/nuvio-updater/` – code and dashboard, owned by root;
- `/var/lib/nuvio-updater/` – restricted configuration, hashed password, SSH profile, state and logs;
- `nuvio-dashboard.service` – dashboard server;
- `nuvio-check.service` + `nuvio-check.timer` – daily check at 19:30 local machine time.

The installer preserves existing configuration and keys on re-run. New installations ask for a dashboard password and **default to automatic installation OFF**.

## Pair TV with the correct Linux account

From the Developer Mode app on the TV, turn **Dev Mode ON** and **Key Server ON**. Then:

```bash
sudo bash scripts/connect-tv-linux.sh 192.168.1.50
```

The helper configures the `nuvio-lg` alias under the **`nuvio-updater`** service user's home. When `input passphrase:` appears, type only the TV passphrase, then press Enter; don't paste other shell commands. It then checks the installed app list.

To do the setup manually:

```bash
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-config --profile tv
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-setup-device --add nuvio-lg --info host=192.168.1.50 --info port=9922 --info username=prisoner
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-novacom --device nuvio-lg --getkey
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-install --device nuvio-lg --listfull
```

The exact app ID should be `space.nuvio.webos`. Do **not** test this CLI pairing as `root` — root has a different device registry and SSH key directory.

## Check and activate auto-updates

Open `http://<linux-machine-ip>:8765` (or a local tunnel to localhost if you chose a localhost bind). Sign in. Press **Verifica aggiornamenti** and inspect both the installed version and latest release. Only after it is working, turn on **Installazione automatica**. The daily task runs at 19:30 in the machine's timezone.

Manual CLI check as the service user:

```bash
cd /opt/nuvio-updater
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater NUVIO_HOME=/var/lib/nuvio-updater /usr/bin/python3 -m nuvio.server run check
```

Service and timer diagnostics:

```bash
sudo systemctl status nuvio-dashboard.service --no-pager
sudo systemctl list-timers --all | grep nuvio
sudo journalctl -u nuvio-dashboard.service -n 80 --no-pager
sudo journalctl -u nuvio-check.service -n 80 --no-pager
sudo systemctl start nuvio-check.service   # Run a scheduled check NOW (respects auto_update)
```

## Update the computer's TV address

If the LG TV DHCP IP changes, update **both** the CLI alias and the web config:

```bash
sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ares-setup-device --modify nuvio-lg --info host=192.168.1.51
sudo python3 - <<'PY'
import json
from pathlib import Path
p=Path('/var/lib/nuvio-updater/config.json')
x=json.loads(p.read_text()); x['tv_ip']='192.168.1.51'; p.write_text(json.dumps(x,indent=2)+'\n')
PY
sudo chown nuvio-updater:nuvio-updater /var/lib/nuvio-updater/config.json
sudo chmod 600 /var/lib/nuvio-updater/config.json
sudo systemctl restart nuvio-dashboard
```

Consider a DHCP reservation on your router to keep the TV IP fixed.

## Test and use the manual downgrade

After verifying the TV and Nuvio version in the dashboard, open **Versioni precedenti**, click **Carica release**, choose an older official IPK and confirm. This is an in-place **app** version change, not LG firmware. The app does not uninstall Nuvio. It turns OFF automatic installation when a downgrade is initiated, and the dashboard logs the result. Older Nuvio versions may not be able to read settings saved by newer releases, so back them up first where possible.

## Raspberry Pi / ARM64 Linux

This installer may work on 64-bit Debian-based ARM64 systems when Python 3.9+, Node 20+ and `@webos-tools/cli` work on the host. **ARM64 LG CLI compatibility is not verified**, and the official vendor CLI requirements are for supported 64-bit environments. Treat Pi 4/5 as experimental, and do not assume an install on Raspberry Pi OS 32-bit will work. See [hardware matrix](HARDWARE_COMPATIBILITY.md).

## Upgrade or uninstall

Extract a new release, run `sudo bash install.sh` again. Files in `/var/lib/nuvio-updater/` are preserved. For uninstall:

```bash
sudo bash uninstall.sh
```

This removes systemd units and program files, but **intentionally preserves credentials and SSH keys** for a future reinstallation. Delete the state directory manually only when you want to lose that pairing and after you have made a backup.

## Security

Port 8765 is HTTP. Don't expose it to the public internet; prefer a VPN, loopback bind or HTTPS reverse proxy for access outside a trusted home network. The Linux service runs as a dedicated unprivileged user and uses the official CLI; no root shell runs from the web server.
