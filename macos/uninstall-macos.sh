#!/usr/bin/env bash
# Removes only LaunchAgents, code and optional logs; preserves pairing and settings.
set -Eeuo pipefail
[[ "$(uname -s)" == 'Darwin' ]] || exit 1
[[ "$(id -u)" != 0 ]] || { echo 'Do not run as root.' >&2; exit 1; }
for name in dashboard check; do
  plist="$HOME/Library/LaunchAgents/local.nuvio.controlcenter.$name.plist"
  launchctl bootout "gui/$(id -u)" "$plist" >/dev/null 2>&1 || true
  rm -f "$plist"
done
rm -rf "$HOME/Applications/NuvioControlCenter"
echo 'Uninstalled. Settings and SSH keys are preserved.'
