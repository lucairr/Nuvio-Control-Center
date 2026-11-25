# Host hardware & platform compatibility

**Important:** the host is the computer/server running Nuvio Control Center, **not** the LG TV firmware. Only **LG webOS Developer Mode** TVs are supported as the target. Samsung Tizen and rooted LG Homebrew workflows are **not implemented**.

| Host | Install method | Status | Comments |
|---|---|---|---|
| Debian 11 VM on ESXi, 64-bit | `install.sh` + systemd | **User-tested** (dashboard, update, manual downgrade) | Reference setup |
| Debian 12/13, Ubuntu 22.04/24.04 (x86-64) | `install.sh` | CI-tested; **live TV not yet verified** | Needs systemd, Python 3.9+, Node 20+ |
| Proxmox VM, Intel NUC, mini PC, home server (Linux x86-64) | `install.sh` | **Not yet hardware-tested** | Best choice for 24/7 updates |
| Windows 10/11 x64 | `install-windows.cmd` | CI-tested; **live TV not yet verified** | Runs while the user is signed in |
| Raspberry Pi 4/5, **64-bit** Raspberry Pi OS | `install.sh` | **Experimental** | Official LG CLI on ARM64 not verified |
| 32-bit systems | — | **Not supported** | Requires 64-bit Python/Node and a working webOS CLI |

The official [LG webOS CLI documentation](https://webostv.developer.lge.com/develop/tools/cli-installation) lists the supported desktop environments. Working Python and Node.js alone do **not** prove the webOS CLI or SSH pairing works on a given architecture.

Use a DHCP reservation for the LG TV to avoid connection errors after IP changes. Please send a **Compatibility report** issue when a combination works for you.
