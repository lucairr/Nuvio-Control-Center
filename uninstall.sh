#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $(id -u) -ne 0 ]]; then echo 'Run with sudo bash uninstall.sh'; exit 1; fi
systemctl disable --now nuvio-dashboard.service nuvio-check.timer 2>/dev/null || true
systemctl stop nuvio-check.service 2>/dev/null || true
rm -f /etc/systemd/system/nuvio-dashboard.service /etc/systemd/system/nuvio-check.service /etc/systemd/system/nuvio-check.timer
systemctl daemon-reload
rm -rf /opt/nuvio-updater
printf 'Services and application removed. Preserved /var/lib/nuvio-updater (configuration + SSH keys).\n'
printf 'To remove stored data and service account, manually remove the directory and account AFTER backing up the data.\n'
