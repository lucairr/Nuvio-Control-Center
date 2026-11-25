# Docker / NAS / Raspberry Pi installation (experimental)

Nuvio Control Center can run in two unprivileged containers: a dashboard and a daily scheduler. This option is intended for **self-hosters**, for example Intel/AMD mini PCs, Proxmox Docker VMs, Raspberry Pi OS 64-bit, Synology Container Manager, QNAP Container Station or a generic Docker host.

**Status: experimental and not yet tested on a real NAS or ARM64 LG CLI installation.** LG documents a 64-bit Linux CLI environment; support for specific ARM boards and NAS firmware is not guaranteed. Use Linux systemd if you already have a working Debian/Ubuntu VM. Do not install Docker on a production NAS just for this project without evaluating resource/security implications.

## Requirements

- Docker Engine + Compose plugin (`docker compose version`), with access to the internet during the image build.
- Linux `x86_64` recommended; `aarch64` experimental. **Not supported:** 32-bit Raspberry Pi OS, architectures without a compatible Node.js/CLI runtime.
- Outbound HTTPS for Nuvio GitHub releases and the CLI, connectivity to TV port **9922**; pairing also needs the Key Server on port **9991**.
- An existing Nuvio LG webOS installation, with Developer Mode and Key Server enabled.
- The containers need time zone data: `TZ=Europe/Rome` is the default. Set another IANA timezone in `.env` if needed.

## 1. Build image

From the extracted repository root:

```bash
docker compose build
```

The Dockerfile installs Python and the official `@webos-tools/cli` inside an image. No host-wide Node.js or Python installation is required.

## 2. Initialize private data and login

Use your **actual TV IP** from the LG Developer Mode app. These commands run in the `dashboard` container's shared named volume and do not touch the TV:

```bash
docker compose run --rm dashboard python3 -m nuvio.bootstrap --tv-ip 192.168.1.50
docker compose run --rm -it dashboard python3 -m nuvio.server set-password
```

Choose a password of at least 12 characters. The config, hashed password, CLI device registry, SSH private key, logs and history remain inside the persistent named volume `nuvio_data`. Re-running bootstrap does not overwrite an existing config.

## 3. Start the services

```bash
docker compose up -d
docker compose ps
```

By default the dashboard binds only to **`http://localhost:8765` on the Docker host**. This is deliberate. To access it from a phone or another PC on your *trusted LAN*, edit `compose.yaml`, changing `127.0.0.1:8765:8765` to `8765:8765` and restrict access using your host firewall. **Do not expose 8765 to the internet.** Alternatively use an SSH tunnel or VPN.

## 4. Pair the TV inside the container

The TV IP must be reachable from the container. On the TV, activate **Developer Mode** and **Key Server**, then:

```bash
docker compose exec dashboard ares-config --profile tv
docker compose exec dashboard ares-setup-device --add nuvio-lg \
  --info host=192.168.1.50 --info port=9922 --info username=prisoner
docker compose exec dashboard ares-novacom --device nuvio-lg --getkey
```

When prompted, enter only the passphrase shown on the TV (never publish it). Then:

```bash
docker compose exec dashboard ares-install --device nuvio-lg --listfull
```

If you previously added the alias, replace `--add` with `--modify`. Docker dashboard and scheduler share the same profile and keys, so no second pairing is needed.

## 5. Test update and downgrade

Use the dashboard: **Verifica aggiornamenti** → **Versioni precedenti** → **Carica release**. A downgrade is *manual only*; it requires a known installed version, confirmation, and an older official IPK. It does not uninstall Nuvio. After initiating a downgrade, automatic installation is disabled to avoid immediately overwriting the selected version. A read-only check never installs anything.

The `scheduler` container checks daily at **19:30 in `TZ`**. The first install has `auto_update=false`; the dashboard switch enables/disables **installation**, not the scheduler itself.

## Administration and upgrades

```bash
docker compose logs --tail=80 dashboard
docker compose logs --tail=80 scheduler
docker compose exec dashboard ares-setup-device --list
docker compose pull    # if using a published image; default compose builds locally
docker compose up -d --build
```

Upgrading/rebuilding the containers preserves `nuvio_data`. `docker compose down` also preserves it; **never run `docker compose down -v` unless you intentionally want to delete the password, config and TV SSH keys.** Back up the named volume before a major change. Do not commit or share files from the volume.

**Network note:** Docker bridge networking usually supports reaching TV IPv4 addresses but some NAS/VLAN firewall policies may block it. The `web_bind` setting inside `config.json` must remain `0.0.0.0` for Docker port forwarding to work.
