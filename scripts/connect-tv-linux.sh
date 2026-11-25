#!/usr/bin/env bash
set -Eeuo pipefail
TV_IP="${1:-}"
TV_ALIAS="${2:-nuvio-lg}"
if [[ ! "$TV_IP" =~ ^[0-9a-fA-F:.]+$ ]]; then
  echo 'Usage: sudo bash scripts/connect-tv-linux.sh <TV_IP> [alias]' >&2
  exit 1
fi
if [[ ! "$TV_ALIAS" =~ ^[a-zA-Z0-9_-]+$ ]]; then echo 'Invalid alias' >&2; exit 1; fi
if [[ $(id -u) -ne 0 ]]; then echo 'Run with sudo' >&2; exit 1; fi
RUN=(runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater)
echo 'Switch ON both Developer Mode and Key Server on the TV, then continue.'
"${RUN[@]}" ares-config --profile tv
if "${RUN[@]}" ares-setup-device --list | grep -Eq "^[[:space:]]*${TV_ALIAS}[[:space:]]"; then
  "${RUN[@]}" ares-setup-device --modify "$TV_ALIAS" --info "host=$TV_IP" --info port=9922 --info username=prisoner
else
  "${RUN[@]}" ares-setup-device --add "$TV_ALIAS" --info "host=$TV_IP" --info port=9922 --info username=prisoner
fi
printf '\nEnter the passphrase shown ON THE TV when asked (never paste a shell command here).\n'
"${RUN[@]}" ares-novacom --device "$TV_ALIAS" --getkey
printf '\nTesting installed applications...\n'
"${RUN[@]}" ares-install --device "$TV_ALIAS" --listfull
printf '\nIf you changed the IP after initial installation, also update tv_ip in /var/lib/nuvio-updater/config.json.\n'
