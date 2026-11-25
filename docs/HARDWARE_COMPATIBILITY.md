# Host hardware & platform compatibility

**Important:** The host is the computer/server running Nuvio Control Center, **not** the LG TV firmware. Only **LG webOS Developer Mode** TVs are supported as the target. Samsung Tizen and rooted LG Homebrew workflows are **not implemented**.

| Host / hardware | Install method | Status (13 Nov 2026) | Comments |
|---|---|---|---|
| Debian 11 VM on ESXi, 64-bit | `install.sh` + systemd | **User-tested** for dashboard + manual downgrade | Actual TV/app operations depend on LG Developer Mode and network |
| Debian 12/13, Ubuntu 22.04/24.04 (Intel/AMD x86-64) | `install.sh` | CI/code-tested; **live TV not verified** | Requires systemd, Python 3.9+, Node 20+ |
| Proxmox VM, Intel NUC, mini PC, home server (Linux x86-64) | `install.sh` or Docker | **Not yet hardware-tested** | Linux host needs LAN connection to TV |
| Windows 10/11 x64 desktop/laptop | PowerShell installer | **Not yet hardware-tested** | Runs under current Windows user; auto-check while logged on |
| macOS Intel / Apple Silicon | `macos/install-macos.sh` | **Experimental, not hardware-tested** | LaunchAgents, no native `.app` package |
| Raspberry Pi 4/5, Raspberry Pi OS **64-bit** | Docker or systemd Debian-based | **Experimental, not ARM64-tested** | Official LG CLI on ARM64 not verified, may fail |
| Synology/QNAP NAS, TrueNAS SCALE, Linux Docker host (x86-64) | `compose.yaml` | **Experimental, not NAS-tested** | Container networking and volume persistence vary |
| NAS ARM64 | Docker | **Experimental / possible CLI incompatibility** | No warranty on CLI binaries/extensions |
| Raspberry Pi OS 32-bit or arbitrary embedded OS | Not supported | **Unsupported** | Requires 64-bit Python/Node and working webOS CLI |

The official [LG webOS CLI documentation](https://webostv.developer.lge.com/develop/tools/cli-installation) specifies supported 64-bit desktop environments and may not certify ARM64 boards or NAS systems. Working Python and Node.js alone does **not** prove the webOS CLI or SSH pairing works on a particular architecture.

**Recommended for first public testing:** Debian/Ubuntu 64-bit or Windows, with LAN-only dashboard and TV pairing before any installation. Use a DHCP reservation for the LG TV to avoid connection errors after IP changes.
