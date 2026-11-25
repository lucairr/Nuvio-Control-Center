# Security policy / threat model

Nuvio Control Center is a local development-mode tool. It can install applications on a TV once you manually pair LG's CLI. **Treat the dashboard like an administrative interface.**

- **Local-only recommendation:** default Windows bind 127.0.0.1 (`-AllowLan` opt-in, firewall rule limited to Private profile + local subnet), Linux LAN bind 0.0.0.0 for convenience. Never forward the port to the Internet. Raw HTTP has no TLS; use a VPN/HTTPS reverse proxy when needed.
- **Authentication:** PBKDF2-SHA256 password with per-installation salt, HttpOnly session cookie with SameSite=Strict, CSRF header + Origin checks for mutations, login throttling, secure headers.
- **Secrets:** state/auth/SSH device keys remain on disk, not in the repository. Linux systemd state at `/var/lib/nuvio-updater/` is restricted to the dedicated unprivileged service user; Windows state is per-user in `%USERPROFILE%\.nuvio-control-center`. Never publish or back up these locations to public repositories.
- **Command execution:** fixed LG CLI operations only; no web endpoint takes shell commands. Device/IP/other local settings should be edited only by an administrator of the host.
- **Downloaded files:** only official Nuvio GitHub release assets are accepted, size-capped, checked against GitHub SHA-256 where provided, and inspected for expected `space.nuvio.webos` and release version before installation. No signature verification when the official release API doesn't provide a cryptographic digest; the GitHub HTTPS trust model still applies.
- **Manual downgrade:** selected older versions must be stable official Nuvio release IPKs; tag, ID and version are checked; no automatic downgrade, and auto-install is switched OFF when a downgrade is started. User app-data compatibility is **not** guaranteed.
- **Safe defaults:** automated installs OFF initially. Scheduled checks run regardless. Missing installed Nuvio, unknown installed version, unreachable TV, downgrade, invalid asset or package: no automatic install.
- **Not root:** Linux dashboard runs under dedicated `nuvio-updater` user and constrained systemd service. Windows runs under the current (non-admin) user with Task Scheduler.
- **Session behavior:** login sessions are in RAM and expire after 12 hours; restarting the server invalidates them. Change the password by running `python -m nuvio.server set-password` as the correct user and restart the dashboard.

**Not supported:** production Internet hosting of the raw server, bypassing LG Developer Mode expiry, automatic LG account login, remote SSH key retrieval without the TV's passphrase, and firmware/root modifications.

For sensitive vulnerabilities, do not open a public issue. Use **Security → Report a vulnerability** on the GitHub repository (private vulnerability reporting). Never include real keys, passphrases or `auth.json` contents.
