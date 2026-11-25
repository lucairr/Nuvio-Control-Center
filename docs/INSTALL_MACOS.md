# macOS installation (beta / not yet hardware-verified)

This is an optional **per-user** setup for a Mac (Intel or Apple Silicon). It does not install a native `.app`; it runs the same Python dashboard using `launchd` LaunchAgents, with a daily check at **19:30** while the Mac/user session is running. If the Mac sleeps, the check might not occur until the next scheduled day.

**Prerequisites:** macOS with Python 3.9+, Node.js 20+ (22 recommended), npm, official LG `@webos-tools/cli` and an LG TV with Developer Mode / Key Server. LG documents 64-bit macOS for the CLI. The project has not yet been tested on a physical Mac/TV combination.

Install prerequisites using their official downloaders or your preferred package manager. Verify:

```bash
python3 --version
node -v
npm -v
npm install -g @webos-tools/cli
ares -V
```

If `npm install -g` fails due to permissions, configure a user-level npm prefix or use a supported Node version manager; do not indiscriminately `sudo npm install`.

From the extracted source repository root, run as your **normal Mac user (not sudo)**:

```bash
TV_IP=192.168.1.50 bash macos/install-macos.sh
```

Enter a dashboard password of at least 12 characters. The script installs code in `~/Applications/NuvioControlCenter`, private configuration in `~/Library/Application Support/NuvioControlCenter`, and `launchd` jobs in `~/Library/LaunchAgents/`. It preserves existing configuration and SSH profiles when rerun.

## Pair TV (same user as the installer)

Enable Developer Mode and Key Server on LG, then run in a Terminal session as that user:

```bash
ares-config --profile tv
ares-setup-device --add nuvio-lg --info host=192.168.1.50 --info port=9922 --info username=prisoner
ares-novacom --device nuvio-lg --getkey
ares-install --device nuvio-lg --listfull
```

At the passphrase prompt type the short code on the TV. If the alias exists, replace `--add` with `--modify`. Open `http://localhost:8765` and press **Verifica aggiornamenti**. Only enable automatic updates after the TV's installed version is visible.

For logs:

```bash
tail -n 60 "$HOME/Library/Application Support/NuvioControlCenter/launchd-dashboard.err"
launchctl list | grep local.nuvio.controlcenter
```

To remove jobs and code but **keep configuration and SSH keys**:

```bash
bash macos/uninstall-macos.sh
```

Do not expose the HTTP dashboard to the internet. For remote access use a trusted VPN or HTTPS proxy.
