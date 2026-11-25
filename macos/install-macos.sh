#!/usr/bin/env bash
# macOS user LaunchAgents (beta / not hardware-verified).
set -Eeuo pipefail
umask 077
[[ "$(uname -s)" == 'Darwin' ]] || { echo 'macOS only' >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || { echo 'Do not run as root or with sudo.' >&2; exit 1; }
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$(command -v python3 || true)"
[[ -n "$PYTHON" ]] || { echo 'Install Python 3.9+ first.' >&2; exit 1; }
"$PYTHON" - <<'PY'
import sys
assert sys.version_info >= (3,9), 'Python 3.9+ required'
PY
command -v node >/dev/null && command -v npm >/dev/null || { echo 'Install Node.js 20+ (22 recommended) and npm first.' >&2; exit 1; }
(( $(node -p 'parseInt(process.versions.node.split(".")[0],10)') >= 20 )) || { echo 'Node 20+ required.' >&2; exit 1; }
command -v ares-install >/dev/null && command -v ares-novacom >/dev/null || {
  echo 'Install official LG CLI first: npm install -g @webos-tools/cli' >&2
  exit 1
}
INSTALL_DIR="$HOME/Applications/NuvioControlCenter"
STATE_DIR="$HOME/Library/Application Support/NuvioControlCenter"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$INSTALL_DIR/nuvio" "$INSTALL_DIR/web" "$STATE_DIR" "$AGENTS"
chmod 700 "$STATE_DIR"
cp -R "$BASE/nuvio/." "$INSTALL_DIR/nuvio/"
cp -R "$BASE/web/." "$INSTALL_DIR/web/"
export NUVIO_HOME="$STATE_DIR" PYTHON INSTALL_DIR STATE_DIR AGENTS
if [[ ! -f "$STATE_DIR/config.json" ]]; then
  if [[ -z "${TV_IP:-}" ]]; then read -r -p 'TV IP shown in Developer Mode: ' TV_IP; fi
  export TV_IP
  (cd "$INSTALL_DIR" && "$PYTHON" -m nuvio.bootstrap --tv-ip "$TV_IP" --web-bind 127.0.0.1)
else
  echo 'Existing config preserved.'
fi
if [[ ! -f "$STATE_DIR/auth.json" ]]; then
  (cd "$INSTALL_DIR" && "$PYTHON" -m nuvio.server set-password)
fi
"$PYTHON" - <<'PY'
import os, plistlib
from pathlib import Path
p=Path(os.environ['AGENTS']); install=os.environ['INSTALL_DIR']
py=os.environ['PYTHON']; state=os.environ['STATE_DIR']
path=os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin')
for name,action in [('dashboard',['serve']),('check',['run','auto'])]:
  label='local.nuvio.controlcenter.'+name
  d={'Label':label,'ProgramArguments':[py,'-m','nuvio.server',*action],
     'WorkingDirectory':install,'EnvironmentVariables':{'NUVIO_HOME':state,'HOME':str(Path.home()),'PATH':path},
     'StandardOutPath':str(Path(state)/('launchd-'+name+'.log')),
     'StandardErrorPath':str(Path(state)/('launchd-'+name+'.err'))}
  if name=='dashboard':d.update({'RunAtLoad':True,'KeepAlive':True})
  else:d['StartCalendarInterval']={'Hour':19,'Minute':30}
  (p/(label+'.plist')).write_bytes(plistlib.dumps(d))
PY
UID_NUM="$(id -u)"
for name in dashboard check; do
  PLIST="$AGENTS/local.nuvio.controlcenter.$name.plist"
  launchctl bootout "gui/$UID_NUM" "$PLIST" >/dev/null 2>&1 || true
  if ! launchctl bootstrap "gui/$UID_NUM" "$PLIST"; then
    echo "LaunchAgent could not start; log in to the macOS desktop and run: launchctl bootstrap gui/$UID_NUM '$PLIST'" >&2
  fi
done
printf '\nInstalled Nuvio Control Center for macOS user %s.\n' "$(id -un)"
printf 'Dashboard: http://localhost:8765 (or configured port)\n'
printf 'Pair TV as THIS user (see docs/INSTALL_MACOS.md). Auto installation starts OFF.\n'
