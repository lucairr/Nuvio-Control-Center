#!/usr/bin/env bash
# Nuvio Control Center: Debian/Ubuntu Linux systemd installer.
set -Eeuo pipefail
umask 077

if [[ "$(id -u)" != 0 ]]; then
  echo 'Run with: sudo bash install.sh' >&2
  exit 1
fi
if ! command -v systemctl >/dev/null 2>&1; then
  echo 'This installer requires systemd (Debian/Ubuntu). See docs/INSTALL_LINUX.md.' >&2
  exit 1
fi
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER=nuvio-updater
INSTALL_DIR=/opt/nuvio-updater
STATE_DIR=/var/lib/nuvio-updater
TV_DEVICE="${TV_DEVICE:-nuvio-lg}"
TV_NAME="${TV_NAME:-LG webOS TV}"
WEB_PORT="${WEB_PORT:-8765}"
WEB_BIND="${WEB_BIND:-0.0.0.0}"

if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.9+ first (sudo apt-get install python3).' >&2
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3,9): raise SystemExit('Python 3.9+ is required')
PY
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo 'Node.js 20+ and npm are required. See docs/INSTALL_LINUX.md.' >&2
  exit 1
fi
if (( $(node -p 'parseInt(process.versions.node.split(".")[0],10)') < 20 )); then
  echo "Node.js $(node -v) is too old. Upgrade to Node 20+ (Node 22 recommended)." >&2
  exit 1
fi
if ! command -v ares-install >/dev/null || ! command -v ares-setup-device >/dev/null || ! command -v ares-novacom >/dev/null; then
  echo 'Installing official LG webOS CLI via npm...'
  npm install -g @webos-tools/cli
fi
# The services run with PATH=/usr/local/bin:/usr/bin:/bin: the CLI must be reachable there
# (it is not when Node comes from nvm under /root or a user's home).
for cmd in ares-install ares-novacom ares-setup-device; do
  if ! PATH=/usr/local/bin:/usr/bin:/bin command -v "$cmd" >/dev/null 2>&1; then
    echo "LG CLI command '$cmd' is not in /usr/local/bin or /usr/bin (found: $(command -v "$cmd" || echo none))." >&2
    echo 'Install Node.js system-wide (NodeSource/apt), not with nvm, then run the installer again.' >&2
    exit 1
  fi
done

if [[ ! -f "$STATE_DIR/config.json" ]]; then
  TV_IP="${TV_IP:-}"
  if [[ -z "$TV_IP" && -t 0 ]]; then read -r -p 'LG TV IPv4 address (shown in Developer Mode): ' TV_IP; fi
  if [[ -z "$TV_IP" ]]; then
    echo 'Provide the TV IP on first install: sudo TV_IP=192.168.1.50 bash install.sh' >&2
    exit 1
  fi
  export TV_IP WEB_PORT WEB_BIND TV_DEVICE TV_NAME
  python3 - <<'PY'
import ipaddress, os, re
ipaddress.ip_address(os.environ['TV_IP'])
assert 1024 <= int(os.environ['WEB_PORT']) <= 65535, 'Port must be >= 1024 and <= 65535'
assert re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', os.environ['TV_DEVICE']), 'Invalid device alias'
assert os.environ['WEB_BIND'] in ('0.0.0.0','127.0.0.1','::1'), 'Invalid bind address'
PY
fi

if ! getent passwd "$APP_USER" >/dev/null; then
  useradd --system --user-group --create-home --home-dir "$STATE_DIR" --shell /usr/sbin/nologin "$APP_USER"
fi
install -d -o "$APP_USER" -g "$APP_USER" -m 0700 "$STATE_DIR"
install -d -m 0755 "$INSTALL_DIR/nuvio" "$INSTALL_DIR/web"
cp -r "$BASE/nuvio/." "$INSTALL_DIR/nuvio/"
cp -r "$BASE/web/." "$INSTALL_DIR/web/"
find "$INSTALL_DIR" -type d -exec chmod 0755 {} +
find "$INSTALL_DIR" -type f -exec chmod 0644 {} +
chown -R root:root "$INSTALL_DIR"

if [[ ! -f "$STATE_DIR/config.json" ]]; then
  python3 - <<'PY'
import json, os
from pathlib import Path
p=Path('/var/lib/nuvio-updater/config.json')
p.write_text(json.dumps({'tv_ip':os.environ['TV_IP'],'tv_device':os.environ['TV_DEVICE'],
 'tv_name':os.environ['TV_NAME'],'auto_update':False,
 'web_port':int(os.environ['WEB_PORT']),'web_bind':os.environ['WEB_BIND']},indent=2)+'\n')
PY
  chown "$APP_USER:$APP_USER" "$STATE_DIR/config.json"
  chmod 0600 "$STATE_DIR/config.json"
else
  echo 'Existing config and state detected: preserving them.'
fi

if [[ ! -f "$STATE_DIR/auth.json" ]]; then
  echo 'Set a dashboard password (minimum 12 characters):'
  (cd "$INSTALL_DIR" && runuser -u "$APP_USER" -- env HOME="$STATE_DIR" NUVIO_HOME="$STATE_DIR" /usr/bin/python3 -m nuvio.server set-password)
fi

install -m 0644 "$BASE/systemd/nuvio-dashboard.service" /etc/systemd/system/nuvio-dashboard.service
install -m 0644 "$BASE/systemd/nuvio-check.service" /etc/systemd/system/nuvio-check.service
install -m 0644 "$BASE/systemd/nuvio-check.timer" /etc/systemd/system/nuvio-check.timer
systemctl daemon-reload
systemctl enable --now nuvio-dashboard.service
systemctl restart nuvio-dashboard.service
systemctl enable --now nuvio-check.timer

printf '\nNuvio Control Center installed.\n'
printf 'Open http://<server-ip>:%s (or localhost when bound to 127.0.0.1)\n' "$(python3 -c 'import json;print(json.load(open("/var/lib/nuvio-updater/config.json"))["web_port"])')"
printf 'TV CLI profile: user=%s, HOME=%s\n' "$APP_USER" "$STATE_DIR"
printf 'Next: follow docs/INSTALL_LINUX.md to pair the TV with Developer Mode.\n'
printf 'Auto-install is disabled by default on a fresh installation.\n'
